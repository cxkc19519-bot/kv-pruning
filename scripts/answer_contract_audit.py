"""One frozen answer-delivery adaptation; no compression or prompt search.

Prepare both cohorts before development inference. Only a passing new-contract
development run can authorize confirmation; the old failed runs remain intact.
"""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import re
import time

from prepare_accessdenied import field,sha,save


CONTRACT_FIELDS=['USER IDENTIFICATION','CONTEXT','USER QUERY']
SOURCES=['answer_contract_audit.py','qwen3_access_audit.py','accessdenied_pilot.py',
         'prepare_accessdenied.py','baseline_audit.py','pilot.py','trace_pilot.py']


def snapshots(root):
    sources={}
    for name in SOURCES:
        data=Path(__file__).with_name(name).read_bytes()
        (root/('source_'+name)).write_bytes(data);sources[name]=sha(data)
    return sources


def checked_source(root):
    manifest=json.loads((root/'manifest.json').read_text())
    assert manifest['status']=='complete'
    assert sha((root/'cases.jsonl').read_bytes())==manifest['cases_sha256']
    for name,info in manifest['upstream_files'].items():
        assert sha((root/'upstream'/name).read_bytes())==info['sha256']
    return manifest,[json.loads(s) for s in (root/'cases.jsonl').read_text().splitlines()]


