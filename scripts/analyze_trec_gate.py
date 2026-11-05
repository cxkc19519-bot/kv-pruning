"""Read-only re-score of a completed TREC Full-KV capability gate."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",required=True);args=parser.parse_args()
    root=Path(args.run);assert not (root/"analysis_manifest.json").exists()
    source=Path(__file__).read_bytes();(root/"source_analyze_trec_gate.py").write_bytes(source)
    manifest=json.loads((root/"manifest.json").read_text());assert manifest["status"]=="complete"
    checked={}
    for name,digest in manifest["source_sha256"].items():
        checked["source_"+name]=sha((root/("source_"+name)).read_bytes())==digest
    for name,digest in manifest["artifact_sha256"].items():
        checked[name]=sha((root/name).read_bytes())==digest
    for name,digest in manifest["input_sha256"].items():
        checked[name]=sha(Path(name).read_bytes())==digest
    assert all(checked.values())
    rows=[json.loads(s) for s in (root/"generations.jsonl").read_text().splitlines()]
    cases=[json.loads(s) for s in (root/"cases.jsonl").read_text().splitlines()]
    proposal=json.loads((root/"proposal.json").read_text())
    previous=json.loads((root/"summary.json").read_text())
    paths=json.loads((root/"correctness_checks.json").read_text())
    assert len(rows)==64 and len(paths)==6 and all(c["passed"] for c in paths)
    inventory=json.loads(Path("results/20261028-trec-data-preflight-v2/label_inventory.json").read_text())
    eos=set(manifest["actual_generation_config"]["eos_token_id"])
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(manifest["args"]["model"],local_files_only=True)
    by_pair={};confusions=defaultdict(Counter)
    for row in rows:
        assert row["status"]=="ok" and (row["source_key"],row["condition"]) not in by_pair
        by_pair[(row["source_key"],row["condition"])]=row
        decoded=tokenizer.decode(row["ids"][:-1] if row["ids"][-1] in eos else row["ids"],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        assert decoded==row["text"] and row["terminated_eos"]==(row["ids"][-1] in eos)
        assert row["metrics"]["exact_correct"]==(decoded.strip()==row["gold"])
        assert row["metrics"]["whole_response_label_format"]==(decoded.strip() in inventory)
        assert row["prefix_kv_bytes"]==row["prefix_tokens"]*57344
        if not row["metrics"]["exact_correct"]:confusions[row["condition"]][(row["gold"],decoded.strip())]+=1
    transitions=Counter();per_case=[]
    for case in cases:
        a,b=[by_pair[(case["source_key"],c)] for c in ["with_demos","without_demos"]]
        assert a["gold"]==b["gold"]==case["gold"]
        state=("C" if a["text"].strip()==case["gold"] else "W")+"2"+("C" if b["text"].strip()==case["gold"] else "W")
        transitions[state]+=1
        per_case.append(dict(source_key=case["source_key"],gold=case["gold"],with_prediction=a["text"],without_prediction=b["text"],transition=state))
    counts={state:transitions[state] for state in ["C2C","C2W","W2C","W2W","N/A"]}
    assert counts==previous["transitions_with_to_without"]
    conditions={c:dict(n=32,correct=sum(r["text"].strip()==r["gold"] for r in rows if r["condition"]==c),
                        format_ok=sum(r["text"].strip() in inventory for r in rows if r["condition"]==c),
                        truncated=sum(r["truncated"] for r in rows if r["condition"]==c)) for c in ["with_demos","without_demos"]}
    for condition,rec in conditions.items():assert rec["correct"]==previous["conditions"][condition]["exact_correct"]
    thresholds=proposal["interpretation"]
    gate=conditions["with_demos"]["correct"]>=thresholds["min_with_demos_exact_correct"] and conditions["with_demos"]["truncated"]<=thresholds["max_with_demos_truncated"] and counts["C2W"]>=thresholds["min_with_correct_without_wrong_pairs"]
    assert gate==previous["context_support_gate"]
    result=dict(conditions=conditions,transitions_with_to_without=counts,context_support_gate=gate,
                net_correct_difference=counts["C2W"]-counts["W2C"],
                errors=[dict(condition=c,gold=g,pred=p,count=n) for c,v in confusions.items() for (g,p),n in v.items()],
                per_case=per_case,all_outputs_label_format=True if all(v["format_ok"]==32 for v in conditions.values()) else False,
                interpretation="Example availability helps some classifications in this frozen pilot; no observed output-label-format violations, no pruning performed, no safety-specific effect established")
    (root/"paired_analysis.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    analysis=dict(status="complete",source_sha256=sha(source),input_sha256={n:sha((root/n).read_bytes()) for n in ["manifest.json","generations.jsonl","cases.jsonl","proposal.json","summary.json","correctness_checks.json"]},
                  all_checks_passed=checked,output_sha256=sha((root/"paired_analysis.json").read_bytes()),new_model_outputs=0)
    (root/"analysis_manifest.json").write_text(json.dumps(analysis,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ["errors","per_case"]}))


if __name__=="__main__":main()
