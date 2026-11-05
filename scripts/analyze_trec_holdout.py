"""CPU re-score and engineering/position/map audit for the staged ten-case run."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import torch
from transformers import AutoTokenizer
from trec_context_gate import make_scorer
from trec_pruning_utils import random_prefix_scores


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")


def main():
    p=argparse.ArgumentParser();p.add_argument("--run",required=True);a=p.parse_args();root=Path(a.run)
    assert not (root/"analysis_manifest.json").exists()
    source=Path(__file__).read_bytes();(root/"source_analyze_trec_holdout.py").write_bytes(source)
    analysis=dict(status="preparing",start_unix=time.time(),source_sha256=sha(source),new_model_outputs=0,args=vars(a))
    save(root/"analysis_manifest.json",analysis)
    try:
        m=json.loads((root/"manifest.json").read_text());assert m["status"] in ["complete","stopped_full_support_gate"]
        checks={}
        for name,d in m["source_sha256"].items():checks["source_"+name]=sha((root/("source_"+name)).read_bytes())==d
        for name,d in m["input_sha256"].items():checks[name]=sha(Path(name).read_bytes())==d
        for name,d in m["artifact_sha256"].items():checks[name]=sha((root/name).read_bytes())==d
        for name,d in m["tokenizer_sha256"].items():checks["tokenizer/"+name]=sha((Path(m["args"]["model"])/name).read_bytes())==d
        assert all(checks.values())
        cfg=json.loads((root/"proposal.json").read_text());cases=[json.loads(s) for s in (root/"cases.jsonl").read_text().splitlines()]
        meta={r["source_key"]:r for r in json.loads((root/"header_budget_metadata.json").read_text())}
        rows=[json.loads(s) for s in (root/"generations.jsonl").read_text().splitlines()]
        assert len(rows)==m["new_model_outputs"] and all(r["status"]=="ok" for r in rows)
        by={(r["source_key"],r["method"]):r for r in rows};assert len(by)==len(rows)
        full={c["source_key"]:by[(c["source_key"],"full")] for c in cases}
        full_correct=sum(r["metrics"]["exact_correct"] for r in full.values())
        assert json.loads((root/"summary.json").read_text())["actual_full_correct_denominator"]==full_correct
        tok=AutoTokenizer.from_pretrained(m["args"]["model"],local_files_only=True)
        data=Path("results/20261028-trec-data-preflight-v2");inventory=json.loads((data/"label_inventory.json").read_text())
        scorer=make_scorer((data/"upstream/metrics.py").read_bytes(),inventory);eos=set(cfg["decode"]["eos_token_ids"])
        transitions={c["method"]:Counter() for c in cfg["conditions"]};formats={c["method"]:Counter() for c in cfg["conditions"]}
        invalid=[];flagged=[]
        for row in rows:
            ids=row["ids"];text=tok.decode(ids[:-1] if ids[-1] in eos else ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
            assert text==row["text"] and row["metrics"]==scorer(text,row["gold"])
            assert row["terminated_eos"]==(ids[-1] in eos) and row["truncated"]==(len(ids)==64 and ids[-1] not in eos)
            original=next(c for c in cases if c["source_key"]==row["source_key"])
            assert row["gold"]==original["gold"] and row["input_ids_sha256"]==original["versions"]["with_demos"]["input_ids_sha256"]
            n,physical=row["prefix_tokens"],row["physical_prefix_slots"]
            assert physical==(n if row["method"]=="full" else n//2) and row["prefix_kv_bytes"]==physical*57344
            assert row["final_live_kv_bytes"]==(physical+row["suffix_tokens"]+len(ids)-1)*57344
            assert len(row["position_trace"])==len(ids)
            for step,trace in enumerate(row["position_trace"]):
                consumed=0 if step==0 else row["suffix_tokens"]+step-1
                assert trace==dict(step=step,physical_start=physical+consumed,logical_start=n+consumed,input_width=row["suffix_tokens"] if step==0 else 1)
            if row["method"]!="full":
                base=full[row["source_key"]]
                state=("C" if base["metrics"]["exact_correct"] else "W")+"2"+("C" if row["metrics"]["exact_correct"] else "W")
                transitions[row["method"]][state]+=1
                f=("valid" if base["metrics"]["whole_response_label_format"] else "invalid")+"2"+("valid" if row["metrics"]["whole_response_label_format"] else "invalid")
                formats[row["method"]][f]+=1
                if not row["metrics"]["whole_response_label_format"]:
                    invalid.append(dict(source_key=row["source_key"],method=row["method"],gold=row["gold"],text=text,full_text=base["text"],full_exact=base["metrics"]["exact_correct"],review_flagged=row["review_flagged"]))
            if row["review_flagged"]:flagged.append(dict(source_key=row["source_key"],method=row["method"],gold=row["gold"],text=text,exact=row["metrics"]["exact_correct"]))
        gate=json.loads((root/"full_support_gate.json").read_text());criteria=cfg["full_support_gate"]
        observed_full=[r for r in rows if r["method"]=="full"]
        passed=len(observed_full)==10 and full_correct>=criteria["min_whole_response_exact_correct"] and sum(r["metrics"]["whole_response_label_format"] for r in observed_full)==10 and not any(r["truncated"] for r in observed_full)
        assert passed==gate["passed"]
        # File order proves every main Full observation precedes any main compressed cell.
        assert all(r["method"]=="full" for r in rows[:10])
        engineering=[json.loads(s) for s in (root/"engineering_outputs.jsonl").read_text().splitlines()]
        assert all(r["stage"]=="full_engineering" for r in engineering[:12])
        if not passed:
            assert len(rows)==10 and len(engineering)==12 and not (root/"compressed_engineering_checks.json").exists()
        else:
            assert len(rows)==50 and len(engineering)==24 and all(r["stage"]=="compressed_engineering" for r in engineering[12:])
        full_checks=json.loads((root/"full_engineering_checks.json").read_text())
        assert len(full_checks)==3 and all(r["full_paths_equal"] and r["hook_all_kv_equal"] and r["reference_unchanged"] and len(r["identity_methods"])==4 for r in full_checks)
        head_checks=oracle_checks=0
        if passed:
            compressed=json.loads((root/"compressed_engineering_checks.json").read_text())
            assert len(compressed)==6 and all(r["ids_equal"] and r["traces_equal"] for r in compressed)
            for case in cases:
                key=case["source_key"];metadata=meta[key];n=metadata["prefix_tokens"];budget=n//2
                scores=torch.load(root/"actual_scores"/(key+".pt"),map_location="cpu",weights_only=True)
                maps=json.loads((root/"actual_maps"/(key+".json")).read_text());bytes_per_method=[]
                for c in cfg["conditions"][1:]:
                    method=c["method"];required=set(metadata["required_pinned_ids"] if c["pin_shared_header"] else metadata["anchor_ids"])
                    for layer in range(28):
                        assert scores[layer].shape==(1,4,n) and torch.isfinite(scores[layer]).all()
                        for head in range(4):
                            ids=maps[method][str(layer)][0][head]
                            assert len(ids)==budget and ids==sorted(set(ids)) and min(ids)>=0 and max(ids)<n and required<=set(ids)
                            head_checks+=1
                        if layer in [0,27]:
                            values=random_prefix_scores(n,key,layer,4) if method.startswith("uniform_random") else scores[layer]
                            for head in range(4):
                                vector=values[0,head].tolist();free=sorted((i for i in range(n) if i not in required),key=lambda i:(-vector[i],i))
                                assert maps[method][str(layer)][0][head]==sorted(required|set(free[:budget-len(required)]));oracle_checks+=1
                    bytes_per_method.append(by[(key,method)]["prefix_kv_bytes"])
                assert len(set(bytes_per_method))==1
            assert head_checks==4480 and oracle_checks==320
        original_summary=json.loads((root/"summary.json").read_text());methods={}
        for c in cfg["conditions"]:
            method=c["method"];selected=[r for r in rows if r["method"]==method]
            rec=dict(n=10,generated=len(selected),exact_correct=sum(r["metrics"]["exact_correct"] for r in selected),label_format=sum(r["metrics"]["whole_response_label_format"] for r in selected),
                     truncated=sum(r["truncated"] for r in selected),not_run=10-len(selected))
            assert rec["exact_correct"]==original_summary["methods"][method]["exact_correct"] and rec["label_format"]==original_summary["methods"][method]["label_format"]
            if method!="full":
                rec.update(full_to_compressed={s:transitions[method][s] for s in ["C2C","C2W","W2C","W2W","N/A"]},
                           format_transitions={s:formats[method][s] for s in ["valid2valid","valid2invalid","invalid2valid","invalid2invalid","N/A"]},full_correct_denominator=full_correct)
                if passed:assert rec["full_to_compressed"]==original_summary["methods"][method]["full_to_compressed"]
            methods[method]=rec
        result=dict(methods=methods,full_support_gate_passed=passed,all_main_outputs_redecoded=True,head_map_checks=head_checks,python_sort_oracle_checks=oracle_checks,
                    engineering_outputs=len(engineering),invalid_label_outputs=invalid,preflagged_case_listing=flagged,
                    stage_order_checked=True,new_model_outputs=0,interpretation="Single fixed holdout-question recheck; no further automatic calibration expansion")
        save(root/"paired_analysis.json",result)
        analysis.update(status="complete",end_unix=time.time(),all_checks_passed=checks,
            input_sha256={str(root/name):sha((root/name).read_bytes()) for name in ["manifest.json","generations.jsonl","summary.json","proposal.json","full_support_gate.json","engineering_outputs.jsonl"]},output_sha256=sha((root/"paired_analysis.json").read_bytes()))
        save(root/"analysis_manifest.json",analysis);print(json.dumps(result,ensure_ascii=False))
    except Exception as error:
        analysis.update(status="failed",end_unix=time.time(),error_type=type(error).__name__,error_message=str(error));save(root/"analysis_manifest.json",analysis);raise


if __name__=="__main__":main()
