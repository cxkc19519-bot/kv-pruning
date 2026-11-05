"""CPU-only pairing of header protection interventions on the full frozen cohort."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",required=True);args=parser.parse_args()
    root=Path(args.run);assert not (root/"header_tradeoff_manifest.json").exists()
    source=Path(__file__).read_bytes();(root/"source_trec_header_tradeoffs.py").write_bytes(source)
    assert json.loads((root/"manifest.json").read_text())["status"]=="complete"
    cases={r["source_key"]:r for r in map(json.loads,(root/"cases.jsonl").read_text().splitlines())}
    rows=[json.loads(s) for s in (root/"generations.jsonl").read_text().splitlines()]
    base={r["source_key"]:r for r in json.loads((root/"baseline_with_demos.json").read_text())}
    by={(r["source_key"],r["method"]):r for r in rows}
    interventions={}
    for family in ["adapted_snapkv_shared_anchors","uniform_random_shared_anchors"]:
        transitions=Counter();formats=Counter();changed=[]
        for key in cases:
            a=by[key,family];b=by[key,family+"_header_pinned"]
            state=("C" if a["metrics"]["exact_correct"] else "W")+"2"+("C" if b["metrics"]["exact_correct"] else "W")
            transitions[state]+=1
            fmt=("valid" if a["metrics"]["whole_response_label_format"] else "invalid")+"2"+("valid" if b["metrics"]["whole_response_label_format"] else "invalid")
            formats[fmt]+=1
            if a["ids"]!=b["ids"]:changed.append(dict(source_key=key,before=a["text"],after=b["text"],exact_transition=state))
        interventions[family]=dict(exact_transitions={s:transitions[s] for s in ["C2C","C2W","W2C","W2W"]},
            format_transitions={s:formats[s] for s in ["valid2valid","valid2invalid","invalid2valid","invalid2invalid"]},
            changed_token_outputs=changed)
    bad=[]
    for r in rows:
        if not r["metrics"]["whole_response_label_format"]:
            key=r["source_key"];pinned=by[key,r["method"]+"_header_pinned"]
            bad.append(dict(source_key=key,user_query=cases[key]["versions"]["with_demos"]["messages"][1]["content"],
                gold=r["gold"],full_prediction=base[key]["text"],full_exact=base[key]["metrics"]["exact_correct"],
                method=r["method"],without_protection=r["text"],with_protection=pinned["text"],
                protected_format=pinned["metrics"]["whole_response_label_format"],protected_exact=pinned["metrics"]["exact_correct"]))
    eligible_path=Path("results/20261028-trec-context-gate-data-v1/eligibility.json")
    eligible=json.loads(eligible_path.read_text())
    remaining=[key for key in eligible["eligible"] if key not in cases]
    result=dict(header_interventions=interventions,invalid_label_outputs=bad,invalid_output_count=len(bad),
                invalid_source_count=len({r["source_key"] for r in bad}),
                invalid_outputs_on_full_exact_correct=sum(r["full_exact"] for r in bad),
                remaining_same_length_eligible_keys=remaining,remaining_count=len(remaining),
                interpretation="Header protection restored exact label-format on the observed invalid outputs but did not correct their classification labels. Equal-budget reallocation can also lose previous correct predictions; no guaranteed method improvement or safety claim.",
                confirmation_status="Remaining10 source keys are candidates only, not an enabled/frozen confirmation experiment; shared demonstration overlap and gold ambiguity require review.")
    output=root/"header_tradeoffs.json";output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    manifest=dict(status="complete",source_sha256=sha(source),new_model_outputs=0,
                  input_sha256={str(p):sha(p.read_bytes()) for p in [root/"manifest.json",root/"cases.jsonl",root/"generations.jsonl",root/"baseline_with_demos.json",eligible_path]},output_sha256=sha(output.read_bytes()))
    (root/"header_tradeoff_manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps(dict(invalid_output_count=len(bad),invalid_source_count=result["invalid_source_count"],invalid_outputs_on_full_exact_correct=result["invalid_outputs_on_full_exact_correct"],remaining_count=len(remaining),
                         interventions={k:{a:b for a,b in v.items() if a!="changed_token_outputs"} for k,v in interventions.items()})))


if __name__=="__main__":main()
