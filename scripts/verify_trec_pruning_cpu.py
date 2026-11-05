"""Independent CPU map/selection oracle and boundary regression checks."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import torch
from transformers import AutoTokenizer
from trec_pruning_utils import native_header_metadata, random_prefix_scores


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",required=True);args=parser.parse_args()
    root=Path(args.run);assert not (root/"verification_manifest.json").exists()
    code=Path(__file__).read_bytes();(root/"source_verify_trec_pruning_cpu.py").write_bytes(code)
    manifest=dict(status="preparing",source_sha256=sha(code),args=vars(args),start_unix=time.time(),new_model_outputs=0)
    save(root/"verification_manifest.json",manifest)
    try:
        m=json.loads((root/"manifest.json").read_text());assert m["status"]=="complete"
        checks={}
        for name,digest in m["source_sha256"].items():checks["source_"+name]=sha((root/("source_"+name)).read_bytes())==digest
        for name,digest in m["artifact_sha256"].items():checks[name]=sha((root/name).read_bytes())==digest
        for name,digest in m["input_sha256"].items():checks[name]=sha(Path(name).read_bytes())==digest
        assert all(checks.values())
        assert not torch.cuda.is_initialized();torch.set_num_threads(4)
        proposal=json.loads((root/"proposal.json").read_text())
        metadata=json.loads((root/"header_budget_metadata.json").read_text())
        cases=[json.loads(s) for s in Path(proposal["cases_path"]).read_text().splitlines()]
        header=json.loads(Path("configs/trec-context-gate-proposal-v1.json").read_text())["shared_system_header"]
        tokenizer=AutoTokenizer.from_pretrained(m["args"]["tokenizer"],local_files_only=True)
        # Deliberately cut a pretend header in the middle of its first token.
        v=cases[0]["versions"]["with_demos"]
        boundary=native_header_metadata(tokenizer,v["messages"],v["input_ids"],v["prefix_tokens"],header[:1])
        assert boundary["boundary_overlaps"] and any(r["demo_overlap_chars"]>0 for r in boundary["boundary_overlaps"])
        header_end=boundary["header_char_span"][1]
        assert any(b>header_end for a,b in boundary["header_token_offsets"])
        save(root/"artificial_boundary_check.json",dict(purpose="Synthetic shortened header only, not actual dataset header or changed prompts",
             metadata=boundary,boundary_crossing_token_included_and_charged=True))
        checked_heads=oracle_heads=0
        for case,r in zip(cases,metadata):
            assert r["source_key"]==case["source_key"]
            n,budget=r["prefix_tokens"],r["budget"]
            maps=json.loads((root/"synthetic_maps"/(r["source_key"]+".json")).read_text())
            recomputed=native_header_metadata(tokenizer,case["versions"]["with_demos"]["messages"],case["versions"]["with_demos"]["input_ids"],n,header)
            for name in ["header_char_span","header_ids","anchor_ids","required_pinned_ids","boundary_overlaps"]:assert r[name]==recomputed[name]
            for condition in proposal["conditions"]:
                method=condition["method"]
                required=set(r["required_pinned_ids"] if condition["pin_shared_header"] else r["anchor_ids"])
                for layer in range(28):
                    assert len(maps[method][str(layer)])==1 and len(maps[method][str(layer)][0])==4
                    for head in range(4):
                        positions=maps[method][str(layer)][0][head]
                        assert len(positions)==budget and positions==sorted(set(positions))
                        assert min(positions)>=0 and max(positions)<n and required<=set(positions)
                        checked_heads+=1
                # Independent Python sort/required-set oracle at first and last layers.
                for layer in [0,27]:
                    if method.startswith("uniform_random"):
                        scores=random_prefix_scores(n,r["source_key"],layer,4)
                    else:
                        local_seed=int.from_bytes(hashlib.sha256(json.dumps([61423,r["source_key"],layer],separators=(",",":")).encode()).digest()[:8],"big")%(2**63)
                        scores=torch.rand((1,4,n),generator=torch.Generator().manual_seed(local_seed),dtype=torch.float32)
                    for head in range(4):
                        values=scores[0,head].tolist()
                        free=sorted((i for i in range(n) if i not in required),key=lambda i:(-values[i],i))
                        expected=sorted(required|set(free[:budget-len(required)]))
                        assert maps[method][str(layer)][0][head]==expected
                        oracle_heads+=1
        expected=32*4*28*4;assert checked_heads==expected and oracle_heads==32*4*2*4
        prepared=json.loads((root/"prepared_config.json").read_text())
        assert prepared["execution_enabled"] is False and prepared["cpu_synthetic_only"] is True
        assert not torch.cuda.is_initialized()
        result=dict(all_saved_index_maps_checked=checked_heads,independent_python_sort_head_checks=oracle_heads,
                    native_metadata_recomputed_cases=32,artificial_boundary_overlap_included=True,original_input_unchanged=True,
                    new_model_outputs=0,cuda_initialized=False,all_source_input_artifact_hashes_passed=True,
                    prepared_config_sha256=sha((root/"prepared_config.json").read_bytes()))
        save(root/"verification_summary.json",result)
        manifest.update(status="complete",end_unix=time.time(),checks=checks,
                        output_sha256={name:sha((root/name).read_bytes()) for name in ["verification_summary.json","artificial_boundary_check.json"]})
        save(root/"verification_manifest.json",manifest)
        print(json.dumps(result))
    except Exception as error:
        manifest.update(status="failed",end_unix=time.time(),error_type=type(error).__name__,error_message=str(error))
        save(root/"verification_manifest.json",manifest);raise


if __name__=="__main__":main()
