"""CPU-only audit of frozen LongBench TREC bytes and an explicit Qwen role adaptation."""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import zipfile


REVISION = "5e628be450b7e67fb7ae6e201bd6d8f7056f7672"
ZIP_SHA = "cb45b11a4133c6bc1d6a44b0f8e701335ff1e543195db1103472e575857f7f64"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def stats(values):
    v = sorted(values)
    return dict(min=v[0], median=v[len(v)//2], p90_nearest_rank=v[(9*len(v)+9)//10-1], max=v[-1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--upstream", required=True)
    args = parser.parse_args()
    root = Path(args.run)
    prior = json.loads((root / "manifest.json").read_text())
    assert prior["status"] == "fetching_data", "Do not overwrite a previous audit"
    code = Path(__file__).read_bytes()
    (root / "source_audit_trec_data.py").write_bytes(code)
    manifest = dict(prior, status="auditing_cpu", command=sys.argv, args=vars(args),
                    source_sha256={"audit_trec_data.py":sha(code)})
    save(root / "manifest.json",manifest)
    try:
        inputs = {}
        def read(path):
            data = path.read_bytes()
            inputs[str(path)] = sha(data)
            return data
        metadata = json.loads(read(root / "hf-metadata.json"))
        assert metadata["id"] == "zai-org/LongBench" and metadata["sha"] == REVISION
        entries = {r["rfilename"]:r for r in metadata["siblings"]}
        assert entries["data.zip"]["lfs"]["sha256"] == ZIP_SHA
        data_zip = read(root / "data.zip")
        assert len(data_zip) == 113932529 and sha(data_zip) == ZIP_SHA
        for name in ["README.md","LongBench.py"]:
            data = read(root / name)
            assert hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == entries[name]["blobId"]
        ast.parse((root / "LongBench.py").read_bytes())
        extracted = root / "data"
        extracted.mkdir(exist_ok=False)
        with zipfile.ZipFile(root / "data.zip") as archive:
            save(root / "archive_members.json",[dict(name=r.filename,bytes=r.file_size,compressed_bytes=r.compress_size,crc32=r.CRC) for r in archive.infolist()])
            raw = archive.read("data/trec.jsonl")
            (extracted / "trec.jsonl").write_bytes(raw)
        inputs[str(extracted / "trec.jsonl")] = sha(raw)
        raw_lines = raw.splitlines()
        rows = [json.loads(line) for line in raw_lines]
        assert len(rows) == 200 and len({r["_id"] for r in rows}) == 200
        upstream = Path(args.upstream)
        selected_sources = ["config/dataset2prompt.json","metrics.py","eval.py","pred.py","LICENSE","README.md"]
        for name in selected_sources:
            data=read(upstream / name)
            dest=root / "upstream" / name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(data)
        prompt = json.loads((root / "upstream/config/dataset2prompt.json").read_text())["trec"]
        assert prompt == "Please determine the type of the question below. Here are some examples of questions.\n\n{context}\n{input}"
        import torch
        from transformers import AutoTokenizer
        assert not torch.cuda.is_initialized()
        tokenizer = AutoTokenizer.from_pretrained(args.tokenizer,local_files_only=True)
        tokenizer_sha = {n:sha((Path(args.tokenizer)/n).read_bytes()) for n in
                         ["config.json","tokenizer.json","tokenizer_config.json","vocab.json","merges.txt"]}
        model_config=json.loads((Path(args.tokenizer)/"config.json").read_text())
        assert model_config["model_type"] == "qwen2" and not model_config.get("use_sliding_window",False)
        bytes_per_slot=2*2*model_config["num_hidden_layers"]*model_config["num_key_value_heads"]*(model_config["hidden_size"]//model_config["num_attention_heads"])
        pattern=re.compile(r"Question: ([^\n]*)\nType: ([^\n]+)(?:\n|$)")
        def normalize(q):
            return " ".join(q.split())
        global_demos=defaultdict(set)
        global_queries=defaultdict(set)
        audits=[]
        demo_counts=Counter()
        labels=Counter()
        all_classes=rows[0]["all_classes"]
        assert len(all_classes)==len(set(all_classes))==50
        for line_no,(row,line) in enumerate(zip(rows,raw_lines)):
            assert set(row)=={"input","context","answers","length","dataset","language","all_classes","_id"}
            assert row["dataset"]=="trec" and row["language"]=="en"
            assert len(row["answers"])==1 and row["answers"][0] in all_classes
            assert row["all_classes"]==all_classes
            target=re.fullmatch(r"Question: ([^\n]*)\nType:\s*",row["input"])
            assert target, row["_id"]
            question=normalize(target.group(1))
            gold=row["answers"][0]
            matches=list(pattern.finditer(row["context"]))
            assert matches and "".join(m.group(0) for m in matches)==row["context"],row["_id"]
            local=defaultdict(set)
            for match in matches:
                q,label=normalize(match.group(1)),match.group(2)
                assert label in all_classes,(row["_id"],label)
                local[q].add(label);global_demos[q].add(label);demo_counts[q]+=1
            global_queries[question].add(gold)
            labels[gold]+=1
            prefix_text=prompt.format(context=row["context"],input="")
            assert prefix_text+row["input"]==prompt.format(**row)
            # Deliberate role adaptation; not the authors' flat completion frontend.
            messages=[dict(role="system",content=prefix_text),dict(role="user",content=row["input"])]
            prefix=tokenizer.apply_chat_template(messages[:1],tokenize=True,add_generation_prompt=False)
            full=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)
            assert full[:len(prefix)]==prefix and len(full)>len(prefix)
            assert tokenizer.decode(prefix).startswith("<|im_start|>system\n")
            assert tokenizer.decode(prefix).endswith("<|im_end|>\n")
            assert tokenizer.decode(full[len(prefix):]).startswith("<|im_start|>user\n")
            suffix=full[len(prefix):]
            n=len(prefix)
            anchors=len(set(range(min(4,n)))|set(range(max(0,n-64),n)))
            budgets={str(r):dict(slots=n if r==1.0 else int(n*r),prefix_kv_bytes=(n if r==1.0 else int(n*r))*bytes_per_slot) for r in [1.0,0.75,0.5]}
            assert all(v["slots"]>=anchors for v in budgets.values())
            audit=dict(source_line_0based=line_no,source_key=row["_id"],raw_line_sha256=sha(line),
                       context_sha256=sha(row["context"].encode()),input_sha256=sha(row["input"].encode()),
                       prefix_ids_sha256=sha(json.dumps(prefix,separators=(",",":")).encode()),
                       full_ids_sha256=sha(json.dumps(full,separators=(",",":")).encode()),
                       prefix_tokens=n,suffix_tokens=len(suffix),flat_prompt_tokens=len(tokenizer.encode(prompt.format(**row),add_special_tokens=False)),
                       reported_length=row["length"],question=question,gold=gold,example_count=len(matches),
                       unique_demo_questions=len(local),local_demo_conflicts=[dict(question=q,labels=sorted(v)) for q,v in local.items() if len(v)>1],
                       target_in_own_demos=question in local,target_demo_labels=sorted(local.get(question,set())),
                       anchor_count=anchors,bf16_prefix_budgets=budgets,
                       preflight_order_sha256=sha(("20261028:trec:"+row["_id"]).encode()))
            audits.append(audit)
        save(root / "cases_cpu_audit.json",audits)
        cross=dict(demo_question_conflicts=[dict(question=q,labels=sorted(v)) for q,v in global_demos.items() if len(v)>1],
                   query_question_conflicts=[dict(question=q,labels=sorted(v)) for q,v in global_queries.items() if len(v)>1],
                   test_queries_appearing_any_demo=[dict(question=q,query_labels=sorted(v),demo_labels=sorted(global_demos[q])) for q,v in global_queries.items() if q in global_demos])
        save(root / "duplicate_conflict_audit.json",cross)
        ranges={f"{low}-{high}":sum(low<=r["prefix_tokens"]<=high for r in audits) for low,high in [(256,2048),(1024,4096),(1024,8192),(1024,16384)]}
        summary=dict(dataset_id=metadata["id"],dataset_revision=REVISION,data_zip_sha256=ZIP_SHA,
                     trec_bytes=len(raw),trec_sha256=sha(raw),rows=len(rows),unique_ids=len(rows),
                     prefix_tokens=stats([r["prefix_tokens"] for r in audits]),suffix_tokens=stats([r["suffix_tokens"] for r in audits]),
                     flat_prompt_tokens=stats([r["flat_prompt_tokens"] for r in audits]),examples_per_context=stats([r["example_count"] for r in audits]),
                     prefix_length_range_counts=ranges,unique_input_questions=len(global_queries),gold_class_count=len(labels),gold_distribution=dict(labels),
                     unique_demo_questions=len(global_demos),demo_question_occurrences=sum(demo_counts.values()),
                     repeated_demo_questions=sum(v>1 for v in demo_counts.values()),global_demo_conflict_questions=len(cross["demo_question_conflicts"]),
                     global_query_conflict_questions=len(cross["query_question_conflicts"]),
                     own_context_target_matches=sum(r["target_in_own_demos"] for r in audits),cross_context_target_matches=len(cross["test_queries_appearing_any_demo"]),
                     duplicate_contexts=len(rows)-len({r["context_sha256"] for r in audits}),
                     all_class_schema_and_native_split_checks_passed=True,tokenizer_checks=200,
                     actual_cache_checks=False,bytes_per_bf16_prefix_token_analytical=bytes_per_slot,
                     sample_execution_ids_frozen=False,execution_enabled=False,new_model_outputs=0,cuda_initialized=torch.cuda.is_initialized(),
                     frontend="Qwen native system(task header+unchanged demonstrations) then user(unchanged query); query-blind; explicit adaptation from flat author prompt",
                     limitation="Label consistency is not semantic gold validation; natural category names may be answerable without demos. No constraint, security, model quality or performance result.")
        assert not torch.cuda.is_initialized()
        save(root / "summary.json",summary)
        save(root / "tokenizer_sha256.json",tokenizer_sha)
        save(root / "label_inventory.json",all_classes)
        manifest.update(status="complete",end_unix=time.time(),input_sha256=inputs,tokenizer_sha256=tokenizer_sha,
                        artifact_sha256={n:sha((root/n).read_bytes()) for n in ["summary.json","cases_cpu_audit.json","duplicate_conflict_audit.json","tokenizer_sha256.json","label_inventory.json","archive_members.json"]})
        save(root / "manifest.json",manifest)
        print(json.dumps(summary,ensure_ascii=False))
        print(json.dumps({k:v[:5] for k,v in cross.items()},ensure_ascii=False))
    except Exception as error:
        manifest.update(status="failed",end_unix=time.time(),error_type=type(error).__name__,error_message=str(error))
        save(root / "manifest.json",manifest)
        raise


if __name__=="__main__":
    main()
