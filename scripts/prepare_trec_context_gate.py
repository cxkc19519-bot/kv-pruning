"""Freeze a CPU-prepared capability gate, not a KV compression experiment."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import time


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-run",required=True)
    parser.add_argument("--out",required=True)
    parser.add_argument("--tokenizer",required=True)
    args=parser.parse_args()
    out=Path(args.out);out.mkdir(exist_ok=False)
    source=Path(__file__).read_bytes();(out/"source_prepare_trec_context_gate.py").write_bytes(source)
    manifest=dict(status="preparing",rows=0,new_model_outputs=0,args=vars(args),start_unix=time.time(),source_sha256=sha(source))
    save(out/"manifest.json",manifest)
    try:
        data_run=Path(args.data_run)
        assert json.loads((data_run/"manifest.json").read_text())["status"]=="complete"
        raw=(data_run/"data/trec.jsonl").read_bytes()
        assert sha(raw)=="20a88e14f7442f58a39082cdd7396f1093ea8162da0a4ea7ead7d6757514c8f4"
        rows={r["_id"]:r for r in map(json.loads,raw.decode().splitlines())}
        audit=json.loads((data_run/"cases_cpu_audit.json").read_text())
        ambiguous={r["question"] for r in json.loads((data_run/"duplicate_conflict_audit.json").read_text())["demo_question_conflicts"]}
        exclusions=[];eligible=[]
        for entry in audit:
            reasons=[]
            if not 1024<=entry["prefix_tokens"]<=4096:reasons.append("source_adaptation_prefix_outside_1024_4096")
            if entry["local_demo_conflicts"]:reasons.append("contradictory_demo_labels_in_this_context")
            context=rows[entry["source_key"]]["context"]
            if any("Question: "+question+"\nType:" in context for question in ambiguous):
                reasons.append("contains_globally_ambiguous_demo_question")
            if entry["target_in_own_demos"]:reasons.append("target_question_present_in_own_examples")
            if reasons:exclusions.append(dict(source_key=entry["source_key"],reasons=reasons))
            else:eligible.append(entry)
        eligible.sort(key=lambda r:r["preflight_order_sha256"])
        save(out/"eligibility.json",dict(order="ascending SHA256('20261028:trec:' + source _id)",eligible=[r["source_key"] for r in eligible],exclusions=exclusions))
        assert len(eligible)>=32,"Stop without loosening eligibility or replacing by model outcomes"
        chosen=eligible[:32]
        import torch
        from transformers import AutoTokenizer
        assert not torch.cuda.is_initialized()
        tokenizer=AutoTokenizer.from_pretrained(args.tokenizer,local_files_only=True)
        inventory=rows[chosen[0]["source_key"]]["all_classes"]
        header="Classify the question. Return exactly one label from the following list and no other text.\nLabels:\n"+"\n".join(inventory)+"\n\nExamples:\n"
        cases=[];lengths=[]
        for entry in chosen:
            row=rows[entry["source_key"]]
            versions={}
            for condition,examples in [("with_demos",row["context"]),("without_demos","")]:
                messages=[dict(role="system",content=header+examples),dict(role="user",content=row["input"])]
                prefix=tokenizer.apply_chat_template(messages[:1],tokenize=True,add_generation_prompt=False)
                ids=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)
                assert ids[:len(prefix)]==prefix and len(ids)>len(prefix)
                assert len(ids)+64<=8192,"No truncation or replacement; stop and review resources"
                versions[condition]=dict(messages=messages,prefix_tokens=len(prefix),suffix_tokens=len(ids)-len(prefix),
                                         input_ids=ids,input_ids_sha256=sha(json.dumps(ids,separators=(",",":")).encode()))
            assert versions["with_demos"]["messages"][0]["content"]==header+row["context"]
            assert versions["without_demos"]["messages"][0]["content"]==header
            assert versions["with_demos"]["messages"][1]==versions["without_demos"]["messages"][1]
            lengths.append(versions["with_demos"]["prefix_tokens"])
            cases.append(dict(source_key=row["_id"],source_line_0based=entry["source_line_0based"],raw_line_sha256=entry["raw_line_sha256"],
                              gold=row["answers"][0],source_context_sha256=entry["context_sha256"],versions=versions))
        cases_data="\n".join(json.dumps(r,ensure_ascii=False) for r in cases)+"\n"
        (out/"cases.jsonl").write_text(cases_data,encoding="utf-8")
        # Reviewed pure official function only; no imports or top-level upstream execution.
        metrics=(data_run/"upstream/metrics.py").read_bytes()
        assert hashlib.sha1(b"blob "+str(len(metrics)).encode()+b"\0"+metrics).hexdigest()=="657cf773dcca6ef2aaeae96353055f208e95b35f"
        node=next(n for n in ast.parse(metrics).body if isinstance(n,ast.FunctionDef) and n.name=="classification_score")
        namespace={};exec(compile(ast.Module(body=[node],type_ignores=[]),"pinned_classification_score","exec"),namespace)
        score=namespace["classification_score"]
        fixtures=[("Individual","Individual",1.,True,True),
                  ("Individual\nExtra text","Individual",1.,False,False),
                  ("Individual or City","Individual",.5,False,False),
                  ("individual","Individual",0.,False,False),
                  ("", "Individual",0.,False,False),
                  ("City","Individual",0.,True,False),
                  ("Label: Individual","Individual",1.,False,False),
                  ("Definition of something","Definition of something",1.,True,True)]
        checked=[]
        for response,gold,expected_compat,expected_format,expected_exact in fixtures:
            firstline=response.lstrip("\n").split("\n")[0]
            compatibility=score(firstline,gold,all_classes=inventory)
            format_ok=response.strip() in inventory
            exact=response.strip()==gold
            assert (compatibility,format_ok,exact)==(expected_compat,expected_format,expected_exact)
            checked.append(dict(response=response,gold=gold,official_firstline_compatibility=compatibility,
                                whole_response_exact_label_format=format_ok,whole_response_gold_exact=exact))
        save(out/"scorer_fixtures.json",checked)
        config=dict(status="cpu_prepared_pending_runner_and_cache_checks",execution_enabled=False,
                    purpose="Limited capability/context-dependence calibration, no security/novelty claim or compression comparison",
                    model="Qwen/Qwen2.5-7B-Instruct",model_revision="a09a35458c702b33eeacc393d103063234e8bc28",
                    source_dataset="zai-org/LongBench",dataset_revision="5e628be450b7e67fb7ae6e201bd6d8f7056f7672",
                    trec_data_sha256=sha(raw),cases_path=str(out/"cases.jsonl"),cases_sha256=sha((out/"cases.jsonl").read_bytes()),
                    frozen_source_keys=[r["source_key"] for r in cases],source_eligibility="Native task-header+demo prefix1024..4096, no local contradictory demo labels or globally ambiguous demo question, no exact target in own demos; select first32 hash order before inference; no padding or truncation",
                    selection_limitation="Shorter-source subset, unbalanced original labels, not representative of all LongBench/TREC lengths; metadata consistency does not prove semantic gold correctness",
                    frontend="Explicit new role/header adaptation with same full50-label inventory and exact-label instruction in both conditions; original demonstrations and query bytes unchanged",
                    shared_system_header=header,conditions=["with_demos_full_kv","without_demos_full_kv"],max_main_outputs=64,
                    decode=dict(do_sample=False,repetition_penalty=1.,max_new_tokens=64,dtype="bfloat16",attention="sdpa"),
                    metrics=["official_firstline_classification_compatibility","whole_response_exact_label_format","whole_response_gold_exact","truncation","all32paired_C2C_C2W_W2C_W2W"],
                    primary_correctness="Raw response.strip() == original gold exactly; no first-line extraction, quote removal, case folding or loose rescue",
                    engineering_gate=["frozen cases/source/tokenizer SHA match", "first3 cases in both input conditions: native full/native cached/custom cached output token agreement", "logical positions and physical cache lengths checked", "generation eos handling/penalty match", "all errors and missing outcomes retain original32 denominator"],
                    interpretation=dict(min_with_demos_exact_correct=16,max_with_demos_truncated=3,min_with_correct_without_wrong_pairs=8,
                                        meaning="Descriptive feasibility thresholds, not significance/power or unique causal mechanism. Require enough useful examples before any compression study; no outcome-based replacement or retuning"),
                    on_insufficient_support="Stop; keep all64 outcomes and report that this fixed pilot does not establish useful context dependence; do not reinterpret as safety result or launch pruning",
                    future_compression="Not defined in this config; requires separate frozen design and equal-byte/shared-anchor/hook/100%-selection checks",
                    old_gates="No changes to stopped native IFEval proposal or failed AccessDenied gates")
        save(out/"proposal.json",config)
        summary=dict(source_eligible=len(eligible),selected=32,source_keys=config["frozen_source_keys"],
                     cases_sha256=config["cases_sha256"],prepared_with_demos_prefix=dict(min=min(lengths),max=max(lengths)),
                     without_demos_prefix_tokens=cases[0]["versions"]["without_demos"]["prefix_tokens"],
                     selected_gold_distribution=dict(__import__('collections').Counter(r["gold"] for r in cases)),
                     scorer_fixtures_passed=len(checked),new_model_outputs=0,cuda_initialized=torch.cuda.is_initialized(),execution_enabled=False)
        assert not torch.cuda.is_initialized()
        save(out/"summary.json",summary)
        manifest.update(status="complete",end_unix=time.time(),
                        input_sha256={str(data_run/name):sha((data_run/name).read_bytes()) for name in ["manifest.json","data/trec.jsonl","cases_cpu_audit.json","duplicate_conflict_audit.json","upstream/metrics.py"]},
                        artifact_sha256={str(p.relative_to(out)):sha(p.read_bytes()) for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'})
        save(out/"manifest.json",manifest)
        print(json.dumps(summary,ensure_ascii=False))
        print('PROPOSAL_SHA256',sha((out/"proposal.json").read_bytes()))
    except Exception as error:
        manifest.update(status="failed",end_unix=time.time(),error_type=type(error).__name__,error_message=str(error))
        save(out/"manifest.json",manifest)
        raise


if __name__=="__main__":
    main()
