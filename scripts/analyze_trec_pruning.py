"""Independent CPU audit of frozen TREC pruning outputs, score maps and budgets."""
import argparse
from collections import Counter, defaultdict
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
    parser=argparse.ArgumentParser();parser.add_argument("--run",required=True);args=parser.parse_args()
    root=Path(args.run);assert not (root/"analysis_manifest.json").exists()
    code=Path(__file__).read_bytes();(root/"source_analyze_trec_pruning.py").write_bytes(code)
    analysis=dict(status="preparing",start_unix=time.time(),source_sha256=sha(code),args=vars(args),new_model_outputs=0)
    save(root/"analysis_manifest.json",analysis)
    try:
        m=json.loads((root/"manifest.json").read_text());assert m["status"]=="complete" and m["rows"]==128
        checks={}
        for name,digest in m["source_sha256"].items():checks["source_"+name]=sha((root/("source_"+name)).read_bytes())==digest
        for name,digest in m["artifact_sha256"].items():checks[name]=sha((root/name).read_bytes())==digest
        for name,digest in m["input_sha256"].items():checks[name]=sha(Path(name).read_bytes())==digest
        for name,digest in m["tokenizer_sha256"].items():checks["tokenizer/"+name]=sha((Path(m["args"]["model"])/name).read_bytes())==digest
        assert all(checks.values())
        cfg=json.loads((root/"prepared_config.json").read_text());snap=json.loads((root/"execution_snapshot.json").read_text())
        assert not cfg["execution_enabled"] and snap["execution_enabled"] and not snap["cpu_synthetic_only"]
        cases=[json.loads(s) for s in (root/"cases.jsonl").read_text().splitlines()]
        metadata=json.loads((root/"header_budget_metadata.json").read_text())
        rows=[json.loads(s) for s in (root/"generations.jsonl").read_text().splitlines()]
        baseline={r["source_key"]:r for r in json.loads((root/"baseline_with_demos.json").read_text())}
        assert len(rows)==128 and all(r["status"]=="ok" for r in rows)
        pairs={(r["source_key"],r["method"]):r for r in rows};assert len(pairs)==128
        assert len(baseline)==32 and sum(r["metrics"]["exact_correct"] for r in baseline.values())==19
        tokenizer=AutoTokenizer.from_pretrained(m["args"]["model"],local_files_only=True)
        inventory=json.loads(Path("results/20261028-trec-data-preflight-v2/label_inventory.json").read_text())
        scorer=make_scorer(Path("results/20261028-trec-data-preflight-v2/upstream/metrics.py").read_bytes(),inventory)
        eos=set(cfg["decode"]["eos_token_ids"])
        computed={};head_checks=0;oracle_checks=0;footprints=defaultdict(list);case_predictions=[]
        for c in cfg["conditions"]:
            computed[c["method"]]=dict(correct=0,label_format=0,truncated=0,compatibility_sum=0.,states=Counter(),changed_from_full=0)
        for case,meta in zip(cases,metadata):
            key=case["source_key"];n=meta["prefix_tokens"];budget=n//2
            maps=json.loads((root/"actual_maps"/(key+".json")).read_text())
            scores=torch.load(root/"actual_scores"/(key+".pt"),map_location="cpu",weights_only=True)
            assert set(scores)==set(range(28))
            predictions=dict(source_key=key,gold=case["gold"],full_prediction=baseline[key]["text"],methods={})
            bytes_this_case=[]
            for c in cfg["conditions"]:
                method=c["method"];row=pairs[(key,method)];ids=row["ids"]
                text=tokenizer.decode(ids[:-1] if ids[-1] in eos else ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
                assert text==row["text"] and row["gold"]==case["gold"]
                assert row["input_ids_sha256"]==case["versions"]["with_demos"]["input_ids_sha256"]
                assert row["metrics"]==scorer(text,case["gold"])
                assert row["terminated_eos"]==(ids[-1] in eos) and row["truncated"]==(len(ids)==64 and ids[-1] not in eos)
                assert row["prefix_kv_bytes"]==budget*57344
                assert row["final_live_kv_bytes"]==(budget+row["suffix_tokens"]+len(ids)-1)*57344
                assert row["physical_prefix_slots"]==budget and row["prefix_tokens"]==n
                for step,trace in enumerate(row["position_trace"]):
                    consumed=0 if step==0 else row["suffix_tokens"]+step-1
                    assert trace==dict(step=step,physical_start=budget+consumed,logical_start=n+consumed,input_width=row["suffix_tokens"] if step==0 else 1)
                assert len(row["position_trace"])==len(ids)
                required=set(meta["required_pinned_ids"] if c["pin_shared_header"] else meta["anchor_ids"])
                for layer in range(28):
                    tensor=scores[layer];assert tensor.shape==(1,4,n) and torch.isfinite(tensor).all()
                    for head in range(4):
                        positions=maps[method][str(layer)][0][head]
                        assert len(positions)==budget and positions==sorted(set(positions)) and positions[0]>=0 and positions[-1]<n
                        assert required<=set(positions)
                        footprints[method].append(len(set(positions)&set(meta["header_ids"])))
                        head_checks+=1
                    if layer in [0,27]:
                        values=random_prefix_scores(n,key,layer,4) if method.startswith("uniform_random") else scores[layer]
                        for head in range(4):
                            vector=values[0,head].tolist()
                            free=sorted((i for i in range(n) if i not in required),key=lambda i:(-vector[i],i))
                            expected=sorted(required|set(free[:budget-len(required)]))
                            assert maps[method][str(layer)][0][head]==expected
                            oracle_checks+=1
                rec=computed[method];correct=row["metrics"]["exact_correct"]
                rec["correct"]+=correct;rec["label_format"]+=row["metrics"]["whole_response_label_format"]
                rec["truncated"]+=row["truncated"];rec["compatibility_sum"]+=row["metrics"]["official_firstline_compatibility"]
                state=("C" if baseline[key]["metrics"]["exact_correct"] else "W")+"2"+("C" if correct else "W")
                rec["states"][state]+=1;rec["changed_from_full"]+=ids!=baseline[key]["ids"]
                predictions["methods"][method]=dict(prediction=text,transition=state,correct=correct)
                bytes_this_case.append(row["prefix_kv_bytes"])
            assert len(set(bytes_this_case))==1
            case_predictions.append(predictions)
        primary=json.loads((root/"summary.json").read_text())
        for method,rec in computed.items():
            original=primary["methods"][method]
            assert rec["correct"]==original["exact_correct"] and rec["label_format"]==original["label_format"]
            assert rec["truncated"]==original["truncated"] and rec["compatibility_sum"]==original["compatibility_sum"]
            rec["full_to_compressed"]={s:rec["states"][s] for s in ["C2C","C2W","W2C","W2W","N/A"]};del rec["states"]
            assert rec["full_to_compressed"]==original["full_to_compressed"]
            values=footprints[method];rec["header_retained_per_layer_head"]=dict(min=min(values),mean=sum(values)/len(values),max=max(values),full_header_count=200)
            rec["full_correct_denominator"]=19;rec["conditional_loss_rate"]=rec["full_to_compressed"]["C2W"]/19
        engineering=json.loads((root/"engineering_checks.json").read_text())
        extra=[json.loads(s) for s in (root/"engineering_outputs.jsonl").read_text().splitlines()]
        assert len(engineering)==3 and len(extra)==24
        for r in engineering:
            assert r["full_baseline_replayed"] and r["hook_all_kv_equal"] and r["reference_unchanged"]
            assert all(x["all_layer_kv_equal"] for x in r["identity"])
            assert all(x["ids_equal"] and x["traces_equal"] and x["native_ids"]==x["custom_ids"] for x in r["compressed_parity"])
        result=dict(baseline_correct=19,original_cases=32,methods=computed,head_map_checks=head_checks,python_sort_oracle_checks=oracle_checks,
                    all_four_method_bytes_equal_per_case=True,all_decoded_text_scores_recomputed=True,engineering_output_count=24,
                    case_predictions=case_predictions,new_model_outputs=0,
                    limitation="Descriptive fixed32-prompt pilot with natural labels; gold ambiguity and shared examples remain. No independent confirmation, safety task, significance claim or new algorithm.")
        assert head_checks==14336 and oracle_checks==1024
        save(root/"paired_analysis.json",result)
        analysis.update(status="complete",end_unix=time.time(),input_sha256={str(root/name):sha((root/name).read_bytes()) for name in ["manifest.json","generations.jsonl","summary.json","engineering_checks.json","engineering_outputs.jsonl"]},
                        all_checks_passed=checks,output_sha256=sha((root/"paired_analysis.json").read_bytes()))
        save(root/"analysis_manifest.json",analysis)
        print(json.dumps({k:v for k,v in result.items() if k!="case_predictions"}))
    except Exception as error:
        analysis.update(status="failed",end_unix=time.time(),error_type=type(error).__name__,error_message=str(error));save(root/"analysis_manifest.json",analysis);raise


if __name__=="__main__":main()
