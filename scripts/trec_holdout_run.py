"""Ten-question staged holdout: Full engineering -> Full gate -> pruning."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time
import traceback

import torch
from transformers import AutoModelForCausalLM,AutoTokenizer,GenerationConfig
from trec_context_gate import cache_state,clone_cache,make_scorer,native,prefill
from trec_pruning_run import build_maps,decode_compact,equal_cache,native_compact,scored_prefill
from trec_pruning_utils import gather_prefix_cache,kv_bytes,native_header_metadata,select_prefix_indices


CONFIG_SHA="147aea59f40dfe6bc6a33635a3f2d8fbb482eb9e5232e00f15765b522584b915"
SOURCES={"trec_pruning_run.py":"7b9393babbcf28293d51fdd43c7a80ed41810d614001811b6c458c55d3c84412",
         "trec_context_gate.py":"12cffbddf37d00e686d51ccd9fce4be59616a4218e34ed136db71329b18dc616",
         "trec_pruning_utils.py":"92594811de726c585087fe1356a81cfcbe3a19a1fd6bb68a7e8781a334c53918",
         "pilot.py":"476b3cbf8a9e16cdbb958286ba931a45d9b089f1bba4fb0a29f3a7ee9ebcdc1f"}


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")
def append(path,value):
    with path.open("a",encoding="utf-8") as f:f.write(json.dumps(value,ensure_ascii=False)+"\n")


def summarize(cases,rows,conditions,cfg,not_run_reason="not_run_engineering_gate"):
    by={(r["source_key"],r["method"]):r for r in rows}
    full={c["source_key"]:by.get((c["source_key"],"full")) for c in cases}
    valid_full=[r for r in full.values() if r and r["status"]=="ok"]
    denominator=sum(r["metrics"]["exact_correct"] for r in valid_full)
    methods={};schedule=[]
    for condition in [dict(method="full")]+conditions:
        method=condition["method"];valid=[];errors=missing=0
        transitions={s:0 for s in ["C2C","C2W","W2C","W2W","N/A"]}
        formats={s:0 for s in ["valid2valid","valid2invalid","invalid2valid","invalid2invalid","N/A"]}
        for case in cases:
            key=case["source_key"];row=by.get((key,method))
            schedule.append(dict(source_key=key,method=method,status=row["status"] if row else not_run_reason))
            if row and row["status"]=="ok":valid.append(row)
            elif row:errors+=1
            else:missing+=1
            if method!="full":
                base=full[key]
                if row and base and row["status"]==base["status"]=="ok":
                    transitions[("C" if base["metrics"]["exact_correct"] else "W")+"2"+("C" if row["metrics"]["exact_correct"] else "W")]+=1
                    formats[("valid" if base["metrics"]["whole_response_label_format"] else "invalid")+"2"+("valid" if row["metrics"]["whole_response_label_format"] else "invalid")]+=1
                else:transitions["N/A"]+=1;formats["N/A"]+=1
        methods[method]=dict(scheduled=10,generated=len(valid),exact_correct=sum(r["metrics"]["exact_correct"] for r in valid),label_format=sum(r["metrics"]["whole_response_label_format"] for r in valid),
            truncated=sum(r["truncated"] for r in valid),compatibility_sum=sum(r["metrics"]["official_firstline_compatibility"] for r in valid),errors=errors,not_run=missing)
        if method!="full":methods[method].update(full_to_compressed=transitions,format_transitions=formats,full_correct_denominator=denominator,
                                                conditional_loss_rate=transitions["C2W"]/denominator if denominator else None)
    gate=cfg["full_support_gate"];f=methods["full"]
    passed=f["generated"]==10 and f["exact_correct"]>=gate["min_whole_response_exact_correct"] and f["label_format"]==gate["required_label_format_correct"] and f["truncated"]<=gate["max_truncated"] and f["errors"]<=gate["max_errors"]
    return dict(methods=methods,full_support_gate_passed=passed,actual_full_correct_denominator=denominator,
                scheduled_main_outputs=50,new_main_outputs=sum(r["status"]=="ok" for r in rows),planned_cells=schedule,
                scope="Ten held-out questions with shared demonstrations; no independent-dataset, significance, method-winner or safety-specific claim")


def main():
    p=argparse.ArgumentParser();p.add_argument("--config",required=True);p.add_argument("--model",required=True);p.add_argument("--out",required=True);a=p.parse_args()
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False);sources={}
    for name in ["trec_holdout_run.py",*SOURCES]:
        raw=Path(__file__).with_name(name).read_bytes()
        if name in SOURCES:assert sha(raw)==SOURCES[name],name
        (root/("source_"+name)).write_bytes(raw);sources[name]=sha(raw)
    m=dict(status="preparing",stage="cpu",rows=0,new_model_outputs=0,extra_correctness_outputs=0,start_unix=time.time(),args=vars(a),pid=os.getpid(),source_sha256=sources,
           cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"),versions={n:importlib.metadata.version(n) for n in ["torch","transformers","tokenizers","safetensors"]})
    save(root/"manifest.json",m);inputs={};cases=[];rows=[];conditions=[];cfg={};active_cell=None
    try:
        raw_cfg=Path(a.config).read_bytes();assert sha(raw_cfg)==CONFIG_SHA
        cfg=json.loads(raw_cfg);assert not cfg["execution_enabled"] and cfg["n_cases"]==10 and cfg["max_main_outputs"]==50 and cfg["max_extra_correctness_outputs"]==24
        assert Path(a.model).name==cfg["model_revision"]
        (root/"proposal.json").write_bytes(raw_cfg)
        raw_cases=Path(cfg["cases_path"]).read_bytes();assert sha(raw_cases)==cfg["cases_sha256"]
        cases=[json.loads(s) for s in raw_cases.decode().splitlines()]
        assert len(cases)==10 and [c["source_key"] for c in cases]==cfg["frozen_source_keys"]
        (root/"cases.jsonl").write_bytes(raw_cases)
        conditions=[c for c in cfg["conditions"] if c["method"]!="full"];assert len(conditions)==4
        raw_meta=Path(cfg["header_metadata_path"]).read_bytes();assert sha(raw_meta)==cfg["header_metadata_sha256"]
        metadata=json.loads(raw_meta);assert [r["source_key"] for r in metadata]==cfg["frozen_source_keys"]
        (root/"header_budget_metadata.json").write_bytes(raw_meta)
        review_bytes=Path(cfg["label_review_path"]).read_bytes();assert sha(review_bytes)==cfg["label_review_sha256"]
        (root/"label_review.json").write_bytes(review_bytes)
        cpu=Path(cfg["cases_path"]).parent
        assert all(json.loads((cpu/name).read_text())["status"]=="complete" for name in ["manifest.json","finalization_manifest.json","verification_manifest.json"])
        # Freeze proof that this run starts before these IDs have experimental answers.
        overlap=[];prior_files=[]
        for file in sorted(Path("results").glob("*/generations.jsonl")):
            prior_files.append(str(file))
            for line in file.open(encoding="utf-8"):
                r=json.loads(line)
                if r.get("source_key") in cfg["frozen_source_keys"]:overlap.append(dict(path=str(file),source_key=r["source_key"]))
        assert not overlap,"New queue already has experimental outputs; no silent rerun"
        save(root/"prior_output_nonoverlap.json",dict(files=prior_files,overlap=overlap))
        for name,digest in cfg["tokenizer_sha256"].items():assert sha((Path(a.model)/name).read_bytes())==digest
        tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True)
        for case,meta in zip(cases,metadata):
            v=case["versions"]["with_demos"]
            reencoded=native_header_metadata(tok,v["messages"],v["input_ids"],v["prefix_tokens"],cfg["shared_system_header"])
            for name in ["header_ids","budget","required_pinned_ids","header_char_span"]:assert reencoded[name]==meta[name]
            assert meta["prefix_ids"]==v["input_ids"][:v["prefix_tokens"]]
        data=Path("results/20261028-trec-data-preflight-v2")
        labels=json.loads((data/"label_inventory.json").read_text());score=make_scorer((data/"upstream/metrics.py").read_bytes(),labels)
        fixtures_path=Path("results/20261028-trec-context-gate-data-v1/scorer_fixtures.json")
        for f in json.loads(fixtures_path.read_text()):
            actual=score(f["response"],f["gold"])
            assert actual==dict(exact_correct=f["whole_response_gold_exact"],whole_response_label_format=f["whole_response_exact_label_format"],official_firstline_compatibility=f["official_firstline_compatibility"])
        for path in [Path(a.config),Path(cfg["cases_path"]),Path(cfg["header_metadata_path"]),Path(cfg["label_review_path"]),cpu/"manifest.json",cpu/"finalization_manifest.json",cpu/"verification_manifest.json",data/"label_inventory.json",data/"upstream/metrics.py",fixtures_path,Path(a.model)/"config.json",Path(a.model)/"generation_config.json"]:inputs[str(path)]=sha(path.read_bytes())
        m.update(status="cpu_verified",input_sha256=inputs,tokenizer_sha256=cfg["tokenizer_sha256"]);save(root/"manifest.json",m)
        model=AutoModelForCausalLM.from_pretrained(a.model,torch_dtype=torch.bfloat16,attn_implementation="sdpa",local_files_only=True).eval().to("cuda:0")
        assert model.config.model_type=="qwen2" and len(model.model.layers)==28 and all(layer.self_attn.sliding_window is None for layer in model.model.layers)
        assert all(param.dtype==torch.bfloat16 for param in model.parameters())
        eos=set(cfg["decode"]["eos_token_ids"]);assert eos==set(model.generation_config.eos_token_id)
        decode=GenerationConfig(do_sample=False,num_beams=1,repetition_penalty=1.,max_new_tokens=64,use_cache=True,eos_token_id=sorted(eos),pad_token_id=151643,bos_token_id=model.generation_config.bos_token_id)
        assert decode.to_dict()==json.loads(Path("results/20261028-trec-pruning-v1/manifest.json").read_text())["actual_generation_config"]
        m.update(status="checking_full",stage="full_engineering",model_class=type(model).__name__,runtime_full_attention_layers=28,
                 bf16_parameters=sum(param.numel() for param in model.parameters()),actual_generation_config=decode.to_dict());save(root/"manifest.json",m)
        def engineering(label,key,ids,trace=None):
            assert m["extra_correctness_outputs"]<24
            append(root/"engineering_outputs.jsonl",dict(stage=m["stage"],label=label,source_key=key,ids=ids,trace=trace))
            m["extra_correctness_outputs"]+=1;save(root/"manifest.json",m)
        def main_row(case,method,ids,trace,n,physical,initial_bytes,final_bytes):
            nonlocal active_cell
            text=tok.decode(ids[:-1] if ids[-1] in eos else ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
            row=dict(source_key=case["source_key"],method=method,status="ok",gold=case["gold"],ids=ids,text=text,
                decoded_with_terminal_tokens=tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False),
                generated_tokens=len(ids),terminated_eos=ids[-1] in eos,truncated=len(ids)==64 and ids[-1] not in eos,metrics=score(text,case["gold"]),
                prefix_tokens=n,physical_prefix_slots=physical,suffix_tokens=case["versions"]["with_demos"]["suffix_tokens"],
                prefix_kv_bytes=initial_bytes,final_live_kv_bytes=final_bytes,position_trace=trace,
                input_ids_sha256=case["versions"]["with_demos"]["input_ids_sha256"],review_flagged=case["source_key"] in cfg["review_flagged_keys"])
            rows.append(row);append(root/"generations.jsonl",row)
            m.update(rows=len(rows),new_model_outputs=len(rows));save(root/"manifest.json",m)
            active_cell=None
            print("MAIN",len(rows),method,case["source_key"],"exact",row["metrics"]["exact_correct"],flush=True)
        full_checks=[]
        for case,meta in zip(cases[:3],metadata[:3]):
            key=case["source_key"];v=case["versions"]["with_demos"];n=v["prefix_tokens"];suffix=v["input_ids"][n:]
            whole=native(model,v["input_ids"],decode);engineering("native_full",key,whole)
            reference=prefill(model,v["input_ids"][:n]);initial=cache_state(reference)
            branch=clone_cache(reference);plain,trace=decode_compact(model,branch,n,suffix,64,eos);engineering("nohook_full",key,plain,trace);del branch
            hooked,scores=scored_prefill(model,v["input_ids"][:n]);assert equal_cache(reference,hooked)
            branch=clone_cache(hooked);hids,htrace=decode_compact(model,branch,n,suffix,64,eos);engineering("hook_full",key,hids,htrace);del branch
            identities=[]
            for index,c in enumerate(conditions):
                idx={layer:select_prefix_indices(scores[layer],n,meta["header_ids"],c["pin_shared_header"]) for layer in range(28)}
                branch=gather_prefix_cache(hooked,idx,n,n,meta["header_ids"],c["pin_shared_header"])
                assert equal_cache(branch,hooked);identities.append(c["method"])
                if index==0:
                    identity,itrace=decode_compact(model,branch,n,suffix,64,eos);engineering("identity_full",key,identity,itrace)
                del branch
            record=dict(source_key=key,full_paths_equal=whole==plain==hids==identity,hook_all_kv_equal=True,identity_methods=identities,
                        reference_unchanged=cache_state(reference)==initial,native_ids=whole)
            full_checks.append(record);save(root/"full_engineering_checks.json",full_checks)
            assert record["full_paths_equal"] and record["reference_unchanged"]
            del reference,hooked,scores
        assert len(full_checks)==3 and m["extra_correctness_outputs"]==12
        save(root/"execution_snapshot_full.json",dict(cfg,status="full_engineering_passed",execution_enabled=True,enabled_methods=["full"],source_sha256=sources,
             full_engineering_sha256=sha((root/"full_engineering_checks.json").read_bytes())))
        m.update(status="running_full",stage="full_main");save(root/"manifest.json",m)
        for case in cases:
            active_cell=dict(source_key=case["source_key"],method="full",gold=case["gold"])
            v=case["versions"]["with_demos"];n=v["prefix_tokens"]
            reference=prefill(model,v["input_ids"][:n]);before=kv_bytes(reference)
            ids,trace=decode_compact(model,reference,n,v["input_ids"][n:],64,eos);after=kv_bytes(reference);del reference
            main_row(case,"full",ids,trace,n,n,before,after)
        baseline_rows=[r for r in rows if r["method"]=="full"];save(root/"full_baseline.json",baseline_rows)
        full_summary=summarize(cases,rows,conditions,cfg,"not_run_full_support_gate")
        save(root/"full_support_gate.json",dict(passed=full_summary["full_support_gate_passed"],criteria=cfg["full_support_gate"],observed=full_summary["methods"]["full"],baseline_sha256=sha((root/"full_baseline.json").read_bytes())))
        if not full_summary["full_support_gate_passed"]:
            save(root/"summary.json",full_summary)
            m.update(status="stopped_full_support_gate",stage="stopped_before_compression",end_unix=time.time(),full_support_gate_passed=False)
            m["artifact_sha256"]={str(p.relative_to(root)):sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and p.name!="manifest.json"}
            save(root/"manifest.json",m);print("STOP_FULL_GATE",json.dumps(full_summary["methods"]["full"]),flush=True);return
        print("FULL_GATE_PASSED",json.dumps(full_summary["methods"]["full"]),flush=True)
        m.update(status="checking_compressed",stage="compressed_engineering",full_support_gate_passed=True);save(root/"manifest.json",m)
        compressed_checks=[]
        for case,meta in zip(cases[:3],metadata[:3]):
            key=case["source_key"];v=case["versions"]["with_demos"];n=v["prefix_tokens"];suffix=v["input_ids"][n:]
            reference,scores=scored_prefill(model,v["input_ids"][:n]);initial=cache_state(reference);maps=build_maps(scores,key,n,meta,conditions)
            for method in ["adapted_snapkv_shared_anchors","uniform_random_shared_anchors_header_pinned"]:
                c=next(c for c in conditions if c["method"]==method)
                a_branch=gather_prefix_cache(reference,maps[method],n,n//2,meta["header_ids"],c["pin_shared_header"])
                nids,nt=native_compact(model,a_branch,n,suffix,decode);engineering("native_"+method,key,nids,nt);del a_branch
                b_branch=gather_prefix_cache(reference,maps[method],n,n//2,meta["header_ids"],c["pin_shared_header"])
                cids,ct=decode_compact(model,b_branch,n,suffix,64,eos);engineering("custom_"+method,key,cids,ct);del b_branch
                record=dict(source_key=key,method=method,ids_equal=nids==cids,traces_equal=nt==ct,native_ids=nids,custom_ids=cids)
                compressed_checks.append(record);save(root/"compressed_engineering_checks.json",compressed_checks)
                assert record["ids_equal"] and record["traces_equal"]
            assert cache_state(reference)==initial;del reference,scores,maps
        assert len(compressed_checks)==6 and m["extra_correctness_outputs"]==24
        save(root/"execution_snapshot_pruning.json",dict(cfg,status="full_support_and_compressed_engineering_passed",execution_enabled=True,
            source_sha256=sources,full_baseline_sha256=sha((root/"full_baseline.json").read_bytes()),
            full_support_gate_sha256=sha((root/"full_support_gate.json").read_bytes()),compressed_checks_sha256=sha((root/"compressed_engineering_checks.json").read_bytes())))
        m.update(status="running_compressed",stage="compressed_main");save(root/"manifest.json",m)
        (root/"actual_maps").mkdir();(root/"actual_scores").mkdir()
        for case,meta in zip(cases,metadata):
            key=case["source_key"];v=case["versions"]["with_demos"];n=v["prefix_tokens"]
            reference,scores=scored_prefill(model,v["input_ids"][:n]);initial=cache_state(reference);maps=build_maps(scores,key,n,meta,conditions)
            torch.save(scores,root/"actual_scores"/(key+".pt"))
            save(root/"actual_maps"/(key+".json"),{method:{str(layer):indices.tolist() for layer,indices in mapping.items()} for method,mapping in maps.items()})
            candidate_bytes=[]
            for c in conditions:
                branch=gather_prefix_cache(reference,maps[c["method"]],n,n//2,meta["header_ids"],c["pin_shared_header"])
                assert kv_bytes(branch)==(n//2)*57344;candidate_bytes.append(kv_bytes(branch));del branch
            assert len(set(candidate_bytes))==1
            for c in conditions:
                active_cell=dict(source_key=key,method=c["method"],gold=case["gold"])
                branch=gather_prefix_cache(reference,maps[c["method"]],n,n//2,meta["header_ids"],c["pin_shared_header"]);before=kv_bytes(branch)
                ids,trace=decode_compact(model,branch,n,v["input_ids"][n:],64,eos);after=kv_bytes(branch);del branch
                assert cache_state(reference)==initial
                main_row(case,c["method"],ids,trace,n,n//2,before,after)
            del reference,scores,maps
        result=summarize(cases,rows,conditions,cfg);save(root/"summary.json",result)
        assert len(rows)==50
        m.update(status="complete",stage="finished",end_unix=time.time(),full_support_gate_passed=True)
        m["artifact_sha256"]={str(p.relative_to(root)):sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and p.name!="manifest.json"}
        save(root/"manifest.json",m);print("COMPLETE",json.dumps({k:v for k,v in result.items() if k!="planned_cells"}),flush=True)
    except Exception as error:
        if active_cell is not None:
            row=dict(active_cell,status="error",error_type=type(error).__name__,error_message=str(error))
            rows.append(row);append(root/"generations.jsonl",row)
        if cases and cfg:save(root/"partial_summary.json",summarize(cases,rows,conditions,cfg))
        m.update(status="failed",end_unix=time.time(),rows=len(rows),new_model_outputs=sum(r["status"]=="ok" for r in rows),input_sha256=inputs,error_type=type(error).__name__,error_message=str(error))
        save(root/"manifest.json",m);(root/"traceback.txt").write_text(traceback.format_exc(),encoding="utf-8");raise


if __name__=="__main__":main()
