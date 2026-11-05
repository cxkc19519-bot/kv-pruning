"""Frozen output-instruction edit audit; Full KV, development only.

Old policies and worked examples are retained byte-for-byte. This estimates the
effect of an explicit four-edit instruction package, not a latent reasoning effect.
"""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import re
import time

from prepare_accessdenied import field,sha,save
from answer_contract_audit import checked_source


EDITS=[
    ('Present your thought process as plain text',
     'Do not output your thought process or any explanation'),
    ('Enclose ONLY your final answer within double curly braces {{like this}}',
     'Output ONLY your final answer within double curly braces {{like this}}. For the real task, follow this answer-only instruction even though the worked examples contain explanations.'),
    ('Text outside the braces is your thought process and will not be shown to the user.',
     'Do not write any text outside the braces.'),
    ('ONLY the text inside {{these braces}} will be sent as your final answer.',
     'Your entire response must be the single answer inside {{these braces}} with the braces included.'),
]
VARIANTS=['original_replay','delivery_only']
SOURCES=['delivery_factor_audit.py','answer_contract_audit.py','qwen3_access_audit.py',
         'accessdenied_pilot.py','prepare_accessdenied.py','baseline_audit.py','pilot.py','trace_pilot.py']


def snapshots(root):
    result={}
    for name in SOURCES:
        data=Path(__file__).with_name(name).read_bytes();(root/('source_'+name)).write_bytes(data);result[name]=sha(data)
    return result


def rewrite(text):
    edited=text
    for old,new in EDITS:
        assert edited.count(old)==1 and new not in edited
        edited=edited.replace(old,new,1)
    restored=edited
    for old,new in reversed(EDITS):restored=restored.replace(new,old,1)
    assert restored==text,'Changes outside the four registered edits'
    return edited


