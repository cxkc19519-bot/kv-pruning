"""Freeze all ten unused eligible TREC questions; CPU/provenance audit only."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.request

import torch
from transformers import AutoTokenizer
from trec_pruning_utils import native_header_metadata, random_prefix_scores, select_prefix_indices, validate_indices


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")
def norm(text):return " ".join(text.split())
def examples(context):
    matches=list(re.finditer(r"Question: ([^\n]*)\nType: ([^\n]+)(?:\n|$)",context))
    assert "".join(match.group(0) for match in matches)==context
    return {(norm(match.group(1)),match.group(2)) for match in matches}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--out",required=True);parser.add_argument("--tokenizer",required=True)
    parser.add_argument("--provenance-snapshot");args=parser.parse_args()
    root=Path(args.out);root.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).read_bytes();(root/"source_prepare_trec_holdout.py").write_bytes(source)
    helper=Path(__file__).with_name("trec_pruning_utils.py").read_bytes()
    assert sha(helper)=="92594811de726c585087fe1356a81cfcbe3a19a1fd6bb68a7e8781a334c53918"
    (root/"source_trec_pruning_utils.py").write_bytes(helper)
    manifest=dict(status="preparing",rows=0,new_model_outputs=0,start_unix=time.time(),args=vars(args),source_sha256={"prepare_trec_holdout.py":sha(source),"trec_pruning_utils.py":sha(helper)},scope="CPU holdout preparation; no model weights or generation")
    save(root/"manifest.json",manifest);inputs={};fetched=[]
    try:
        assert not torch.cuda.is_initialized();torch.set_num_threads(4)
        paths=dict(data=Path("results/20261028-trec-data-preflight-v2/data/trec.jsonl"),
                   eligibility=Path("results/20261028-trec-context-gate-data-v1/eligibility.json"),
                   development=Path("results/20261028-trec-context-gate-data-v1/cases.jsonl"),
                   audit=Path("results/20261028-trec-data-preflight-v2/cases_cpu_audit.json"),
                   conflicts=Path("results/20261028-trec-data-preflight-v2/duplicate_conflict_audit.json"),
                   parent=Path("configs/trec-pruning-calibration-proposal-v1.json"),
                   frontend=Path("configs/trec-context-gate-proposal-v1.json"),
                   prior_tradeoffs=Path("results/20261028-trec-pruning-v1/header_tradeoffs.json"))
        for p in paths.values():inputs[str(p)]=sha(p.read_bytes())
        assert inputs[str(paths["data"])]=="20a88e14f7442f58a39082cdd7396f1093ea8162da0a4ea7ead7d6757514c8f4"
        assert inputs[str(paths["parent"])]=="289bb122e62788cff3406df9ba42a792172b2f10959144be187271e52634093f"
        assert inputs[str(paths["development"])]=="e709d4bd298cd61a272f42835a180c7ac032b450b0aa1c40892814c7f6c8caf7"
        raw_lines=paths["data"].read_bytes().splitlines();data={r["_id"]:r for r in map(json.loads,raw_lines)}
        development=[json.loads(s) for s in paths["development"].read_text().splitlines()]
        used={r["source_key"] for r in development}
        eligible=json.loads(paths["eligibility"].read_text())["eligible"]
        keys=[key for key in eligible if key not in used]
        assert len(keys)==10 and len(eligible)==42 and eligible[:32]==[r["source_key"] for r in development]
        assert keys==json.loads(paths["prior_tradeoffs"].read_text())["remaining_same_length_eligible_keys"]
        assert not used.intersection(keys)
        save(root/"frozen_source_keys.json",keys)
        upstream=root/"upstream";upstream.mkdir()
        for name,url in [("taxonomy.html","https://cogcomp.seas.upenn.edu/Data/QA/QC/definition.html"),
                         ("TREC_10.label","https://cogcomp.seas.upenn.edu/Data/QA/QC/TREC_10.label")]:
            record=dict(name=name,url=url,status="fetching")
            try:
                if args.provenance_snapshot:
                    snapshot=Path(args.provenance_snapshot)
                    prior=next(r for r in json.loads((snapshot/"upstream_checks.json").read_text()) if r["name"]==name)
                    raw=(snapshot/"upstream"/name).read_bytes()
                    assert prior["status"]=="complete" and prior["url"]==url and sha(raw)==prior["sha256"] and len(raw)==prior["bytes"]
                    record.update(prior,reused_verified_snapshot=str(snapshot))
                    for path in [snapshot/"upstream_checks.json",snapshot/"upstream"/name]:inputs[str(path)]=sha(path.read_bytes())
                else:
                    response=urllib.request.urlopen(url,timeout=20);raw=response.read()
                    record.update(status="complete",bytes=len(raw),sha256=sha(raw),final_url=response.url,content_type=response.headers.get("Content-Type"))
                (upstream/name).write_bytes(raw)
            except Exception as error:
                record.update(status="failed",error=repr(error));fetched.append(record);save(root/"upstream_checks.json",fetched);raise
            fetched.append(record);save(root/"upstream_checks.json",fetched)
        # Original source is a dated snapshot, not a Git commit; keep raw bytes + SHA.
        original={}
        for index,line in enumerate((upstream/"TREC_10.label").read_text(encoding="latin-1").splitlines()):
            label,question=line.split(" ",1);key=norm(question)
            assert key not in original
            original[key]=dict(label=label,source_line_0based=index)
        assert len(original)==500
        mapping={"ENTY:substance":"Element and substance","HUM:ind":"Individual","DESC:def":"Definition of something",
                 "LOC:state":"State","LOC:other":"Other location","LOC:city":"City","LOC:country":"Country"}
        taxonomy=(upstream/"taxonomy.html").read_text(encoding="latin-1")
        assert all(word in taxonomy.lower() for word in ["substance","definition","individual","state","country","cities"])
        parent=json.loads(paths["parent"].read_text());front=json.loads(paths["frontend"].read_text());header=front["shared_system_header"]
        audit={r["source_key"]:r for r in json.loads(paths["audit"].read_text())}
        ambiguity={r["question"] for r in json.loads(paths["conflicts"].read_text())["demo_question_conflicts"]}
        tokenizer=AutoTokenizer.from_pretrained(args.tokenizer,local_files_only=True)
        token_path=Path("results/20261028-trec-data-preflight-v2/tokenizer_sha256.json")
        token_sha=json.loads(token_path.read_text());inputs[str(token_path)]=sha(token_path.read_bytes())
        for name,digest in token_sha.items():assert sha((Path(args.tokenizer)/name).read_bytes())==digest
        dev_demo_sets=[examples(data[r["source_key"]]["context"]) for r in development]
        dev_demo_union=set().union(*dev_demo_sets)
        dev_queries={norm(re.fullmatch(r"Question: ([^\n]*)\nType:\s*",data[r["source_key"]]["input"]).group(1)) for r in development}
        new_sets=[examples(data[key]["context"]) for key in keys]
        cases=[];provenance=[];overlap=[];metadata=[];selector_checks=0
        for key,own_examples in zip(keys,new_sets):
            row=data[key];a=audit[key]
            assert 1024<=a["prefix_tokens"]<=4096 and not a["local_demo_conflicts"] and not a["target_in_own_demos"]
            assert not {q for q,label in own_examples}.intersection(ambiguity)
            question=norm(re.fullmatch(r"Question: ([^\n]*)\nType:\s*",row["input"]).group(1))
            assert question not in dev_queries and question not in {q for q,label in own_examples}
            original_entry=original[question];assert mapping[original_entry["label"]]==row["answers"][0]
            provenance.append(dict(source_key=key,question=question,longbench_gold=row["answers"][0],original_code=original_entry["label"],original_test_line=original_entry["source_line_0based"],original_label_match=True))
            messages=[dict(role="system",content=header+row["context"]),dict(role="user",content=row["input"])]
            ids=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)
            prefix=tokenizer.apply_chat_template(messages[:1],tokenize=True,add_generation_prompt=False)
            assert ids[:len(prefix)]==prefix and len(ids)+64<=8192
            v=dict(messages=messages,input_ids=ids,input_ids_sha256=sha(json.dumps(ids,separators=(",",":")).encode()),prefix_tokens=len(prefix),suffix_tokens=len(ids)-len(prefix))
            cases.append(dict(source_key=key,source_line_0based=a["source_line_0based"],raw_line_sha256=sha(raw_lines[a["source_line_0based"]]),source_context_sha256=sha(row["context"].encode()),gold=row["answers"][0],versions=dict(with_demos=v)))
            meta=native_header_metadata(tokenizer,messages,ids,len(prefix),header)
            assert meta["required_pinned_count"]<=meta["budget"]
            meta.update(source_key=key,prefix_ids=prefix,prefix_ids_sha256=sha(json.dumps(prefix,separators=(",",":")).encode()))
            metadata.append(meta)
            # No real saliency: selector checks with deterministic random scores only.
            for layer in range(28):
                scores=random_prefix_scores(len(prefix),key,layer,4)
                for pin in [False,True]:
                    idx=select_prefix_indices(scores,len(prefix)//2,meta["header_ids"],pin)
                    validate_indices(idx,len(prefix),len(prefix)//2,4,meta["header_ids"],pin)
                    selector_checks+=4
            seen=own_examples&dev_demo_union
            overlap.append(dict(source_key=key,example_count=a["example_count"],unique_demo_pairs=len(own_examples),
                demo_pairs_seen_in_development=len(seen),demo_pair_overlap_fraction=len(seen)/len(own_examples),
                query_seen_in_development_queries=question in dev_queries,query_seen_in_development_demos=question in {q for q,label in dev_demo_union},
                max_example_pair_jaccard_with_development=max(len(own_examples&s)/len(own_examples|s) for s in dev_demo_sets)))
        (root/"cases.jsonl").write_text("\n".join(json.dumps(r,ensure_ascii=False) for r in cases)+"\n",encoding="utf-8")
        save(root/"header_budget_metadata.json",metadata);save(root/"original_label_provenance.json",provenance)
        save(root/"demonstration_overlap.json",overlap);save(root/"tokenizer_sha256.json",token_sha)
        save(root/"taxonomy_mapping_used.json",mapping)
        summary=dict(candidates=10,all_unused_eligible_kept=True,development_id_overlap=0,development_query_overlap=0,
            original_test_label_matches=sum(r["original_label_match"] for r in provenance),
            gold_classes=dict(Counter(c["gold"] for c in cases)),
            prefix_range=[min(r["prefix_tokens"] for r in metadata),max(r["prefix_tokens"] for r in metadata)],
            suffix_range=[min(c["versions"]["with_demos"]["suffix_tokens"] for c in cases),max(c["versions"]["with_demos"]["suffix_tokens"] for c in cases)],
            header_counts=sorted({r["header_count"] for r in metadata}),required_pinned_counts=sorted({r["required_pinned_count"] for r in metadata}),
            half_budget_range=[min(r["budget"] for r in metadata),max(r["budget"] for r in metadata)],
            new_query_seen_in_development_demo_count=sum(r["query_seen_in_development_demos"] for r in overlap),
            demo_overlap_fraction_range=[min(r["demo_pair_overlap_fraction"] for r in overlap),max(r["demo_pair_overlap_fraction"] for r in overlap)],
            shared_development_demo_pairs=len(set().union(*new_sets)&dev_demo_union),total_holdout_unique_demo_pairs=len(set().union(*new_sets)),
            native_input_checks=10,selector_layer_head_checks=selector_checks,cases_sha256=sha((root/"cases.jsonl").read_bytes()),
            new_model_outputs=0,cuda_initialized=torch.cuda.is_initialized(),execution_enabled=False,
            semantic_review="Pending explicit per-source review; source-label match is provenance, not proof of unique or unambiguous category",
            limitation="Unused test questions on same source/length subset, not independent training examples or a power-guaranteed confirmation set")
        assert not torch.cuda.is_initialized();save(root/"summary.json",summary)
        manifest.update(status="complete_pending_semantic_review",end_unix=time.time(),input_sha256=inputs,tokenizer_sha256=token_sha,
            artifact_sha256={str(p.relative_to(root)):sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and p.name!='manifest.json'})
        save(root/"manifest.json",manifest);print(json.dumps(summary,ensure_ascii=False));print(json.dumps(provenance,ensure_ascii=False))
    except Exception as error:
        manifest.update(status="failed",end_unix=time.time(),error_type=type(error).__name__,error_message=str(error),input_sha256=inputs)
        save(root/"manifest.json",manifest);raise


if __name__=="__main__":main()
