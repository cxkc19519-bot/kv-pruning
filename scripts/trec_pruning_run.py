"""Frozen query-blind TREC pruning calibration, with bounded real-model gates."""
import argparse
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import time
import traceback
import types

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
from pilot import WindowScores
from trec_context_gate import cache_state, clone_cache, make_scorer, native, prefill
from trec_pruning_utils import (gather_prefix_cache, kv_bytes, native_header_metadata,
    random_prefix_scores, select_prefix_indices, validate_indices)


PREPARED_SHA="892bde36749089e03f9e2aa84b8bc65379fb6d22b505867d49c2353dbb8ecf25"
SOURCES={"pilot.py":"476b3cbf8a9e16cdbb958286ba931a45d9b089f1bba4fb0a29f3a7ee9ebcdc1f",
         "trec_context_gate.py":"12cffbddf37d00e686d51ccd9fce4be59616a4218e34ed136db71329b18dc616",
         "trec_pruning_utils.py":"92594811de726c585087fe1356a81cfcbe3a19a1fd6bb68a7e8781a334c53918"}


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")
def append(path,value):
    with path.open("a",encoding="utf-8") as f:f.write(json.dumps(value,ensure_ascii=False)+"\n")
def equal_cache(a,b):return len(a.layers)==len(b.layers) and all(torch.equal(x.keys,y.keys) and torch.equal(x.values,y.values) for x,y in zip(a.layers,b.layers))


@torch.no_grad()
def scored_prefill(model,prefix_ids):
    hook=WindowScores(window=64,kernel=5)
    handles=[layer.self_attn.register_forward_hook(hook.hook,with_kwargs=True) for layer in model.model.layers]
    try:cache=prefill(model,prefix_ids)
    finally:
        for handle in handles:handle.remove()
    assert set(hook.scores)==set(range(28))
    for value in hook.scores.values():
        assert tuple(value.shape)==(1,4,len(prefix_ids)) and torch.isfinite(value).all()
    return cache,hook.scores


@torch.inference_mode()
def decode_compact(model,cache,logical_prefix,suffix,max_new,eos):
    """Original RoPE positions and compact physical causal indices are independent."""
    start=cache.get_seq_length();offset=logical_prefix-start
    assert start<=logical_prefix
    x=torch.tensor([suffix],device=model.device);ids=[];trace=[]
    for step in range(max_new):
        physical=cache.get_seq_length()
        logical=logical_prefix if step==0 else logical_prefix+len(suffix)+step-1
        assert logical-physical==offset
        width=x.shape[1]
        cp=torch.arange(physical,physical+width,device=model.device)
        pos=torch.arange(logical,logical+width,device=model.device)[None,:]
        output=model(input_ids=x,past_key_values=cache,use_cache=True,
                     position_ids=pos,cache_position=cp,logits_to_keep=1)
        token=int(output.logits[0,-1].argmax());ids.append(token);del output
        assert cache.get_seq_length()==physical+width
        trace.append(dict(step=step,physical_start=physical,logical_start=logical,input_width=width))
        if token in eos:break
        x=torch.tensor([[token]],device=model.device)
    assert cache.get_seq_length()==start+len(suffix)+len(ids)-1
    return ids,trace


@torch.inference_mode()
def native_compact(model,cache,logical_prefix,suffix,decode):
    """HF generate reference: retain its mask/cache update, add constant RoPE offset."""
    physical=cache.get_seq_length();offset=logical_prefix-physical
    original=model.prepare_inputs_for_generation
    prior_override=model.__dict__.get("prepare_inputs_for_generation")
    trace=[]
    def prepare(instance,input_ids,**kwargs):
        prepared=original(input_ids,**kwargs)
        cp=prepared["cache_position"]
        derived=prepared["position_ids"]
        assert torch.equal(derived,cp[None,:]),"Expected unpadded HF physical positions"
        assert int(cp[0])==prepared["past_key_values"].get_seq_length()
        prepared["position_ids"]=derived+offset
        trace.append(dict(step=len(trace),physical_start=int(cp[0]),logical_start=int(derived[0,0])+offset,input_width=cp.numel()))
        return prepared
    model.prepare_inputs_for_generation=types.MethodType(prepare,model)
    try:
        x=torch.tensor([suffix],device=model.device)
        output=model.generate(input_ids=x,past_key_values=cache,
                              attention_mask=torch.ones((1,physical+len(suffix)),device=model.device,dtype=torch.long),
                              cache_position=torch.arange(physical,physical+len(suffix),device=model.device),
                              generation_config=decode,logits_to_keep=1)
        ids=output[0,len(suffix):].tolist()
    finally:
        if prior_override is None:delattr(model,"prepare_inputs_for_generation")
        else:model.prepare_inputs_for_generation=prior_override
    return ids,trace


