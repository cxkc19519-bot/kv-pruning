"""Independent monolithic native-generate check of all frozen scale requests."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from baseline_audit import native_generate
from scale_pilot import evaluate
from trace_pilot import save, sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--source-run',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();root=Path(a.out);root.mkdir(parents=True,exist_ok=False);prior=Path(a.source_run)
    original=[json.loads(x) for x in (prior/'generations.jsonl').read_text().splitlines()]
    original={(r['case_id'],r['query_index']):r for r in original if r['policy']=='full'}
    cases=[json.loads(x) for x in (prior/'cases.jsonl').read_text().splitlines()]
    torch.manual_seed(20261027);torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=False
    sources=['scale_native_audit.py','scale_pilot.py','trace_pilot.py','pilot.py','baseline_audit.py',
             'vendor/expected_attention_reference.py','vendor/expected_support.py','vendor/__init__.py','vendor/LICENSE','vendor/NOTICE.md']
    source_hash={}
    for name in sources:
        data=(Path(__file__).parent/name).read_bytes();source_hash[name]=sha(data)
        dest=root/('source_'+name);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    manifest=dict(args=vars(a),status='running',start_unix=time.time(),source_sha256=source_hash,
        input_sha256={name:sha((prior/name).read_bytes()) for name in ['cases.jsonl','generations.jsonl','manifest.json']},
        versions={n:importlib.metadata.version(n) for n in ['torch','transformers','tokenizers','safetensors']},
        decode_policy=dict(do_sample=False,repetition_penalty=1.,max_new_tokens=64),planned_rows=len(original))
    save(root/'manifest.json',manifest);(root/'cases.jsonl').write_bytes((prior/'cases.jsonl').read_bytes())
    tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True)
    model=AutoModelForCausalLM.from_pretrained(a.model,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True).eval().to('cuda:0')
    assert model.config.model_type=='qwen2' and all(x.self_attn.sliding_window is None for x in model.model.layers)
    rows=[]
    with (root/'generations.jsonl').open('w') as f:
        for c in cases:
            for i,q in enumerate(c['requests']):
                ids=tok.encode(q['full_text'],add_special_tokens=False);assert ids==c['prefix_ids']+q['suffix_ids']
                text,new=native_generate(model,tok,ids,64,repetition_penalty=1.)
                row=dict(case_id=c['id'],query_index=i,task=c['task'],record_count=c['record_count'],text=text,ids=new,
                         metrics=evaluate(text,q,c),token_exact_with_cached_custom=new==original[(c['id'],i)]['ids'])
                rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
    result=dict(n=len(rows),token_exact=sum(r['token_exact_with_cached_custom'] for r in rows),
                groups=[dict(task=t,n=sum(r['task']==t for r in rows),correct=sum(r['metrics']['correct'] for r in rows if r['task']==t)) for t in ['permission','routing']],
                note='All frozen requests audited; no filtering of errors and no compression efficacy run')
    save(root/'summary.json',result);manifest.update(status='complete',rows=len(rows),end_unix=time.time());save(root/'manifest.json',manifest)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
