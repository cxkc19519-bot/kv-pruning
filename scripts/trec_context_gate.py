"""Frozen 32-pair Full-KV capability gate. No pruning or sample replacement."""
import argparse
import ast
from collections import Counter
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, DynamicCache, GenerationConfig


PROPOSAL_SHA = "6e9c61d13d8a926ed0ce3d338d33642f95ff4aa48e2a014a8804896f65e2f91c"
MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
CONDITIONS = ["with_demos", "without_demos"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def append(path, value):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")


def cache_bytes(cache):
    return sum(t.numel()*t.element_size() for layer in cache.layers for t in [layer.keys,layer.values])


def cache_state(cache):
    return [(layer.keys.data_ptr(),layer.values.data_ptr(),layer.keys._version,layer.values._version,
             tuple(layer.keys.shape),tuple(layer.values.shape)) for layer in cache.layers]


def clone_cache(reference):
    branch=DynamicCache()
    for index,layer in enumerate(reference.layers):
        keys,values=layer.keys.clone(),layer.values.clone()
        assert keys.data_ptr()!=layer.keys.data_ptr() and values.data_ptr()!=layer.values.data_ptr()
        assert torch.equal(keys,layer.keys) and torch.equal(values,layer.values)
        branch.update(keys,values,index)
    assert cache_bytes(branch)==cache_bytes(reference)
    return branch


@torch.no_grad()
def prefill(model, ids):
    cache=DynamicCache()
    x=torch.tensor([ids],device=model.device)
    positions=torch.arange(len(ids),device=model.device)
    model.model(input_ids=x,past_key_values=cache,use_cache=True,
                position_ids=positions[None,:],cache_position=positions)
    assert len(cache.layers)==28 and all(layer.keys.shape[2]==len(ids) for layer in cache.layers)
    assert cache_bytes(cache)==len(ids)*57344
    return cache


@torch.inference_mode()
def native(model, ids, generation_config, cache=None, prefix_length=0):
    x=torch.tensor([ids],device=model.device)
    kwargs={}
    if cache is not None:
        assert cache.get_seq_length()==prefix_length
        kwargs=dict(past_key_values=cache,cache_position=torch.arange(prefix_length,prefix_length+len(ids),device=model.device))
    output=model.generate(input_ids=x,attention_mask=torch.ones((1,prefix_length+len(ids)),device=model.device,dtype=torch.long),
                          generation_config=generation_config,logits_to_keep=1,**kwargs)
    return output[0,len(ids):].tolist()


@torch.inference_mode()
def custom(model, cache, prefix_length, suffix, max_new, eos):
    assert cache.get_seq_length()==prefix_length
    inputs=torch.tensor([suffix],device=model.device)
    result=[]
    for step in range(max_new):
        physical=cache.get_seq_length()
        logical=prefix_length if step==0 else prefix_length+len(suffix)+step-1
        assert physical==logical, "This runner only supports Full KV"
        length=inputs.shape[1]
        output=model(input_ids=inputs,past_key_values=cache,use_cache=True,
                     position_ids=torch.arange(logical,logical+length,device=model.device)[None,:],
                     cache_position=torch.arange(physical,physical+length,device=model.device),logits_to_keep=1)
        token=int(output.logits[0,-1].argmax())
        result.append(token)
        del output
        assert cache.get_seq_length()==physical+length
        if token in eos:
            break
        inputs=torch.tensor([[token]],device=model.device)
    assert cache.get_seq_length()==prefix_length+len(suffix)+len(result)-1
    return result


def make_scorer(metrics_bytes, inventory):
    assert hashlib.sha1(b"blob "+str(len(metrics_bytes)).encode()+b"\0"+metrics_bytes).hexdigest()=="657cf773dcca6ef2aaeae96353055f208e95b35f"
    node=next(n for n in ast.parse(metrics_bytes).body if isinstance(n,ast.FunctionDef) and n.name=="classification_score")
    namespace={}
    exec(compile(ast.Module(body=[node],type_ignores=[]),"pinned_classification_score","exec"),namespace)
    official=namespace["classification_score"]
    def score(text,gold):
        firstline=text.lstrip("\n").split("\n")[0]
        return dict(official_firstline_compatibility=official(firstline,gold,all_classes=inventory),
                    whole_response_label_format=text.strip() in inventory,
                    exact_correct=text.strip()==gold)
    return score


def summarize(cases, rows, interpretation):
    by_pair={(r["source_key"],r["condition"]):r for r in rows}
    conditions={}
    for condition in CONDITIONS:
        records=[by_pair.get((c["source_key"],condition)) for c in cases]
        valid=[r for r in records if r and r["status"]=="ok"]
        conditions[condition]=dict(scheduled=32,generated=len(valid),
            exact_correct=sum(r["metrics"]["exact_correct"] for r in valid),
            label_format=sum(r["metrics"]["whole_response_label_format"] for r in valid),
            compatibility_sum=sum(r["metrics"]["official_firstline_compatibility"] for r in valid),
            compatibility_mean_original_denominator=sum(r["metrics"]["official_firstline_compatibility"] for r in valid)/32,
            truncated=sum(r["truncated"] for r in valid),errors=sum(r is not None and r["status"]=="error" for r in records),
            not_run=sum(r is None for r in records))
    transitions=Counter();pairs=[]
    for case in cases:
        a,b=[by_pair.get((case["source_key"],c)) for c in CONDITIONS]
        state=("C" if a["metrics"]["exact_correct"] else "W")+"2"+("C" if b["metrics"]["exact_correct"] else "W") if a and b and a["status"]==b["status"]=="ok" else "N/A"
        transitions[state]+=1
        pairs.append(dict(source_key=case["source_key"],gold=case["gold"],transition=state,
                          with_text=a.get("text") if a else None,without_text=b.get("text") if b else None))
    counts={s:transitions[s] for s in ["C2C","C2W","W2C","W2W","N/A"]}
    w=conditions["with_demos"]
    complete=len(rows)==64 and all(r["status"]=="ok" for r in rows)
    gate=complete and w["exact_correct"]>=interpretation["min_with_demos_exact_correct"] and w["truncated"]<=interpretation["max_with_demos_truncated"] and counts["C2W"]>=interpretation["min_with_correct_without_wrong_pairs"]
    return dict(conditions=conditions,transitions_with_to_without=counts,pairs=pairs,all_64_completed=complete,
                context_support_gate=gate,interpretation_gate=interpretation,
                decision="Independent compression design may be reviewed; not an automatic pruning run" if gate else "Stop compression progression for this fixed setup; no sample/prompt/model replacement",
                limitation="With-to-without-demos transitions, not Full-to-pruned. Different lengths/positions; descriptive feasibility only, not safety evidence or a unique causal mechanism.")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--proposal",required=True)
    parser.add_argument("--model",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    root=Path(args.out);root.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).read_bytes();(root/"source_trec_context_gate.py").write_bytes(source)
    manifest=dict(status="preparing",args=vars(args),start_unix=time.time(),rows=0,new_model_outputs=0,
                  pid=os.getpid(),source_sha256={"trec_context_gate.py":sha(source)},
                  versions={name:importlib.metadata.version(name) for name in ["torch","transformers","tokenizers","safetensors"]},
                  cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES","all"),scope="32 fixed paired Full-KV capability inputs; no pruning")
    save(root/"manifest.json",manifest)
    rows=[];cases=[];checks=[];inputs={}
    try:
        proposal_bytes=Path(args.proposal).read_bytes();assert sha(proposal_bytes)==PROPOSAL_SHA
        proposal=json.loads(proposal_bytes);assert proposal["execution_enabled"] is False
        assert Path(args.model).name==MODEL_REVISION and proposal["model_revision"]==MODEL_REVISION
        (root/"proposal.json").write_bytes(proposal_bytes)
        cases_path=Path(proposal["cases_path"]);raw=cases_path.read_bytes();assert sha(raw)==proposal["cases_sha256"]
        cases=[json.loads(line) for line in raw.decode().splitlines()]
        assert len(cases)==32 and [r["source_key"] for r in cases]==proposal["frozen_source_keys"]
        (root/"cases.jsonl").write_bytes(raw)
        prep=cases_path.parent
        token_sha_path=Path("results/20261028-trec-data-preflight-v2/tokenizer_sha256.json")
        token_hashes=json.loads(token_sha_path.read_text())
        for name,value in token_hashes.items():
            assert sha((Path(args.model)/name).read_bytes())==value,name
        tok=AutoTokenizer.from_pretrained(args.model,local_files_only=True)
        metadata=Path("results/20261028-trec-data-preflight-v2")
        inventory=json.loads((metadata/"label_inventory.json").read_text())
        assert len(inventory)==50 and proposal["max_main_outputs"]==64
        metrics_bytes=(metadata/"upstream/metrics.py").read_bytes()
        score=make_scorer(metrics_bytes,inventory)
        fixtures=json.loads((prep/"scorer_fixtures.json").read_text())
        for fixture in fixtures:
            got=score(fixture["response"],fixture["gold"])
            assert got==dict(official_firstline_compatibility=fixture["official_firstline_compatibility"],
                             whole_response_label_format=fixture["whole_response_exact_label_format"],exact_correct=fixture["whole_response_gold_exact"])
        for case in cases:
            assert case["gold"] in inventory
            for condition in CONDITIONS:
                v=case["versions"][condition]
                ids=tok.apply_chat_template(v["messages"],tokenize=True,add_generation_prompt=True)
                prefix=tok.apply_chat_template(v["messages"][:1],tokenize=True,add_generation_prompt=False)
                assert ids==v["input_ids"] and len(prefix)==v["prefix_tokens"] and ids[:len(prefix)]==prefix
                assert sha(json.dumps(ids,separators=(",",":")).encode())==v["input_ids_sha256"]
                assert len(ids)-len(prefix)==v["suffix_tokens"] and len(ids)+64<=8192
            a,b=[case["versions"][c] for c in CONDITIONS]
            assert a["input_ids"][a["prefix_tokens"]:]==b["input_ids"][b["prefix_tokens"]:]
        for path in [Path(args.proposal),cases_path,token_sha_path,prep/"manifest.json",prep/"scorer_fixtures.json",metadata/"label_inventory.json",metadata/"upstream/metrics.py",Path(args.model)/"config.json",Path(args.model)/"generation_config.json"]:
            inputs[str(path)]=sha(path.read_bytes())
        manifest.update(status="cpu_checks_passed",input_sha256=inputs,tokenizer_sha256=token_hashes,scorer_fixtures_passed=len(fixtures),frozen_inputs_retokenized=64)
        save(root/"manifest.json",manifest)
        print("CPU_CHECKS_PASSED",flush=True)
        model=AutoModelForCausalLM.from_pretrained(args.model,torch_dtype=torch.bfloat16,attn_implementation="sdpa",local_files_only=True).eval().to("cuda:0")
        assert model.config.model_type=="qwen2" and len(model.model.layers)==28
        assert all(layer.self_attn.sliding_window is None for layer in model.model.layers)
        assert all(p.dtype==torch.bfloat16 for p in model.parameters())
        eos=model.generation_config.eos_token_id
        eos=sorted(set(eos if isinstance(eos,list) else [eos]));assert all(isinstance(i,int) for i in eos)
        decode=GenerationConfig(do_sample=False,num_beams=1,repetition_penalty=1.,max_new_tokens=64,use_cache=True,
                                eos_token_id=eos,pad_token_id=tok.pad_token_id if tok.pad_token_id is not None else eos[0],bos_token_id=model.generation_config.bos_token_id)
        manifest.update(status="checking_generation_paths",actual_generation_config=decode.to_dict(),runtime_full_attention_layers=28,
                        bf16_parameters=sum(p.numel() for p in model.parameters()),model_class=type(model).__name__)
        save(root/"manifest.json",manifest)
        for case in cases[:3]:
            for condition in CONDITIONS:
                v=case["versions"][condition];n=v["prefix_tokens"]
                full_ids=v["input_ids"];suffix=full_ids[n:]
                whole=native(model,full_ids,decode)
                reference=prefill(model,full_ids[:n]);initial=cache_state(reference)
                branch=clone_cache(reference);cached=native(model,suffix,decode,branch,n);del branch
                assert cache_state(reference)==initial
                branch=clone_cache(reference);custom_ids=custom(model,branch,n,suffix,64,set(eos));del branch
                assert cache_state(reference)==initial
                record=dict(source_key=case["source_key"],condition=condition,prefix_tokens=n,suffix_tokens=len(suffix),
                            prefix_kv_bytes=cache_bytes(reference),bytes_per_prefix_token=cache_bytes(reference)//n,
                            native_full_ids=whole,native_cached_ids=cached,custom_cached_ids=custom_ids,
                            native_full_text=tok.decode(whole,skip_special_tokens=True),native_cached_text=tok.decode(cached,skip_special_tokens=True),
                            custom_cached_text=tok.decode(custom_ids,skip_special_tokens=True),
                            passed=whole==cached==custom_ids,reference_unmodified=True,clone_exact=True)
                checks.append(record);save(root/"correctness_checks.json",checks)
                del reference
                assert record["passed"],"Generation path gate failed; no main outputs permitted"
                print("PATH_CHECK",condition,case["source_key"],"PASS",flush=True)
        assert len(checks)==6 and all(c["passed"] for c in checks)
        snapshot=dict(proposal,status="engineering_gate_passed_before_main_outputs",execution_enabled=True,
                      parent_proposal_sha256=PROPOSAL_SHA,runner_sha256=sha(source),cases_sha256=sha(raw),tokenizer_sha256=token_hashes,
                      correctness_checks_sha256=sha((root/"correctness_checks.json").read_bytes()),decode_actual=decode.to_dict())
        save(root/"execution_snapshot.json",snapshot)
        manifest.update(status="running_main",engineering_gate_passed=True,extra_correctness_outputs=18)
        save(root/"manifest.json",manifest)
        for case in cases:
            for condition in CONDITIONS:
                row=dict(source_key=case["source_key"],condition=condition,gold=case["gold"],status="ok")
                try:
                    v=case["versions"][condition];n=v["prefix_tokens"]
                    reference=prefill(model,v["input_ids"][:n]);kv_bytes=cache_bytes(reference)
                    ids=custom(model,reference,n,v["input_ids"][n:],64,set(eos))
                    del reference
                    response_ids=ids[:-1] if ids[-1] in eos else ids
                    text=tok.decode(response_ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
                    row.update(text=text,ids=ids,generated_tokens=len(ids),terminated_eos=ids[-1] in eos,
                               decoded_with_terminal_tokens=tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False),
                               truncated=len(ids)==64 and ids[-1] not in eos,metrics=score(text,case["gold"]),
                               prefix_tokens=n,suffix_tokens=v["suffix_tokens"],prefix_kv_bytes=kv_bytes,input_ids_sha256=v["input_ids_sha256"])
                    rows.append(row);append(root/"generations.jsonl",row)
                except Exception as error:
                    row.update(status="error",error_type=type(error).__name__,error_message=str(error))
                    rows.append(row);append(root/"generations.jsonl",row);raise
                manifest.update(rows=len(rows),new_model_outputs=sum(r["status"]=="ok" for r in rows))
                save(root/"manifest.json",manifest)
                print("MAIN",len(rows),condition,case["source_key"],"exact",row["metrics"]["exact_correct"],flush=True)
        result=summarize(cases,rows,proposal["interpretation"]);save(root/"summary.json",result)
        manifest.update(status="complete",rows=64,new_model_outputs=64,end_unix=time.time(),context_support_gate=result["context_support_gate"],
                        artifact_sha256={n:sha((root/n).read_bytes()) for n in ["proposal.json","cases.jsonl","correctness_checks.json","execution_snapshot.json","generations.jsonl","summary.json"]})
        save(root/"manifest.json",manifest)
        print("COMPLETE",json.dumps({k:v for k,v in result.items() if k!="pairs"}),flush=True)
    except Exception as error:
        if cases:
            proposal=json.loads((root/"proposal.json").read_text())
            save(root/"partial_summary.json",summarize(cases,rows,proposal["interpretation"]))
        manifest.update(status="failed",rows=len(rows),new_model_outputs=sum(r["status"]=="ok" for r in rows),end_unix=time.time(),
                        input_sha256=inputs,error_type=type(error).__name__,error_message=str(error),correctness_cases_logged=len(checks))
        save(root/"manifest.json",manifest);(root/"traceback.txt").write_text(traceback.format_exc(),encoding="utf-8")
        raise


if __name__=="__main__":
    main()
