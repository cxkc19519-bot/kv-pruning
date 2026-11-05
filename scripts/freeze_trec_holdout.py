"""Complete per-ID review and freeze a disabled ten-question recheck proposal."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",required=True);parser.add_argument("--review",required=True);args=parser.parse_args()
    root=Path(args.run);assert not (root/"finalization_manifest.json").exists()
    code=Path(__file__).read_bytes();(root/"source_freeze_trec_holdout.py").write_bytes(code)
    final=dict(status="preparing",source_sha256=sha(code),args=vars(args),start_unix=time.time(),new_model_outputs=0)
    save(root/"finalization_manifest.json",final)
    try:
        audit_bytes=(root/"manifest.json").read_bytes();audit=json.loads(audit_bytes)
        assert audit["status"]=="complete_pending_semantic_review"
        (root/"audit_manifest_before_review.json").write_bytes(audit_bytes)
        checked={}
        for name,digest in audit["artifact_sha256"].items():checked[name]=sha((root/name).read_bytes())==digest
        for name,digest in audit["input_sha256"].items():checked[name]=sha(Path(name).read_bytes())==digest
        for name,digest in audit["source_sha256"].items():checked["source_"+name]=sha((root/("source_"+name)).read_bytes())==digest
        assert all(checked.values())
        review_bytes=Path(args.review).read_bytes();review=json.loads(review_bytes)
        cases=[json.loads(s) for s in (root/"cases.jsonl").read_text().splitlines()]
        keys=[c["source_key"] for c in cases]
        entries=review["entries"]
        assert [r["source_key"] for r in entries]==keys and len(entries)==10 and all(r["retain"] for r in entries)
        provenance=json.loads((root/"original_label_provenance.json").read_text())
        assert sha((root/"upstream/TREC_10.label").read_bytes())==review["source_test_sha256"]
        assert sha((root/"upstream/taxonomy.html").read_bytes())==review["source_taxonomy_sha256"]
        for row,case,original in zip(entries,cases,provenance):
            assert row["gold"]==case["gold"]==original["longbench_gold"]
            assert row["original_code"]==original["original_code"] and row["source_line_0based"]==original["original_test_line"]
        (root/"label_review.json").write_bytes(review_bytes)
        # Check experimental output IDs across existing main generation files, not metadata views.
        previous_output_files=[];previous_source_keys=set()
        for file in sorted(Path("results").glob("*/generations.jsonl")):
            previous_output_files.append(str(file))
            for line in file.open(encoding="utf-8"):
                obj=json.loads(line)
                if obj.get("source_key"):previous_source_keys.add(obj["source_key"])
        assert not set(keys)&previous_source_keys
        parent_path=Path("configs/trec-pruning-calibration-proposal-v1.json")
        parent_bytes=parent_path.read_bytes();assert sha(parent_bytes)=="289bb122e62788cff3406df9ba42a792172b2f10959144be187271e52634093f"
        parent=json.loads(parent_bytes)
        frontend_path=Path("configs/trec-context-gate-proposal-v1.json")
        frontend=json.loads(frontend_path.read_text())
        summary=json.loads((root/"summary.json").read_text())
        flagged=[r["source_key"] for r in entries if r["flags"]]
        config=dict(status="cpu_frozen_pending_bounded_ten_case_runner",execution_enabled=False,
            purpose="Single held-out-question recheck of classification versus exact-label-format retention; not an independent dataset, safety benchmark or novel method",
            model=parent["model"],model_revision=parent["model_revision"],dataset_id="zai-org/LongBench",
            dataset_revision="5e628be450b7e67fb7ae6e201bd6d8f7056f7672",trec_data_sha256="20a88e14f7442f58a39082cdd7396f1093ea8162da0a4ea7ead7d6757514c8f4",
            parent_pruning_proposal_sha256=sha(parent_bytes),development_cases_sha256="e709d4bd298cd61a272f42835a180c7ac032b450b0aa1c40892814c7f6c8caf7",
            cases_path=str(root/"cases.jsonl"),cases_sha256=sha((root/"cases.jsonl").read_bytes()),frozen_source_keys=keys,n_cases=10,
            header_metadata_path=str(root/"header_budget_metadata.json"),header_metadata_sha256=sha((root/"header_budget_metadata.json").read_bytes()),
            label_review_path=args.review,label_review_sha256=sha(review_bytes),review_flagged_keys=flagged,
            source_selection="All10 remaining from the original42 eligible after original32 development IDs, original hash order. No extra length band, seed change, padding, rewriting, relabeling, exclusions after review or replacement by model results",
            frontend="Same exact shared50-label header plus unchanged original demonstrations in system, original query in user; no NoDemo condition and no truncation",
            shared_system_header=frontend["shared_system_header"],query_blind=True,
            tokenizer_sha256=json.loads((root/"tokenizer_sha256.json").read_text()),conditions=[dict(method="full",keep=1.0,pin_shared_header=False)]+parent["conditions"],
            budget=parent["budget"],adapted_snapkv=parent["adapted_snapkv"],random=parent["random"],decode=parent["decode"],
            source_hashes=dict(pilot="476b3cbf8a9e16cdbb958286ba931a45d9b089f1bba4fb0a29f3a7ee9ebcdc1f",selector="92594811de726c585087fe1356a81cfcbe3a19a1fd6bb68a7e8781a334c53918",development_runner="7b9393babbcf28293d51fdd43c7a80ed41810d614001811b6c458c55d3c84412"),
            stages=["First3 new cases: Full native/nohook/hook/100%-gather checks, at most12 extra outputs; no compressed outputs yet",
                    "Generate all10 new Full main outputs, freeze baseline IDs and scores",
                    "If Full gate passes, first3 new cases compressed native/custom reference checks for two representative methods, at most12 further extra outputs",
                    "If engineering passes, generate all original10 cases for all4 compressed conditions, including Full-wrong cases; no adaptive method selection"],
            full_support_gate=dict(required_full_outputs=10,min_whole_response_exact_correct=5,required_label_format_correct=10,max_truncated=0,max_errors=0,
                on_failure="Stop before any compressed reference/main outputs; preserve all10 Full and mark other40 not_run_full_support_gate. Do not alter prompts/models/budgets/IDs",
                meaning="Descriptive minimum support and clean format baseline only, not a statistical power calculation; same50% exact-support fraction as development gate, not an AccessDenied exception"),
            max_main_outputs=50,max_extra_correctness_outputs=24,
            primary_endpoint="For all10 fixed queries, count Full-format-valid to compressed-format-invalid outputs separately for each method; complete raw-response label inventory membership",
            secondary_endpoints=["original-gold exact and official compatibility","Full-to-compressed exact C2C/C2W/W2C/W2W with all10 and actual Full-correct denominator","pin-versus-unpinned format and exact transitions for each method","truncation/errors/N/A","all-case results plus descriptive flagged-case listing; never drop flagged cases"],
            scorer="Same prior whole response.strip() label-format and exact-gold scoring. Remove only terminal EOS token; do not first-line-filter primary scores or hide other special tokens. Official firstline compatibility remains secondary",
            reporting_constraints="No method winner or significance claim from n10, no stable family ranking, no combination with development as an independently confirmed sample. Zero format failures or improvements are valid outcomes; do not run more seeds/budgets to induce failures",
            overlap=summary["limitation"],development_demo_overlap_fraction_range=summary["demo_overlap_fraction_range"],
            engineering_gates=["all sources/cases/header/tokenizer SHA match and new IDs never in previous experimental main outputs", "all10 native IDs, source question/context/gold bytes and fixed budget assertions pass",
                "first3 Full native/nohook/hook and every-policy100% gather agree", "Full gate frozen before compressed reference outputs", "first3 compressed physical-cache/original-RoPE trajectories and HF reference/custom IDs agree",
                "all4 methods every case/layer/head exact equal bytes, anchors/header charged, actual score/maps saved; snapshot enabled only after checks"],
            on_runner_failure="Preserve bounded partial outputs and manifests, mark remaining cells not_run_engineering_gate; do not silently fallback or retry model outcomes",
            after_single_recheck="Stop this calibration round and synthesize development+holdout separately. Do not automatically expand cases, methods, budgets or models",
            runner_warning="Existing development runner is hardcoded to32 and baseline19. Requires a new bounded10-case stage-aware adapter; do not merely disable its cohort/budget assertions",
            old_gates="No changes to stopped native IFEval or failed AccessDenied gates")
        save(root/"proposal.json",config)
        results=dict(reviewed_cases=10,original_labels_preserved=10,review_flagged_cases=len(flagged),all_candidates_retained=True,
            previous_main_generation_files_checked=len(previous_output_files),previous_output_id_overlap=0,
            full_gate_before_compression=config["full_support_gate"],max_main_outputs=50,max_extra_outputs=24,
            cases_sha256=config["cases_sha256"],proposal_sha256=sha((root/"proposal.json").read_bytes()),execution_enabled=False,new_model_outputs=0)
        save(root/"review_finalization_summary.json",results)
        final.update(status="complete",end_unix=time.time(),checks=checked,
            input_sha256={str(p):sha(p.read_bytes()) for p in [root/"audit_manifest_before_review.json",Path(args.review),parent_path,frontend_path]},
            output_sha256={name:sha((root/name).read_bytes()) for name in ["label_review.json","proposal.json","review_finalization_summary.json"]})
        save(root/"finalization_manifest.json",final)
        audit.update(status="complete",semantic_review_complete=True,review_flags_retained=len(flagged),finalization_manifest="finalization_manifest.json",proposal_sha256=results["proposal_sha256"])
        save(root/"manifest.json",audit)
        print(json.dumps(results))
    except Exception as error:
        final.update(status="failed",end_unix=time.time(),error_type=type(error).__name__,error_message=str(error));save(root/"finalization_manifest.json",final);raise


if __name__=="__main__":main()
