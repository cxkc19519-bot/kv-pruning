"""CPU-only native-token feasibility gate; never loads a language model.

The pinned proposal is an input, not edited to accommodate the observed lengths.
Official scoring is deliberately not run when its prerequisite count fails.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / "manifest.json").exists(), "Never overwrite a prior run"
    source = Path(__file__).read_bytes()
    (out / "source_audit_ifeval_feasibility.py").write_bytes(source)
    manifest = dict(status="preparing", start_unix=time.time(), args=vars(args),
                    command=sys.argv, rows=0, new_model_outputs=0,
                    source_sha256={"audit_ifeval_feasibility.py": digest(source)},
                    scope="CPU tokenizer and source audit only; no model weights, generation, or upstream scorer execution")
    save(out / "manifest.json", manifest)
    try:
        data = Path(args.data).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        assert blob == "cbe52f6eecf3986fdac745b4acba4da1408eb146"
        proposal_bytes = Path(args.proposal).read_bytes()
        assert digest(proposal_bytes) == "ecca3b4e26f686496ffceb9918438d5115fb7b879936f12392ff0aa0fea3eb50"
        proposal = json.loads(proposal_bytes)
        assert proposal["execution_enabled"] is False
        (out / "proposal.json").write_bytes(proposal_bytes)
        rows = [json.loads(line) for line in data.decode("utf-8").splitlines()]
        assert len(rows) == 541 and len({r["key"] for r in rows}) == 541
        import torch
        from transformers import AutoTokenizer

        assert not torch.cuda.is_initialized()
        tokenizer_dir = Path(args.tokenizer)
        names = ["config.json", "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"]
        tokenizer_sha = {name: digest((tokenizer_dir / name).read_bytes()) for name in names}
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir, local_files_only=True)
        model_config = json.loads((tokenizer_dir / "config.json").read_text())
        assert model_config["model_type"] == "qwen2" and not model_config.get("use_sliding_window", False)
        assert not model_config.get("sliding_window") or not model_config.get("use_sliding_window", False)
        limits = proposal["selection"]
        candidates = []
        for row in rows:
            assert isinstance(row["key"], int) and isinstance(row["prompt"], str)
            assert len(row["instruction_id_list"]) == len(row["kwargs"]) > 0
            assert all(isinstance(v, dict) for v in row["kwargs"])
            messages = [{"role": "user", "content": row["prompt"]}]
            prefix = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False)
            full = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
            assert full[:len(prefix)] == prefix and len(full) > len(prefix)
            suffix = full[len(prefix):]
            assert tokenizer.decode(suffix) == "<|im_start|>assistant\n"
            n = len(prefix)
            length_ok = limits["min_native_prefix_tokens"] <= n <= limits["max_native_prefix_tokens"]
            budgets = {str(r): int(n * r) for r in [0.75, 0.5]}
            anchors = len(set(range(min(4, n))) | set(range(max(0, n - 64), n)))
            if length_ok:
                assert all(v >= anchors for v in budgets.values())
            candidates.append(dict(key=row["key"], prefix_tokens=n, suffix_tokens=len(suffix),
                                   prompt_sha256=digest(row["prompt"].encode()),
                                   prefix_ids_sha256=digest(json.dumps(prefix, separators=(",", ":")).encode()),
                                   instruction_ids=row["instruction_id_list"], length_eligible=length_ok,
                                   exclusion_reason=None if length_ok else "native_prefix_outside_preregistered_range",
                                   order_sha256=digest(("20261028:" + str(row["key"])).encode()),
                                   anchor_count=anchors, per_head_slot_budgets=budgets))
        candidates.sort(key=lambda r: r["order_sha256"])
        eligible = [r for r in candidates if r["length_eligible"]]
        lengths = sorted(r["prefix_tokens"] for r in candidates)
        count = len(eligible)
        stopped = count < limits["count"]
        assert stopped, "This audit only closes the insufficient-count branch; checker/selector preflight is still required otherwise"
        save(out / "candidates.json", candidates)
        prior_path = out / "token-length-audit.json"
        if prior_path.exists():
            prior = json.loads(prior_path.read_text())
            assert [(r["key"], r["prefix_tokens"], r["suffix_tokens"], r["length_eligible"]) for r in prior] == [
                (r["key"], r["prefix_tokens"], r["suffix_tokens"], r["length_eligible"]) for r in candidates]
        assert not torch.cuda.is_initialized()
        summary = dict(source_rows=len(rows), unique_keys=len(rows),
                       source_data_sha256=digest(data), git_blob_sha1=blob,
                       source_revision=proposal["dataset_revision"], length_eligible=count,
                       required_count=limits["count"], excluded_length=len(rows)-count,
                       eligible_keys=[r["key"] for r in eligible], frozen_execution_keys=None,
                       prefix_tokens=dict(min=lengths[0], median=lengths[len(lengths)//2],
                                          p90_nearest_rank=lengths[(9*len(lengths)+9)//10-1], max=lengths[-1]),
                       suffix_token_counts=dict(Counter(r["suffix_tokens"] for r in candidates)),
                       native_split_checks=len(candidates), native_default_system_segment=tokenizer.decode(
                           tokenizer.apply_chat_template([{"role":"user", "content":"x"}], tokenize=True,
                                                         add_generation_prompt=False)).split("<|im_end|>", 1)[0],
                       model_config_layers=model_config["num_hidden_layers"],
                       engineering_gate_passed=False, gpu_inference_eligible=False,
                       checker="not_run_length_stop", random_selector="not_implemented_length_stop",
                       model_generation="not_run_length_stop", new_model_outputs=0,
                       cuda_initialized=torch.cuda.is_initialized(),
                       decision="Stop the original proposal before inference; no padding, threshold changes, reseeding, or replacements")
        save(out / "summary.json", summary)
        save(out / "tokenizer_sha256.json", tokenizer_sha)
        manifest.update(status="stopped_insufficient_length_eligible", end_unix=time.time(),
                        input_sha256={str(Path(args.data)): digest(data), str(Path(args.proposal)): digest(proposal_bytes)},
                        tokenizer_sha256=tokenizer_sha, engineering_gate_passed=False,
                        artifacts_sha256={name:digest((out/name).read_bytes()) for name in
                                          ["candidates.json", "summary.json", "tokenizer_sha256.json", "proposal.json"]})
        save(out / "manifest.json", manifest)
        print(json.dumps(summary, ensure_ascii=False))
    except Exception as error:
        manifest.update(status="failed", end_unix=time.time(), error_type=type(error).__name__, error_message=str(error))
        save(out / "manifest.json", manifest)
        raise


if __name__ == "__main__":
    main()