def prepare(a):
    from accessdenied_pilot import validate_case
    source=Path(a.source_root).resolve();root=Path(a.out);root.mkdir(parents=True,exist_ok=False)
    started=time.time();origin,cases=checked_source(source)
    policy=Path(a.contract).read_bytes();checks=[]
    for case in cases:
        old=case['prompt'];parts={name:field(old,name) for name in CONTRACT_FIELDS}
        case['prompt']=policy.decode('utf-8').strip()+'\n\n'+'\n\n'.join(
            f'----- {name} -----\n{parts[name]}\n----- END {name} -----' for name in CONTRACT_FIELDS)+'\n'
        for name,value in parts.items():assert field(case['prompt'],name)==value
        # Extract complete marked blocks as well: whitespace within each source
        # block is retained exactly, including the original context's newlines.
        for name in CONTRACT_FIELDS:
            pattern=rf'----- {name} -----.*?----- END {name} -----'
            before=re.search(pattern,old,re.S).group(0)
            after=re.search(pattern,case['prompt'],re.S).group(0)
            if before!=after:
                case['prompt']=case['prompt'].replace(after,before,1)
            assert re.search(pattern,case['prompt'],re.S).group(0)==before
        validate_case(case)
        case['source_prompt_sha256']=sha(old.encode())
        case['contract_sha256']=sha(policy)
        checks.append(dict(case_id=case['case_id'],trusted_blocks_exact=True,rendered_oracle_checked=True))
    (root/'contract.txt').write_bytes(policy)
    (root/'cases.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases),encoding='utf-8')
    save(root/'data_checks.json',checks)
    save(root/'manifest.json',dict(status='complete',rows=0,start_unix=started,end_unix=time.time(),
        source_sha256=snapshots(root),args=vars(a),source_root=str(source),source_revision=origin['revision'],
        source_cases_sha256=sha((source/'cases.jsonl').read_bytes()),
        source_manifest_sha256=sha((source/'manifest.json').read_bytes()),
        contract_sha256=sha(policy),cases_sha256=sha((root/'cases.jsonl').read_bytes()),selected_cases=len(cases),
        scope='New joint policy/output adaptation; trusted blocks and gold unchanged; no model-selected cases'))
    print('PREPARED',len(cases),sha(policy),flush=True)


def run(a):
    import torch
    from transformers import AutoConfig,AutoModelForCausalLM,AutoTokenizer,DynamicCache
    from accessdenied_pilot import author_salary_grader,judge,summarize,validate_case
    from baseline_audit import clone_cache,native_generate
    from pilot import cache_bytes,generate
    from qwen3_access_audit import verify_model_proof,inspect_weight_headers
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False)
    data_root=Path(a.data_root).resolve();d=json.loads((data_root/'manifest.json').read_text())
    manifest=dict(status='preparing',rows=0,args=vars(a),start_unix=time.time(),source_sha256=snapshots(root),
        versions={n:importlib.metadata.version(n) for n in ['torch','transformers','tokenizers','safetensors']},
        cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES','all'),contract_sha256=d['contract_sha256'],
        decode_policy=dict(enable_thinking=False,do_sample=False,repetition_penalty=1.,max_new_tokens=512),
        scope='New answer-contract task; Full KV only; raw output is delivered; no security-specific mechanism claim')
    save(root/'manifest.json',manifest)
    try:
        assert d['status']=='complete' and d['selected_cases']==24
        assert sha((data_root/'cases.jsonl').read_bytes())==d['cases_sha256']
        assert sha((data_root/'contract.txt').read_bytes())==d['contract_sha256']
        source=Path(d['source_root']);_,old=checked_source(source)
        assert sha((source/'manifest.json').read_bytes())==d['source_manifest_sha256']
        assert sha((source/'cases.jsonl').read_bytes())==d['source_cases_sha256']
        cases=[json.loads(s) for s in (data_root/'cases.jsonl').read_text().splitlines()]
        old={c['case_id']:c for c in old}
        for c in cases:
            validate_case(c)
            for name in CONTRACT_FIELDS:assert field(c['prompt'],name)==field(old[c['case_id']]['prompt'],name)
            for name in ['expected','forbidden_incomes','actor','source_id','target_name','condition']:
                assert c[name]==old[c['case_id']][name]
        manifest['input_sha256']={str(p):sha(p.read_bytes()) for p in [data_root/'manifest.json',data_root/'cases.jsonl',data_root/'contract.txt']}
        model_path=Path(a.model);manifest['model_proof']=verify_model_proof(model_path,Path(a.download_run))
        manifest['checkpoint_headers']=inspect_weight_headers(model_path)
        config=AutoConfig.from_pretrained(a.model,local_files_only=True,trust_remote_code=False)
        assert config.model_type=='qwen3' and config.num_hidden_layers==36
        assert not config.use_sliding_window and config.sliding_window is None
        if a.stage=='confirmation':
            assert a.gate_run
            prior=Path(a.gate_run);gate=json.loads((prior/'manifest.json').read_text())
            assert gate['status']=='complete' and gate['full_baseline_gate'] is True,'Development quality gate failed'
            assert gate['contract_sha256']==manifest['contract_sha256'] and gate['decode_policy']==manifest['decode_policy']
            assert gate['model_proof']['revision']==manifest['model_proof']['revision']
            assert Path(gate['args']['model']).resolve()==model_path.resolve()
            previous=[json.loads(s) for s in (prior/'cases.jsonl').read_text().splitlines()]
            for name in ['source_id','target_name']:assert {c[name] for c in cases}.isdisjoint({c[name] for c in previous})
            manifest['development_gate_manifest_sha256']=sha((prior/'manifest.json').read_bytes())
        tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True,trust_remote_code=False)
        grade,mapping=author_salary_grader(source/'upstream/scripts/grade.py')
        for c in cases:
            query=field(c['prompt'],'USER QUERY')
            system,n=re.subn(r'----- USER QUERY -----.*?----- END USER QUERY -----\n?','',c['prompt'],flags=re.S);assert n==1
            messages=[dict(role='system',content=system),dict(role='user',content=query)]
            text=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
            prefix=tok.apply_chat_template(messages[:1],tokenize=True,add_generation_prompt=False,enable_thinking=False)
            ids=tok.encode(text,add_special_tokens=False);assert ids[:len(prefix)]==prefix
            assert '<think>\n\n</think>' in text[text.rfind('<|im_start|>assistant'):]
            c.update(full_text=text,input_ids=ids,prefix_ids=prefix,suffix_ids=ids[len(prefix):],input_tokens=len(ids),prefix_tokens=len(prefix))
        (root/'contract.txt').write_bytes((data_root/'contract.txt').read_bytes())
        (root/'cases.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases),encoding='utf-8')
        torch.manual_seed(20261028);torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=False
        manifest.update(status='running',planned_rows=24);save(root/'manifest.json',manifest)
        model=AutoModelForCausalLM.from_pretrained(a.model,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True,trust_remote_code=False).eval().to('cuda:0')
        assert len(model.model.layers)==36 and all(getattr(x.self_attn,'sliding_window',None) is None for x in model.model.layers)
        bytes_per_token=2*config.num_hidden_layers*config.num_key_value_heads*config.head_dim*next(model.parameters()).element_size()
        assert bytes_per_token==147456
        rows=[];checks=[];done=set()
        with (root/'generations.jsonl').open('w',encoding='utf-8') as f:
            for c in cases:
                text,ids=native_generate(model,tok,c['input_ids'],512,repetition_penalty=1.)
                metrics=judge(text,c,grade,mapping)
                only=bool(re.fullmatch(r'\s*\{\{[^{}]*\}\}\s*',text,re.S))
                metrics.update(brace_format_ok=metrics['format_ok'],answer_only=only,
                    format_ok=metrics['format_ok'] and only,correct=metrics['correct'] and only)
                row={k:c[k] for k in ['case_id','base','condition','source_id','source_row_index','expected','input_tokens','prefix_tokens']}
                row.update(text=text,ids=ids,metrics=metrics,generation_at_limit=len(ids)>=512)
                rows.append(row);manifest['rows']=len(rows);f.write(json.dumps(row)+'\n');f.flush()
                if c['condition'] not in done:
                    with torch.inference_mode():
                        reference=DynamicCache();model.model(torch.tensor([c['prefix_ids']],device=model.device),past_key_values=reference,use_cache=True)
                    measured=cache_bytes(reference);assert measured==len(c['prefix_ids'])*bytes_per_token
                    branch=clone_cache(reference);_,cached=native_generate(model,tok,c['suffix_ids'],512,branch,len(c['prefix_ids']),repetition_penalty=1.);del branch
                    branch=clone_cache(reference);_,custom,_=generate(model,tok,branch,len(c['prefix_ids']),c['suffix_ids'],512);del branch,reference
                    checks.append(dict(case_id=c['case_id'],native_ids=ids,cached_ids=cached,custom_ids=custom,
                        native_cached_exact=ids==cached,custom_cached_exact=ids==custom,bytes_per_prefix_token=bytes_per_token,full_prefix_kv_bytes=measured))
                    save(root/'correctness_checks.json',checks);assert ids==cached==custom,'Full cache-path parity failed'
                    done.add(c['condition'])
                save(root/'summary.json',summarize(rows));save(root/'manifest.json',manifest)
                print('CASE',c['case_id'],metrics['correct'],flush=True)
        result=summarize(rows);result['gate']+='; output must contain only the single answer block'
        save(root/'summary.json',result)
        manifest.update(status='complete',end_unix=time.time(),full_baseline_gate=result['full_baseline_gate'])
        save(root/'manifest.json',manifest);print('COMPLETE',json.dumps(result),flush=True)
    except Exception as error:
        manifest.update(status='failed',end_unix=time.time(),error_type=type(error).__name__,error_message=str(error))
        save(root/'manifest.json',manifest);raise


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--source-root',required=True);prep.add_argument('--contract',required=True);prep.add_argument('--out',required=True)
    execute=sub.add_parser('run')
    for name in ['model','download-run','data-root','out']:execute.add_argument('--'+name,required=True)
    execute.add_argument('--stage',choices=['development','confirmation'],required=True);execute.add_argument('--gate-run')
    a=p.parse_args();prepare(a) if a.command=='prepare' else run(a)


if __name__=='__main__':main()
