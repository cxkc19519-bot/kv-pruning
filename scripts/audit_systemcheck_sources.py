"""Pinned upstream source and tokenizer audit; no model or upstream imports."""
import argparse
import ast
import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--transport", choices=["raw", "api"], default="raw")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / "manifest.json").exists(), "Do not overwrite a prior run"
    source = Path(__file__).read_bytes()
    (out / "source_audit_systemcheck_sources.py").write_bytes(source)
    manifest = dict(status="preparing", rows=0, new_model_outputs=0, args=vars(args),
                    command=sys.argv, start_unix=time.time(),
                    source_sha256={"audit_systemcheck_sources.py": sha(source)},
                    scope="CPU tokenizer/source audit; no upstream imports, model weights, or generation")
    save(out / "manifest.json", manifest)
    fetched, failures = [], []
    try:
        specs = [
            ("pitfalls", "alexluchen/pitfalls-of-kv-cache-compression", "73079e1b3bf27cd182f680d7da5edd97b660bd82",
             ["README.md", "kvpress/LICENSE", "kv_cache_compression/requirements.txt",
              "kv_cache_compression/benchmarks/ifeval/inputs/sys_ifeval.jsonl",
              "kv_cache_compression/benchmarks/ifeval/dataset_shuffler.py",
              "kv_cache_compression/benchmarks/ifeval/evaluate.py",
              "kv_cache_compression/benchmarks/ifeval/utils/instructions.py",
              "kv_cache_compression/benchmarks/ifeval/utils/instructions_registry.py",
              "kv_cache_compression/benchmarks/ifeval/utils/instructions_util.py",
              "kv_cache_compression/experiments/compressed_context_ifeval.py",
              "kv_cache_compression/experiments/compressed_context_evaluation.py",
              "kv_cache_compression/experiments/utils.py",
              "kv_cache_compression/benchmarks/raccoon/defenses/defense_template.json"]),
            ("systemcheck", "normster/SystemCheck", "ed829f6ac7cd4e09f7161fe7dffbebdd220eb024",
             ["README.md", "LICENSE", "evals/ifeval/inputs/sys_ifeval.jsonl", "evals/ifeval/evaluate.py"]),
        ]
        tasks = []
        for label, repo, rev, paths in specs:
            tree = json.loads((out / (label + "-tree.json")).read_text())
            assert tree["sha"] == rev and not tree.get("truncated", False)
            entries = {x["path"]: x for x in tree["tree"] if x["type"] == "blob"}
            for path in paths:
                entry = entries[path]
                tasks.append((label, repo, rev, path, entry))
        def fetch(task):
            label, repo, rev, path, entry = task
            url = (f"https://raw.githubusercontent.com/{repo}/{rev}/{path}" if args.transport == "raw" else
                   f"https://api.github.com/repos/{repo}/git/blobs/{entry['sha']}")
            payload = urllib.request.urlopen(url, timeout=40).read()
            data = payload if args.transport == "raw" else base64.b64decode(json.loads(payload)["content"])
            blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            assert blob == entry["sha"] and len(data) == entry["size"], path
            dest = out / "upstream" / label / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            rec = dict(repository=repo, revision=rev, path=path, destination=str(dest.relative_to(out)),
                       url=url, bytes=len(data), git_blob_sha1=blob, sha256=sha(data), git_blob_verified=True)
            if path.endswith(".py"):
                tree = ast.parse(data)
                rec["ast_valid"] = True
                rec["imports"] = [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
            return rec
        with ThreadPoolExecutor(max_workers=4) as pool:
            pending = {pool.submit(fetch, task): task for task in tasks}
            for future in as_completed(pending):
                task = pending[future]
                try:
                    fetched.append(future.result())
                except Exception as error:
                    failures.append(dict(path=task[3], repository=task[1], error=repr(error)))
                save(out / "upstream_checks.json", sorted(fetched, key=lambda r: (r["repository"], r["path"])))
                save(out / "fetch_failures.json", failures)
        assert not failures, "Source fetch/check failures retained in fetch_failures.json"
        import torch
        from transformers import AutoTokenizer
        assert not torch.cuda.is_initialized()
        tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True)
        tokenizer_sha = {name: sha((Path(args.tokenizer) / name).read_bytes()) for name in
                         ["config.json", "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"]}
        systemcheck = out / "upstream/systemcheck/evals/ifeval/inputs/sys_ifeval.jsonl"
        pitdata = out / "upstream/pitfalls/kv_cache_compression/benchmarks/ifeval/inputs/sys_ifeval.jsonl"
        google_path = Path("results/20261028-ifeval-cpu-preflight-v1/input_data.jsonl")
        google_bytes = google_path.read_bytes()
        assert sha(google_bytes) == "67ffeee0fcb87c317c5b08a2de85557b4a7e96ada6178aa645b4954fe4b53d49"
        google = {r["key"]: r for r in map(json.loads, google_bytes.decode().splitlines())}
        tables = {}
        prepend = "You are a helpful assistant. If you receive a valid user request, please respond while adhering to the following guidelines:\n\n"
        defenses = json.loads((out / "upstream/pitfalls/kv_cache_compression/benchmarks/raccoon/defenses/defense_template.json").read_text())
        save(out / "defense_keys.json", list(defenses))
        for label, path in [("systemcheck", systemcheck), ("pitfalls", pitdata)]:
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            assert len({r["key"] for r in rows}) == len(rows)
            table = []
            for row in rows:
                messages = row["messages"]
                assert [m["role"] for m in messages] == ["system", "user"]
                assert len(row["instruction_id_list"]) == len(row["kwargs"])
                counts = {}
                for name, sys_content in [("unwrapped", messages[0]["content"]),
                                          ("default_prepend_only", prepend + messages[0]["content"])]:
                    changed = [{"role": "system", "content": sys_content}, messages[1]]
                    prefix = tokenizer.apply_chat_template(changed[:1], tokenize=True, add_generation_prompt=False)
                    full = tokenizer.apply_chat_template(changed, tokenize=True, add_generation_prompt=True)
                    assert full[:len(prefix)] == prefix and len(full) > len(prefix)
                    counts[name] = dict(prefix_tokens=len(prefix), suffix_tokens=len(full)-len(prefix),
                                        length_256_2048=256 <= len(prefix) <= 2048,
                                        anchors=min(len(prefix), 68), budget_50=len(prefix)//2,
                                        prefix_ids_sha256=sha(json.dumps(prefix, separators=(",", ":")).encode()))
                original = google.get(row["key"])
                table.append(dict(key=row["key"], counts=counts, instruction_count=len(row["instruction_id_list"]),
                                  ids_kwargs_equal_google=bool(original and all(row[k] == original[k] for k in ["instruction_id_list", "kwargs"])),
                                  prompt_equal_google=bool(original and row["prompt"] == original["prompt"]),
                                  system_chars=len(messages[0]["content"]), user_chars=len(messages[1]["content"])))
            save(out / (label + "_token_audit.json"), table)
            tables[label] = dict(rows=len(rows), key_set_equal_google={r["key"] for r in rows} == set(google),
                                 ids_kwargs_equal_google=sum(r["ids_kwargs_equal_google"] for r in table),
                                 prompt_equal_google=sum(r["prompt_equal_google"] for r in table),
                                 variants={})
            for variant in ["unwrapped", "default_prepend_only"]:
                lengths = sorted(r["counts"][variant]["prefix_tokens"] for r in table)
                tables[label]["variants"][variant] = dict(min=lengths[0], median=lengths[len(lengths)//2],
                    p90_nearest_rank=lengths[(9*len(lengths)+9)//10-1], max=lengths[-1],
                    count_256_2048=sum(256 <= n <= 2048 for n in lengths),
                    count_50_budget_below_68=sum(n//2 < min(n,68) for n in lengths))
        pitrows = {r["key"]: r for r in map(json.loads, pitdata.read_text().splitlines())}
        sysrows = {r["key"]: r for r in map(json.loads, systemcheck.read_text().splitlines())}
        comparison = {field:sum(k in sysrows and pitrows[k].get(field)==sysrows[k].get(field) for k in pitrows)
                      for field in ["messages", "prompt", "instruction_id_list", "kwargs"]}
        assert not torch.cuda.is_initialized()
        summary = dict(datasets=tables, pitfalls_equal_systemcheck_by_key=comparison,
                       sources=len(fetched), python_ast_checked=sum(r.get("ast_valid",False) for r in fetched),
                       all_blobs_verified=True, upstream_code_executed=False, new_model_outputs=0,
                       cuda_initialized=False, scope="Source/length feasibility only, no scorer/quality/cache correctness validation",
                       note="Variants are source-audit descriptions, not a new sample-selection registration. No prompt padding or old proposal changes.")
        save(out / "summary.json", summary)
        save(out / "tokenizer_sha256.json", tokenizer_sha)
        manifest.update(status="complete", end_unix=time.time(), upstream_files=len(fetched),
                        input_sha256={str(google_path):sha(google_bytes), **{str(out/(n+"-tree.json")):sha((out/(n+"-tree.json")).read_bytes()) for n in ["pitfalls","systemcheck"]}},
                        tokenizer_sha256=tokenizer_sha,
                        artifact_sha256={name:sha((out/name).read_bytes()) for name in ["summary.json", "upstream_checks.json", "tokenizer_sha256.json", "systemcheck_token_audit.json", "pitfalls_token_audit.json"]})
        save(out / "manifest.json", manifest)
        print(json.dumps(summary, ensure_ascii=False))
    except Exception as error:
        manifest.update(status="failed", end_unix=time.time(), error_type=type(error).__name__, error_message=str(error))
        save(out / "manifest.json", manifest)
        raise


if __name__ == "__main__":
    main()
