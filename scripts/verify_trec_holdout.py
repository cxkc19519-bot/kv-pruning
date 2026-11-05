"""Independent CPU verification of the ten-ID recheck freeze and prior-output scan."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import torch
from transformers import AutoTokenizer


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",required=True);args=parser.parse_args()
    root=Path(args.run);assert not (root/"verification_manifest.json").exists()
    source=Path(__file__).read_bytes();(root/"source_verify_trec_holdout.py").write_bytes(source)
    manifest=dict(status="preparing",source_sha256=sha(source),new_model_outputs=0,args=vars(args),start_unix=time.time())
    save(root/"verification_manifest.json",manifest)
    try:
        m=json.loads((root/"manifest.json").read_text());f=json.loads((root/"finalization_manifest.json").read_text())
        assert m["status"]==f["status"]=="complete"
        checks={}
        for name,d in m["source_sha256"].items():checks["source_"+name]=sha((root/("source_"+name)).read_bytes())==d
        for name,d in m["input_sha256"].items():checks[name]=sha(Path(name).read_bytes())==d
        for name,d in m["artifact_sha256"].items():checks[name]=sha((root/name).read_bytes())==d
        for name,d in f["input_sha256"].items():checks[name]=sha(Path(name).read_bytes())==d
        for name,d in f["output_sha256"].items():checks[name]=sha((root/name).read_bytes())==d
        checks["source_freeze_trec_holdout.py"]=sha((root/"source_freeze_trec_holdout.py").read_bytes())==f["source_sha256"]
        assert all(checks.values())
        assert not torch.cuda.is_initialized()
        cfg=json.loads((root/"proposal.json").read_text());cases=[json.loads(s) for s in (root/"cases.jsonl").read_text().splitlines()]
        meta=json.loads((root/"header_budget_metadata.json").read_text());keys=[r["source_key"] for r in cases]
        assert keys==cfg["frozen_source_keys"] and len(set(keys))==10 and not cfg["execution_enabled"]
        original_lines=Path("results/20261028-trec-data-preflight-v2/data/trec.jsonl").read_bytes().splitlines()
        tokenizer=AutoTokenizer.from_pretrained(m["args"]["tokenizer"],local_files_only=True)
        for name,d in cfg["tokenizer_sha256"].items():assert sha((Path(m["args"]["tokenizer"])/name).read_bytes())==d
        for case,metadata in zip(cases,meta):
            raw=original_lines[case["source_line_0based"]];original=json.loads(raw)
            assert sha(raw)==case["raw_line_sha256"] and original["_id"]==case["source_key"]==metadata["source_key"]
            assert case["gold"]==original["answers"][0]
            v=case["versions"]["with_demos"]
            assert v["messages"][0]["content"]==cfg["shared_system_header"]+original["context"]
            assert v["messages"][1]["content"]==original["input"]
            native=tokenizer.apply_chat_template(v["messages"],tokenize=True,add_generation_prompt=True)
            prefix=tokenizer.apply_chat_template(v["messages"][:1],tokenize=True,add_generation_prompt=False)
            assert native==v["input_ids"] and prefix==metadata["prefix_ids"] and len(prefix)==v["prefix_tokens"]
            assert sha(json.dumps(native,separators=(",",":")).encode())==v["input_ids_sha256"]
            assert metadata["budget"]==len(prefix)//2 and metadata["required_pinned_count"]<=metadata["budget"]
        scan=[]
        for path in sorted(Path("results").glob("*/generations.jsonl")):
            digest=hashlib.sha256();count=0;overlap=[]
            with path.open("rb") as stream:
                for line in stream:
                    digest.update(line);count+=1
                    row=json.loads(line)
                    if row.get("source_key") in keys:overlap.append(row["source_key"])
            assert not overlap
            scan.append(dict(path=str(path),sha256=digest.hexdigest(),rows=count,new_id_overlap=overlap))
        save(root/"previous_output_scan.json",scan)
        assert cfg["n_cases"]==10 and cfg["max_main_outputs"]==50 and cfg["max_extra_correctness_outputs"]==24
        assert len(cfg["conditions"])==5 and cfg["full_support_gate"]["required_label_format_correct"]==10
        assert cfg["full_support_gate"]["min_whole_response_exact_correct"]==5
        assert cfg["full_support_gate"]["max_truncated"]==cfg["full_support_gate"]["max_errors"]==0
        assert not torch.cuda.is_initialized()
        summary=dict(cases_reencoded=10,original_queries_context_and_gold_preserved=10,prior_output_files_checked=len(scan),
                     prior_main_rows_scanned=sum(r["rows"] for r in scan),prior_output_id_overlap=0,
                     proposal_sha256=sha((root/"proposal.json").read_bytes()),all_hash_checks_passed=True,
                     execution_enabled=False,new_model_outputs=0,cuda_initialized=False)
        save(root/"verification_summary.json",summary)
        manifest.update(status="complete",end_unix=time.time(),checks=checks,
                        output_sha256={name:sha((root/name).read_bytes()) for name in ["verification_summary.json","previous_output_scan.json"]})
        save(root/"verification_manifest.json",manifest);print(json.dumps(summary))
    except Exception as error:
        manifest.update(status="failed",end_unix=time.time(),error_type=type(error).__name__,error_message=str(error));save(root/"verification_manifest.json",manifest);raise


if __name__=="__main__":main()