def build_maps(scores,source_key,n,metadata,conditions):
    maps={c["method"]:{} for c in conditions}
    for layer in range(28):
        random=random_prefix_scores(n,source_key,layer,4)
        for c in conditions:
            value=random if c["method"].startswith("uniform_random") else scores[layer]
            indices=select_prefix_indices(value,n//2,metadata["header_ids"],c["pin_shared_header"])
            validate_indices(indices,n,n//2,4,metadata["header_ids"],c["pin_shared_header"])
            maps[c["method"]][layer]=indices
    return maps


def report(cases,rows,baseline,conditions):
    by={(r["source_key"],r["method"]):r for r in rows}
    result={}
    for c in conditions:
        method=c["method"];states={s:0 for s in ["C2C","C2W","W2C","W2W","N/A"]}
        records=[by.get((case["source_key"],method)) for case in cases]
        valid=[r for r in records if r and r["status"]=="ok"]
        for case,r in zip(cases,records):
            if not r or r["status"]!="ok":states["N/A"]+=1
            else:
                state=("C" if baseline[case["source_key"]]["metrics"]["exact_correct"] else "W")+"2"+("C" if r["metrics"]["exact_correct"] else "W")
                states[state]+=1
        result[method]=dict(scheduled=32,generated=len(valid),exact_correct=sum(r["metrics"]["exact_correct"] for r in valid),
            label_format=sum(r["metrics"]["whole_response_label_format"] for r in valid),
            compatibility_sum=sum(r["metrics"]["official_firstline_compatibility"] for r in valid),
            truncated=sum(r["truncated"] for r in valid),errors=sum(r is not None and r["status"]=="error" for r in records),
            not_run=sum(r is None for r in records),full_to_compressed=states,full_correct_denominator=19,
            conditional_loss_numerator=states["C2W"],conditional_loss_rate=states["C2W"]/19,
            prefix_kv_byte_range=[min(r["prefix_kv_bytes"] for r in valid),max(r["prefix_kv_bytes"] for r in valid)] if valid else None)
    return dict(baseline=dict(n=32,exact_correct=19,label_format=32),methods=result,
                new_main_outputs=sum(r["status"]=="ok" for r in rows),scheduled_main_outputs=128,
                scope="Full-to-compressed paired classification/label-format calibration; no safety-specific or novelty claim; NoDemo results excluded from these pairs")


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--prepared",required=True);parser.add_argument("--model",required=True);parser.add_argument("--out",required=True)
    args=parser.parse_args();root=Path(args.out);root.mkdir(parents=True,exist_ok=False)
    source_sha={}
    for name in ["trec_pruning_run.py",*SOURCES]:
        data=Path(__file__).with_name(name).read_bytes()
        if name in SOURCES:assert sha(data)==SOURCES[name],name
        (root/("source_"+name)).write_bytes(data);source_sha[name]=sha(data)
    m=dict(status="preparing",rows=0,new_model_outputs=0,extra_correctness_outputs=0,start_unix=time.time(),pid=os.getpid(),args=vars(args),
           source_sha256=source_sha,versions={name:importlib.metadata.version(name) for name in ["torch","transformers","tokenizers","safetensors"]},
           cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"),scope="Frozen32 cases, four half-budget query-blind prefix KV selectors")
    save(root/"manifest.json",m);inputs={};rows=[];checks=[];cases=[];conditions=[];baseline={}
    try:
        raw_prepared=Path(args.prepared).read_bytes();assert sha(raw_prepared)==PREPARED_SHA
        cfg=json.loads(raw_prepared);assert cfg["execution_enabled"] is False
        assert Path(args.model).name==cfg["model_revision"]
        conditions=cfg["conditions"]
        assert len(conditions)==4 and cfg["max_new_main_outputs"]==128 and cfg["max_extra_correctness_outputs"]==24
        (root/"prepared_config.json").write_bytes(raw_prepared)
        cpu=Path(cfg["cpu_preflight_run"])
        cpu_m=json.loads((cpu/"manifest.json").read_text());assert cpu_m["status"]=="complete" and cpu_m["cpu_engineering_gate_passed"]
        assert json.loads((cpu/"verification_manifest.json").read_text())["status"]=="complete"
        metadata_raw=(cpu/"header_budget_metadata.json").read_bytes();assert sha(metadata_raw)==cfg["header_budget_metadata_sha256"]
        meta=json.loads(metadata_raw);(root/"header_budget_metadata.json").write_bytes(metadata_raw)
        raw_cases=Path(cfg["cases_path"]).read_bytes();assert sha(raw_cases)==cfg["cases_sha256"]
        cases=[json.loads(line) for line in raw_cases.decode().splitlines()];assert len(cases)==32
        (root/"cases.jsonl").write_bytes(raw_cases)
        full=Path(cfg["baseline_run"])
        full_raw=(full/"generations.jsonl").read_bytes();assert sha(full_raw)==cfg["baseline_generations_sha256"]
        baseline_rows=[r for r in map(json.loads,full_raw.decode().splitlines()) if r["condition"]=="with_demos"]
        assert [r["source_key"] for r in baseline_rows]==[r["source_key"] for r in cases]==[r["source_key"] for r in meta]
        baseline={r["source_key"]:r for r in baseline_rows};assert sum(r["metrics"]["exact_correct"] for r in baseline_rows)==19
        save(root/"baseline_with_demos.json",baseline_rows)
        for name,digest in cfg["tokenizer_sha256"].items():assert sha((Path(args.model)/name).read_bytes())==digest
        tok=AutoTokenizer.from_pretrained(args.model,local_files_only=True)
        header=json.loads(Path("configs/trec-context-gate-proposal-v1.json").read_text())["shared_system_header"]
        for case,metadata in zip(cases,meta):
            v=case["versions"]["with_demos"];n=v["prefix_tokens"]
            recomputed=native_header_metadata(tok,v["messages"],v["input_ids"],n,header)
            for name in ["header_ids","required_pinned_ids","header_char_span","budget","boundary_overlaps"]:assert recomputed[name]==metadata[name]
            assert metadata["prefix_ids"]==v["input_ids"][:n]
        data=Path("results/20261028-trec-data-preflight-v2")
        inventory=json.loads((data/"label_inventory.json").read_text())
        score=make_scorer((data/"upstream/metrics.py").read_bytes(),inventory)
        fixture_path=Path(cfg["cases_path"]).parent/"scorer_fixtures.json"
        for fixture in json.loads(fixture_path.read_text()):
            got=score(fixture["response"],fixture["gold"])
            assert got["exact_correct"]==fixture["whole_response_gold_exact"] and got["whole_response_label_format"]==fixture["whole_response_exact_label_format"] and got["official_firstline_compatibility"]==fixture["official_firstline_compatibility"]
        for path in [Path(args.prepared),Path(cfg["cases_path"]),cpu/"manifest.json",cpu/"verification_manifest.json",cpu/"header_budget_metadata.json",full/"manifest.json",full/"generations.jsonl",full/"execution_snapshot.json",data/"label_inventory.json",data/"upstream/metrics.py",fixture_path,Path(args.model)/"config.json",Path(args.model)/"generation_config.json"]:inputs[str(path)]=sha(path.read_bytes())
        m.update(status="cpu_inputs_verified",input_sha256=inputs,tokenizer_sha256=cfg["tokenizer_sha256"]);save(root/"manifest.json",m)
        print("CPU_INPUTS_VERIFIED",flush=True)
        model=AutoModelForCausalLM.from_pretrained(args.model,torch_dtype=torch.bfloat16,attn_implementation="sdpa",local_files_only=True).eval().to("cuda:0")
        assert model.config.model_type=="qwen2" and len(model.model.layers)==28
        assert all(layer.self_attn.sliding_window is None for layer in model.model.layers) and all(p.dtype==torch.bfloat16 for p in model.parameters())
        eos=set(cfg["decode"]["eos_token_ids"])
        assert eos==set(model.generation_config.eos_token_id)
        decode=GenerationConfig(do_sample=False,num_beams=1,repetition_penalty=1.,max_new_tokens=64,use_cache=True,eos_token_id=sorted(eos),pad_token_id=151643,bos_token_id=model.generation_config.bos_token_id)
        assert decode.to_dict()==json.loads((full/"manifest.json").read_text())["actual_generation_config"]
        save(root/"hf_prepare_inputs_for_generation.txt",inspect.getsource(type(model).prepare_inputs_for_generation))
        m.update(status="engineering_checks",model_class=type(model).__name__,runtime_full_attention_layers=28,bf16_parameters=sum(p.numel() for p in model.parameters()),actual_generation_config=decode.to_dict());save(root/"manifest.json",m)
        def checked_output(label,key,ids,trace=None):
            record=dict(label=label,source_key=key,ids=ids,trace=trace)
            append(root/"engineering_outputs.jsonl",record)
            m["extra_correctness_outputs"]+=1;assert m["extra_correctness_outputs"]<=24
            save(root/"manifest.json",m)
            return ids
        for case,metadata in zip(cases[:3],meta[:3]):
            key=case["source_key"];v=case["versions"]["with_demos"];n=v["prefix_tokens"];suffix=v["input_ids"][n:]
            expected=baseline[key]["ids"]
            whole=checked_output("native_full",key,native(model,v["input_ids"],decode));assert whole==expected
            nohook=prefill(model,v["input_ids"][:n]);before_nohook=cache_state(nohook)
            branch=clone_cache(nohook);ids,trace=decode_compact(model,branch,n,suffix,64,eos);checked_output("nohook_cached_full",key,ids,trace);del branch;assert ids==expected
            reference,scores=scored_prefill(model,v["input_ids"][:n]);initial=cache_state(reference)
            assert equal_cache(nohook,reference) and cache_state(nohook)==before_nohook
            branch=clone_cache(reference);ids,trace=decode_compact(model,branch,n,suffix,64,eos);checked_output("hook_cached_full",key,ids,trace);del branch;assert ids==expected
            identity_checks=[]
            for c in conditions:
                identity={layer:select_prefix_indices(scores[layer],n,metadata["header_ids"],c["pin_shared_header"]) for layer in range(28)}
                full_branch=gather_prefix_cache(reference,identity,n,n,metadata["header_ids"],c["pin_shared_header"])
                assert equal_cache(full_branch,reference) and kv_bytes(full_branch)==kv_bytes(reference)
                identity_checks.append(dict(method=c["method"],all_layer_kv_equal=True))
                if c is conditions[0]:
                    ids,trace=decode_compact(model,full_branch,n,suffix,64,eos);checked_output("identity_gather_full",key,ids,trace);assert ids==expected
                del full_branch
            maps=build_maps(scores,key,n,metadata,conditions);byte_counts={}
            for c in conditions:
                compact=gather_prefix_cache(reference,maps[c["method"]],n,n//2,metadata["header_ids"],c["pin_shared_header"])
                byte_counts[c["method"]]=kv_bytes(compact);assert kv_bytes(compact)==(n//2)*57344;del compact
            assert len(set(byte_counts.values()))==1
            compressed_parity=[]
            for method in ["adapted_snapkv_shared_anchors","uniform_random_shared_anchors_header_pinned"]:
                c=next(c for c in conditions if c["method"]==method)
                a=gather_prefix_cache(reference,maps[method],n,n//2,metadata["header_ids"],c["pin_shared_header"])
                native_ids,ntrace=native_compact(model,a,n,suffix,decode);checked_output("native_compressed_"+method,key,native_ids,ntrace);del a
                b=gather_prefix_cache(reference,maps[method],n,n//2,metadata["header_ids"],c["pin_shared_header"])
                custom_ids,ctrace=decode_compact(model,b,n,suffix,64,eos);checked_output("custom_compressed_"+method,key,custom_ids,ctrace);del b
                compressed_parity.append(dict(method=method,ids_equal=native_ids==custom_ids,traces_equal=ntrace==ctrace,native_ids=native_ids,custom_ids=custom_ids))
                save(root/"compressed_parity_progress.json",dict(source_key=key,checks=compressed_parity))
                assert native_ids==custom_ids and ntrace==ctrace,"Compressed native/custom parity failed"
            assert cache_state(reference)==initial and equal_cache(reference,nohook)
            checks.append(dict(source_key=key,full_baseline_replayed=True,hook_all_kv_equal=True,reference_unchanged=True,identity=identity_checks,compressed_parity=compressed_parity,all_method_prefix_bytes=byte_counts))
            save(root/"engineering_checks.json",checks)
            del nohook,reference,scores,maps
            print("ENGINEERING_PASS",len(checks),key,flush=True)
        assert len(checks)==3 and m["extra_correctness_outputs"]==24
        snapshot=dict(cfg,status="actual_engineering_passed_before_main",execution_enabled=True,cpu_synthetic_only=False,
                      parent_prepared_sha256=PREPARED_SHA,runner_source_sha256=source_sha,engineering_checks_sha256=sha((root/"engineering_checks.json").read_bytes()),decode_actual=decode.to_dict())
        save(root/"execution_snapshot.json",snapshot)
        m.update(status="running_main",engineering_gate_passed=True);save(root/"manifest.json",m)
        maps_folder=root/"actual_maps";maps_folder.mkdir();score_folder=root/"actual_scores";score_folder.mkdir()
        for case,metadata in zip(cases,meta):
            key=case["source_key"];v=case["versions"]["with_demos"];n=v["prefix_tokens"]
            reference,scores=scored_prefill(model,v["input_ids"][:n]);initial=cache_state(reference)
            maps=build_maps(scores,key,n,metadata,conditions)
            score_path=score_folder/(key+".pt");torch.save(scores,score_path)
            save(maps_folder/(key+".json"),{method:{str(layer):indices.tolist() for layer,indices in mapping.items()} for method,mapping in maps.items()})
            # Check every candidate branch before generating any condition for this case.
            byte_counts=[]
            for c in conditions:
                test=gather_prefix_cache(reference,maps[c["method"]],n,n//2,metadata["header_ids"],c["pin_shared_header"])
                assert kv_bytes(test)==(n//2)*57344;byte_counts.append(kv_bytes(test));del test
            assert len(set(byte_counts))==1
            for c in conditions:
                row=dict(source_key=key,method=c["method"],keep=.5,pin_shared_header=c["pin_shared_header"],gold=case["gold"],status="ok",baseline_exact=baseline[key]["metrics"]["exact_correct"])
                try:
                    branch=gather_prefix_cache(reference,maps[c["method"]],n,n//2,metadata["header_ids"],c["pin_shared_header"])
                    prefix_bytes=kv_bytes(branch);ids,trace=decode_compact(model,branch,n,v["input_ids"][n:],64,eos)
                    final_bytes=kv_bytes(branch);del branch
                    assert cache_state(reference)==initial
                    text=tok.decode(ids[:-1] if ids[-1] in eos else ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
                    row.update(text=text,ids=ids,decoded_with_terminal_tokens=tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False),
                               generated_tokens=len(ids),terminated_eos=ids[-1] in eos,truncated=len(ids)==64 and ids[-1] not in eos,
                               metrics=score(text,case["gold"]),prefix_tokens=n,physical_prefix_slots=n//2,suffix_tokens=v["suffix_tokens"],
                               prefix_kv_bytes=prefix_bytes,final_live_kv_bytes=final_bytes,header_tokens=metadata["header_count"],
                               required_pinned_count=metadata["required_pinned_count"] if c["pin_shared_header"] else metadata["anchor_count"],
                               input_ids_sha256=v["input_ids_sha256"],position_trace=trace)
                    rows.append(row);append(root/"generations.jsonl",row)
                except Exception as error:
                    row.update(status="error",error_type=type(error).__name__,error_message=str(error));rows.append(row);append(root/"generations.jsonl",row);raise
                m.update(rows=len(rows),new_model_outputs=sum(r["status"]=="ok" for r in rows));save(root/"manifest.json",m)
                print("MAIN",len(rows),c["method"],key,"exact",row["metrics"]["exact_correct"],flush=True)
            del reference,scores,maps
        result=report(cases,rows,baseline,conditions);save(root/"summary.json",result)
        m.update(status="complete",rows=128,new_model_outputs=128,end_unix=time.time(),
                 artifact_sha256={str(p.relative_to(root)):sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and p.name!='manifest.json'})
        save(root/"manifest.json",m);print("COMPLETE",json.dumps(result),flush=True)
    except Exception as error:
        if cases and baseline:save(root/"partial_summary.json",report(cases,rows,baseline,conditions))
        m.update(status="failed",rows=len(rows),new_model_outputs=sum(r["status"]=="ok" for r in rows),end_unix=time.time(),input_sha256=inputs,error_type=type(error).__name__,error_message=str(error),engineering_cases_completed=len(checks))
        save(root/"manifest.json",m);(root/"traceback.txt").write_text(traceback.format_exc(),encoding="utf-8");raise


if __name__=="__main__":main()