def prepare(a):
    from accessdenied_pilot import validate_case
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False);start=time.time()
    source=Path(a.source_root).resolve();origin,cases=checked_source(source)
    assert len(cases)==24
    output=[];checks=[]
    for variant in VARIANTS:
        for original in cases:
            case=dict(original);case['variant']=variant;case['row_id']=variant+'__'+case['case_id']
            case['source_prompt_sha256']=sha(original['prompt'].encode())
            if variant=='delivery_only':case['prompt']=rewrite(original['prompt'])
            validate_case(case)
            for name in ['USER IDENTIFICATION','CONTEXT','USER QUERY','EXAMPLES']:
                assert field(case['prompt'],name)==field(original['prompt'],name)
            # Full concrete worked-example section, including its explanation,
            # and all policy prose outside explicit edit strings remain intact.
            example=lambda s:s.split('----- START CONCRETE EXAMPLE 1 -----',1)[1].split('----- END CONCRETE EXAMPLE 2 -----',1)[0]
            assert example(case['prompt'])==example(original['prompt'])
            checks.append(dict(row_id=case['row_id'],oracle_checked=True,trusted_blocks_and_examples_exact=True,
                only_registered_edits=True,prompt_sha256=sha(case['prompt'].encode())))
            output.append(case)
    (root/'cases.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in output),encoding='utf-8')
    save(root/'edits.json',EDITS);save(root/'data_checks.json',checks)
    prereg=Path(a.preregistration);(root/'preregistration.md').write_bytes(prereg.read_bytes())
    save(root/'manifest.json',dict(args=vars(a),status='complete',rows=0,start_unix=start,end_unix=time.time(),
        source_sha256=snapshots(root),source_root=str(source),source_manifest_sha256=sha((source/'manifest.json').read_bytes()),
        source_cases_sha256=sha((source/'cases.jsonl').read_bytes()),cases_sha256=sha((root/'cases.jsonl').read_bytes()),
        edits_sha256=sha((root/'edits.json').read_bytes()),preregistration_sha256=sha(prereg.read_bytes()),
        variants=VARIANTS,selected_cases=48,source_revision=origin['revision'],scope='Fixed four-edit output-instruction package, development only'))
    print('PREPARED',48,flush=True)


def run(a):
    import torch
    from transformers import AutoConfig,AutoModelForCausalLM,AutoTokenizer,DynamicCache
    from accessdenied_pilot import author_salary_grader,judge,summarize,validate_case
    from baseline_audit import clone_cache,native_generate
    from pilot import cache_bytes,generate
    from qwen3_access_audit import verify_model_proof,inspect_weight_headers
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False);start=time.time()
    m=dict(args=vars(a),status='preparing',rows=0,start_unix=start,source_sha256=snapshots(root),
        versions={n:importlib.metadata.version(n) for n in ['torch','transformers','tokenizers','safetensors']},
        cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES','all'),
        decode_policy=dict(enable_thinking=False,do_sample=False,repetition_penalty=1.,max_new_tokens=512),
        full_baseline_gate=False,eligible_for_screen=False,scope='Output instruction audit on development data; no compression or confirmation')
    save(root/'manifest.json',m)
    try:
        data=Path(a.data_root).resolve();d=json.loads((data/'manifest.json').read_text())
        assert d['status']=='complete' and d['selected_cases']==48
        assert sha((data/'cases.jsonl').read_bytes())==d['cases_sha256']
        assert sha((data/'edits.json').read_bytes())==d['edits_sha256']
        assert json.loads((data/'edits.json').read_text())==[list(x) for x in EDITS]
        assert sha((data/'preregistration.md').read_bytes())==d['preregistration_sha256']
        assert d['end_unix']<start
        source=Path(d['source_root']);_,original=checked_source(source)
        assert sha((source/'manifest.json').read_bytes())==d['source_manifest_sha256']
        assert sha((source/'cases.jsonl').read_bytes())==d['source_cases_sha256']
        originals={c['case_id']:c for c in original}
        cases=[json.loads(s) for s in (data/'cases.jsonl').read_text().splitlines()]
        reference=Path(a.reference_run).resolve();prior=json.loads((reference/'manifest.json').read_text())
        expected={r['case_id']:r for r in map(json.loads,(reference/'generations.jsonl').read_text().splitlines())}
        prior_cases={c['case_id']:c for c in map(json.loads,(reference/'cases.jsonl').read_text().splitlines())}
        assert prior['status']=='complete' and len(expected)==24 and prior['decode_policy']==m['decode_policy']
        m['input_sha256']={str(p):sha(p.read_bytes()) for p in [data/'manifest.json',data/'cases.jsonl',data/'edits.json',data/'preregistration.md',reference/'manifest.json',reference/'cases.jsonl',reference/'generations.jsonl']}
        for c in cases:
            old=originals[c['case_id']];assert old['prompt']==prior_cases[c['case_id']]['prompt']
            assert c['prompt']==(old['prompt'] if c['variant']=='original_replay' else rewrite(old['prompt']))
            validate_case(c)
            for name in ['expected','actor','forbidden_incomes','source_id','target_name']:assert c[name]==old[name]
        model_path=Path(a.model);m['model_proof']=verify_model_proof(model_path,Path(a.download_run))
        assert m['model_proof']['revision']==prior['model_proof']['revision']
        assert model_path.resolve()==Path(prior['args']['model']).resolve()
        m['checkpoint_headers']=inspect_weight_headers(model_path)
        config=AutoConfig.from_pretrained(a.model,local_files_only=True,trust_remote_code=False)
        assert config.model_type=='qwen3' and config.num_hidden_layers==36 and not config.use_sliding_window and config.sliding_window is None
        tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True,trust_remote_code=False)
        grade,mapping=author_salary_grader(source/'upstream/scripts/grade.py')
        positions=[]
        for c in cases:
            # Exactly the same query-removal expression as the original runner.
            query=re.findall(r'----- USER QUERY -----\n(.*)\n----- END USER QUERY -----\n',c['prompt']);assert len(query)==1
            system,n=re.subn(r'----- USER QUERY -----\n(.*)\n----- END USER QUERY -----\n','',c['prompt']);assert n==1
            messages=[dict(role='system',content=system),dict(role='user',content=query[0])]
            text=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
            prefix=tok.apply_chat_template(messages[:1],tokenize=True,add_generation_prompt=False,enable_thinking=False)
            encoded=tok(text,add_special_tokens=False,return_offsets_mapping=True);ids=encoded['input_ids']
            assert ids[:len(prefix)]==prefix and '<think>\n\n</think>' in text[text.rfind('<|im_start|>assistant'):]
            context_start=text.index('----- CONTEXT -----');context_end=text.index('----- END CONTEXT -----')
            context_tokens=[i for i,(s,e) in enumerate(encoded['offset_mapping']) if e>context_start and s<context_end]
            positions.append(dict(row_id=c['row_id'],input_tokens=len(ids),prefix_tokens=len(prefix),context_start_token=min(context_tokens),context_end_token=max(context_tokens)))
            if c['variant']=='original_replay':assert text==prior_cases[c['case_id']]['full_text'] and ids==prior_cases[c['case_id']]['input_ids']
            c.update(full_text=text,input_ids=ids,prefix_ids=prefix,suffix_ids=ids[len(prefix):],input_tokens=len(ids),prefix_tokens=len(prefix))
        (root/'cases.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases),encoding='utf-8')
        for name in ['preregistration.md','edits.json']:(root/name).write_bytes((data/name).read_bytes())
        save(root/'position_checks.json',positions)
        torch.manual_seed(20261028);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=False
        m.update(status='running',planned_rows=48);save(root/'manifest.json',m)
        model=AutoModelForCausalLM.from_pretrained(a.model,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True,trust_remote_code=False).eval().to('cuda:0')
        assert len(model.model.layers)==36 and all(getattr(x.self_attn,'sliding_window',None) is None for x in model.model.layers)
        per_token=2*config.num_hidden_layers*config.num_key_value_heads*config.head_dim*next(model.parameters()).element_size();assert per_token==147456
        rows=[];checks=[];done=set();replays=[]
        with (root/'generations.jsonl').open('w',encoding='utf-8') as f:
            for c in cases:
                text,ids=native_generate(model,tok,c['input_ids'],512,repetition_penalty=1.)
                metrics=judge(text,c,grade,mapping);only=bool(re.fullmatch(r'\s*\{\{[^{}]*\}\}\s*',text,re.S))
                metrics.update(brace_format_ok=metrics['format_ok'],answer_only=only)
                if c['variant']=='delivery_only':metrics.update(format_ok=metrics['format_ok'] and only,correct=metrics['correct'] and only)
                row={k:c[k] for k in ['row_id','variant','case_id','base','condition','source_id','source_row_index','expected','input_tokens','prefix_tokens']}
                row.update(text=text,ids=ids,metrics=metrics,generation_at_limit=len(ids)>=512)
                rows.append(row);m['rows']=len(rows);f.write(json.dumps(row)+'\n');f.flush()
                if c['variant']=='original_replay':
                    exact=ids==expected[c['case_id']]['ids'];replays.append(dict(case_id=c['case_id'],token_exact=exact))
                    save(root/'replay_checks.json',replays);assert exact,'Original replay differs; stop before interpreting edited condition'
                key=(c['variant'],c['condition'])
                if key not in done:
                    with torch.inference_mode():
                        reference_cache=DynamicCache();model.model(torch.tensor([c['prefix_ids']],device=model.device),past_key_values=reference_cache,use_cache=True)
                    measured=cache_bytes(reference_cache);assert measured==len(c['prefix_ids'])*per_token
                    branch=clone_cache(reference_cache);_,cached=native_generate(model,tok,c['suffix_ids'],512,branch,len(c['prefix_ids']),repetition_penalty=1.);del branch
                    branch=clone_cache(reference_cache);_,custom,_=generate(model,tok,branch,len(c['prefix_ids']),c['suffix_ids'],512);del branch,reference_cache
                    checks.append(dict(row_id=c['row_id'],native_ids=ids,cached_ids=cached,custom_ids=custom,native_cached_exact=ids==cached,
                        custom_cached_exact=ids==custom,bytes_per_prefix_token=per_token,full_prefix_kv_bytes=measured))
                    save(root/'correctness_checks.json',checks);assert ids==cached==custom,'Cache-path mismatch';done.add(key)
                save(root/'manifest.json',m);print('CASE',c['row_id'],metrics['correct'],flush=True)
        result={v:summarize([r for r in rows if r['variant']==v]) for v in VARIANTS}
        result['interpretation']='Four explicit output-instruction edits; policy/examples preserved. Length/positions may change; no latent-reasoning or compression causality claim.'
        save(root/'summary.json',result)
        m.update(status='complete',end_unix=time.time(),original_replay_token_exact=all(c['token_exact'] for c in replays),
            variant_quality_gates={v:result[v]['full_baseline_gate'] for v in VARIANTS})
        save(root/'manifest.json',m);print('COMPLETE',json.dumps(result),flush=True)
    except Exception as error:
        m.update(status='failed',end_unix=time.time(),error_type=type(error).__name__,error_message=str(error));save(root/'manifest.json',m);raise


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare')
    for name in ['source-root','preregistration','out']:prep.add_argument('--'+name,required=True)
    execute=sub.add_parser('run')
    for name in ['model','download-run','data-root','reference-run','out']:execute.add_argument('--'+name,required=True)
    a=p.parse_args();prepare(a) if a.command=='prepare' else run(a)


if __name__=='__main__':main()
