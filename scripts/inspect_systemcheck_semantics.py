"""Supplement a completed source audit, retaining a separate analysis manifest."""
import argparse
import ast
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import time
import urllib.request


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--tokenizer", required=True)
    args = parser.parse_args()
    root = Path(args.run)
    assert json.loads((root / "manifest.json").read_text())["status"] == "complete"
    out = root / "semantics"
    out.mkdir(exist_ok=False)
    source = Path(__file__).read_bytes()
    (out / "source_inspect_systemcheck_semantics.py").write_bytes(source)
    manifest = dict(status="preparing", args=vars(args), start_unix=time.time(), new_model_outputs=0,
                    source_sha256=sha(source), scope="CPU source/text/token audit; no upstream module imports or model weights")
    save(out / "analysis_manifest.json", manifest)
    checks = []
    try:
        specs = [("longbench", "THUDM/LongBench", "2e00731f8d0bff23dc4325161044d0ed8af94c1e",
                  ["LongBench/README.md", "LongBench/LICENSE", "LongBench/config/dataset2prompt.json",
                   "LongBench/metrics.py", "LongBench/eval.py", "LongBench/pred.py"]),
                 ("systemcheck", "normster/SystemCheck", "ed829f6ac7cd4e09f7161fe7dffbebdd220eb024",
                  ["evals/EVALS.md", "evals/convert.sh"])]
        tasks = []
        for label, repo, rev, paths in specs:
            tree = json.loads((root / (label + "-tree.json")).read_text())
            assert tree["sha"] == rev
            entries = {r["path"]:r for r in tree["tree"] if r["type"] == "blob"}
            for path in paths:
                tasks.append((label, repo, rev, path, entries[path]))
        def fetch(task):
            label, repo, rev, path, entry = task
            url = f"https://api.github.com/repos/{repo}/git/blobs/{entry['sha']}"
            payload = json.loads(urllib.request.urlopen(url, timeout=20).read())
            data = base64.b64decode(payload["content"])
            assert hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == entry["sha"]
            assert len(data) == entry["size"]
            dest = out / "upstream" / label / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            if path.endswith(".py"):
                ast.parse(data)
            return dict(repository=repo, revision=rev, path=path, destination=str(dest.relative_to(out)),
                        bytes=len(data), sha256=sha(data), git_blob_sha1=entry["sha"], git_blob_verified=True,
                        ast_valid=path.endswith(".py"))
        with ThreadPoolExecutor(max_workers=4) as pool:
            for result in pool.map(fetch, tasks):
                checks.append(result)
                save(out / "upstream_checks.json", checks)
        def rows(path):
            return {r["key"]:r for r in map(json.loads, path.read_text().splitlines())}
        google_path = Path("results/20261028-ifeval-cpu-preflight-v1/input_data.jsonl")
        google = rows(google_path)
        sysdata = root / "upstream/systemcheck/evals/ifeval/inputs/sys_ifeval.jsonl"
        pitdata = root / "upstream/pitfalls/kv_cache_compression/benchmarks/ifeval/inputs/sys_ifeval.jsonl"
        systemcheck, pitfalls = rows(sysdata), rows(pitdata)
        differences = dict(missing_pitfalls_keys=sorted(set(google)-set(pitfalls)), changed_systemcheck={})
        for key in google:
            changes = {field:dict(google=google[key].get(field), systemcheck=systemcheck[key].get(field))
                       for field in ["prompt", "instruction_id_list", "kwargs"] if google[key].get(field) != systemcheck[key].get(field)}
            if changes:
                differences["changed_systemcheck"][key] = changes
        save(out / "annotation_differences.json", differences)
        import torch
        from transformers import AutoTokenizer
        assert not torch.cuda.is_initialized()
        tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True)
        prepend = "You are a helpful assistant. If you receive a valid user request, please respond while adhering to the following guidelines:\n\n"
        defense_path = root / "upstream/pitfalls/kv_cache_compression/benchmarks/raccoon/defenses/defense_template.json"
        defense = json.loads(defense_path.read_text())["standard_defense"]
        table = []
        for key, row in pitfalls.items():
            content = defense.replace("$system_prompt", prepend + row["messages"][0]["content"])
            messages = [{"role":"system", "content":content}, row["messages"][1]]
            pre = tokenizer.apply_chat_template(messages[:1], tokenize=True, add_generation_prompt=False)
            full = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
            assert full[:len(pre)] == pre
            table.append(dict(key=key, prefix_tokens=len(pre), suffix_tokens=len(full)-len(pre),
                              prefix_ids_sha256=sha(json.dumps(pre,separators=(",", ":")).encode())))
        save(out / "standard_defense_lengths.json", table)
        lengths = sorted(r["prefix_tokens"] for r in table)
        prompt_file = out / "upstream/longbench/LongBench/config/dataset2prompt.json"
        trec_prompt = json.loads(prompt_file.read_text())["trec"]
        metrics_file = out / "upstream/longbench/LongBench/metrics.py"
        metrics_source = metrics_file.read_text()
        classifier = next(n for n in ast.parse(metrics_source).body if isinstance(n,ast.FunctionDef) and n.name == "classification_score")
        eval_file = out / "upstream/longbench/LongBench/eval.py"
        pred_file = out / "upstream/longbench/LongBench/pred.py"
        excerpts = dict(trec_prompt=trec_prompt, classification_score=ast.get_source_segment(metrics_source,classifier),
                        eval_lines=[dict(line=i+1,text=t) for i,t in enumerate(eval_file.read_text().splitlines()) if any(s in t for s in ["trec", "split", "strip", "dataset2metric"])],
                        prediction_lines=[dict(line=i+1,text=t) for i,t in enumerate(pred_file.read_text().splitlines()) if any(s in t for s in ["trec", "max_length", "tokenized_prompt", "load_dataset", "build_chat"])])
        save(out / "longbench_scoring_excerpts.json",excerpts)
        summary = dict(upstream_files=len(checks), python_ast_checked=sum(r["ast_valid"] for r in checks),
                       standard_defense_plus_prepend=dict(rows=len(table),min=lengths[0],median=lengths[len(lengths)//2],max=lengths[-1],
                                                          count_256_2048=sum(256<=v<=2048 for v in lengths)),
                       annotations=differences, new_model_outputs=0, cuda_initialized=torch.cuda.is_initialized(),
                       longbench_data_downloaded=False, longbench_ids_frozen=False,
                       note="Author README declares CC BY4.0; SystemCheck has MIT; vendored Google files retain Apache headers. Keep each source notice. No complete third-party reproduction.")
        assert not torch.cuda.is_initialized()
        save(out / "summary.json", summary)
        manifest.update(status="complete",end_unix=time.time(),
                        input_sha256={str(p):sha(p.read_bytes()) for p in [google_path,sysdata,pitdata,defense_path]},
                        artifact_sha256={str(p.relative_to(out)):sha(p.read_bytes()) for p in out.rglob("*") if p.is_file() and p.name != "analysis_manifest.json"})
        save(out / "analysis_manifest.json", manifest)
        print(json.dumps(summary,ensure_ascii=False))
        print(json.dumps(excerpts,ensure_ascii=False))
    except Exception as error:
        manifest.update(status="failed",end_unix=time.time(),error_type=type(error).__name__,error_message=str(error))
        save(out / "analysis_manifest.json", manifest)
        raise


if __name__ == "__main__":
    main()
