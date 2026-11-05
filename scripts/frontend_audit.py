"""Bounded native Full-KV role/position audit and oracle-row diagnostic."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import time

import torch
from transformers import AutoModelForCausalLM,AutoTokenizer,DynamicCache
from baseline_audit import clone_cache,native_generate
from frontend_cases import first_fact,transform
from pilot import generate
from scale_pilot import evaluate,make_world,pad_cases,summary
from trace_pilot import save,sha


def summarize(rows):
    groups=[];passing=[]
    for variant in sorted({r['variant'] for r in rows}):
        result=summary([r for r in rows if r['variant']==variant])
        for group in result['groups']:group['variant']=variant;groups.append(group)
        if result['passing_record_counts']:passing.append(variant)
    return dict(groups=groups,passing_variants=passing,
        scope='Frozen development audit. Oracle row is a diagnostic, never an eligible baseline.',
        candidate_eligible='single_aligned' in passing)


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--out',required=True)
    p.add_argument('--source-run');p.add_argument('--stage',choices=['audit','fresh'],default='audit')
    p.add_argument('--base-start',type=int,default=700);p.add_argument('--bases',type=int,default=6)
    a=p.parse_args();root=Path(a.out);root.mkdir(parents=True,exist_ok=False)
    source={}
    for name in ['frontend_audit.py','frontend_cases.py','scale_pilot.py','trace_pilot.py','baseline_audit.py','pilot.py',
                 'vendor/expected_attention_reference.py','vendor/expected_support.py','vendor/__init__.py','vendor/LICENSE','vendor/NOTICE.md']:
        data=(Path(__file__).parent/name).read_bytes();source[name]=sha(data)
        dest=root/('source_'+name);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    manifest=dict(args=vars(a),status='preparing',start_unix=time.time(),source_sha256=source,
        versions={n:importlib.metadata.version(n) for n in ['torch','transformers','tokenizers','safetensors']},
        model_config_sha256=sha((Path(a.model)/'config.json').read_bytes()),cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES','all'),
        decode_policy=dict(do_sample=False,repetition_penalty=1.,max_new_tokens=64))
    save(root/'manifest.json',manifest)
    tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True)
    if a.stage=='audit':
        assert a.source_run;prior=Path(a.source_run)
        cases=[json.loads(x) for x in (prior/'cases.jsonl').read_text().splitlines()]
        original={(r['case_id'],r['query_index']):r for r in map(json.loads,(prior/'generations.jsonl').read_text().splitlines()) if r['policy']=='full'}
        manifest['input_sha256']={name:sha((prior/name).read_bytes()) for name in ['cases.jsonl','generations.jsonl','manifest.json']}
        variants=['original','single_matched','two_aligned','single_aligned','row_given']
    else:
        assert a.source_run;prior=Path(a.source_run)
        assert json.loads((prior/'manifest.json').read_text())['status']=='complete'
        assert json.loads((prior/'summary.json').read_text())['candidate_eligible'],'Development candidate failed; no fresh run'
        cases=pad_cases(tok,[make_world(tok,b,w,t,32) for b in range(a.base_start,a.base_start+a.bases) for w in [0,1] for t in ['permission','routing']])
        original={};variants=['single_aligned'];manifest['development_manifest_sha256']=sha((prior/'manifest.json').read_bytes())
    targets={n:max(first_fact(tok,c['prefix_text']) for c in cases if c['record_count']==n) for n in {c['record_count'] for c in cases}}
    plan=[transform(tok,c,v,targets[c['record_count']]) for c in cases for v in variants]
    # Explicitly compare directory positions across semantic tasks, within world.
    for c in plan:
        if c['frontend'] not in ['two_aligned','single_aligned']:continue
        mate=next(x for x in plan if x['base']==c['base'] and x['swap']==c['swap'] and x['task']!=c['task'] and x['frontend']==c['frontend'])
        assert mate['fact_row_ids']==c['fact_row_ids']
        assert len(mate['prefix_ids'])==len(c['prefix_ids'])
        assert [len(q['suffix_ids']) for q in mate['requests']]==[len(q['suffix_ids']) for q in c['requests']]
    with (root/'cases.jsonl').open('w') as f:
        for c in plan:f.write(json.dumps(c)+'\n')
    save(root/'input_checks.json',dict(cases=len(cases),variants=variants,rendered_cases=len(plan),directory_tokens_preserved=True,
        aligned_task_fact_positions_equal=True,source_complete_input_lengths_preserved_except_row_diagnostic=True,targets=targets))
    manifest.update(status='running',planned_rows=len(plan)*4);save(root/'manifest.json',manifest)
    torch.manual_seed(20261027);torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=False
    try:model=AutoModelForCausalLM.from_pretrained(a.model,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True).eval().to('cuda:0')
    except torch.OutOfMemoryError:
        manifest.update(status='failed_oom',rows=0,end_unix=time.time());save(root/'manifest.json',manifest);raise
    assert model.config.model_type=='qwen2' and all(x.self_attn.sliding_window is None for x in model.model.layers)
    rows=[];checks=[];done=set()
    with (root/'generations.jsonl').open('w') as f:
        for c in plan:
            variant=c['frontend'];reference=None
            if variant not in done:
                with torch.inference_mode():
                    reference=DynamicCache();model.model(torch.tensor([c['prefix_ids']],device=model.device),past_key_values=reference,use_cache=True)
            for qi,q in enumerate(c['requests']):
                full=tok.encode(q['full_text'],add_special_tokens=False);assert full==c['prefix_ids']+q['suffix_ids']
                text,ids=native_generate(model,tok,full,64,repetition_penalty=1.)
                row={k:c[k] for k in ['base','swap','task','record_count','target_length']}
                row.update(case_id=c['id'],query_index=qi,variant=variant,policy='full',allowed=q['allowed'],metrics=evaluate(text,q,c),text=text,ids=ids)
                if variant=='original':row['token_exact_with_source']=ids==original[(c['id'],qi)]['ids']
                rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
                if reference is not None:
                    branch=clone_cache(reference);_,cached_ids=native_generate(model,tok,q['suffix_ids'],64,branch,len(c['prefix_ids']),repetition_penalty=1.);del branch
                    branch=clone_cache(reference);_,custom_ids,_=generate(model,tok,branch,len(c['prefix_ids']),q['suffix_ids'],64);del branch
                    check=dict(variant=variant,query_index=qi,native_cached_exact=ids==cached_ids,custom_cached_exact=ids==custom_ids,
                               native_ids=ids,cached_ids=cached_ids,custom_ids=custom_ids)
                    checks.append(check);save(root/'correctness_checks.json',checks)
                    assert ids==cached_ids==custom_ids,'New prefix generation parity failed'
            if reference is not None:del reference;done.add(variant)
            save(root/'summary.json',summarize(rows));print('CASE',c['id'],variant,'rows',len(rows),flush=True)
    result=summarize(rows);save(root/'summary.json',result)
    manifest.update(status='complete',rows=len(rows),end_unix=time.time(),candidate_eligible=result['candidate_eligible']);save(root/'manifest.json',manifest)
    print('COMPLETE',json.dumps(result),flush=True)


if __name__=='__main__':main()
