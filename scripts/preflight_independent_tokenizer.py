"""Offline native-tokenizer check; no torch, weights or GPU access."""
import os
os.environ.update(USE_TORCH='0', USE_TF='0', USE_FLAX='0', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import signal
import time
import traceback


def sha(b): return hashlib.sha256(b).hexdigest()
def save(p, x): p.write_text(json.dumps(x,ensure_ascii=True,allow_nan=False,indent=2)+'\n')
def check(x, reason):
    if not x: raise ValueError(reason)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    r=Path(__file__).resolve().parent.parent
    check(a.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning','server explicit execution required')
    raw=(r/'configs/independent-squad-tokenizer-proposal-v1.json').read_bytes();cfg=json.loads(raw)
    out=r/cfg['run'];check(out.resolve().parent==(r/'results').resolve(),'run boundary');out.mkdir(exist_ok=False)
    start=time.monotonic();state=dict(status='running',stage='verify_inputs',pid=os.getpid(),main_outputs=0,engineering_outputs=0,model_loaded=False,gpu_queried=False,cases_completed=0,tokenizer_encodes=0)
    def timeout(*args): raise TimeoutError('90 second cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(90)
    rows=[]
    try:
        (out/'proposal_snapshot.json').write_bytes(raw)
        src=Path(__file__).read_bytes();(out/'source.py').write_bytes(src)
        for p,h in [(cfg['cases'],cfg['cases_sha256']),(cfg['parent_manifest'],cfg['parent_manifest_sha256'])]:check(sha((r/p).read_bytes())==h,'parent pin:'+p)
        model=Path(cfg['model']);check(model.name==cfg['model_revision'],'revision')
        for p,h in cfg['files'].items():check(sha((model/p).read_bytes())==h,'model pin:'+p)
        mc=json.loads((model/'config.json').read_text());tc=json.loads((model/'tokenizer_config.json').read_text())
        check(sha(tc['chat_template'].encode())==cfg['template_sha256'],'template pin')
        check(mc['model_type']=='qwen2' and mc['num_hidden_layers']==28 and mc['num_key_value_heads']==4 and not mc['use_sliding_window'],'Full Attention config')
        check(mc['hidden_size']//mc['num_attention_heads']==128 and mc['torch_dtype']=='bfloat16','shape/dtype')
        versions={k:importlib.metadata.version(k) for k in cfg['versions']};check(versions==cfg['versions'],'versions')
        cases=[json.loads(x) for x in (r/cfg['cases']).read_text().splitlines()]
        cases=[x for x in cases if x['split_role']=='engineering'][:2]+[x for x in cases if x['split_role']=='development'];check(len(cases)==14,'role count');check(sha((r/cfg['amendment']).read_bytes())==cfg['amendment_sha256'],'amendment pin')
        save(out/'execution_snapshot.json',dict(execution_enabled=True,runner_implemented=True,proposal_sha256=sha(raw),runner_sha256=sha(src),versions=versions,python=sys.version,environment={k:os.environ[k] for k in ['USE_TORCH','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE']},model_files=cfg['files'],network=False,weight_load=False))
        from transformers import AutoTokenizer, AutoConfig
        tok=AutoTokenizer.from_pretrained(str(model),local_files_only=True,trust_remote_code=False,use_fast=True)
        ac=AutoConfig.from_pretrained(str(model),local_files_only=True,trust_remote_code=False)
        check(tok.is_fast and len(ac.layer_types)==28 and set(ac.layer_types)=={'full_attention'},'native config layer types')
        state['stage']='native_boundaries'
        for case in cases:
            messages=[dict(role='system',content=case['prompt']['system']),dict(role='user',content=case['prompt']['user'])]
            system=tok.apply_chat_template(messages[:1],tokenize=False,add_generation_prompt=False)
            qs=[case['question']]+(cfg['alternative_engineering_questions'] if case['split_role']=='engineering' else [])
            variants=[]
            for question in qs:
                user=case['prompt']['user'][:case['question_start_user_character']]+question
                ms=[messages[0],dict(role='user',content=user)]
                rendered=tok.apply_chat_template(ms,tokenize=False,add_generation_prompt=True)
                expected=system+'<|im_start|>user\n'+user+'<|im_end|>\n<|im_start|>assistant\n'
                check(rendered==expected,'native rendering changed')
                encoded=tok(rendered,add_special_tokens=False,return_offsets_mapping=True);state['tokenizer_encodes']+=1
                ids=tok.apply_chat_template(ms,tokenize=True,add_generation_prompt=True);state['tokenizer_encodes']+=1
                check(ids==encoded['input_ids'] and len(ids)<=2048,'encoding equality/length')
                offsets=encoded['offset_mapping'];qchar=len(system)+len('<|im_start|>user\n')+case['question_start_user_character']
                check(all(not (a<qchar<b) for a,b in offsets),'token straddles question boundary')
                n=sum(b<=qchar for a,b in offsets)
                check(n>0 and all(b<=qchar for a,b in offsets[:n]) and all(a>=qchar for a,b in offsets[n:]),'noncontiguous question boundary')
                protected=[i for i,(a,b) in enumerate(offsets) if b>a and a<len(system) and b>0]
                coverage={j for i in protected for j in range(max(0,offsets[i][0]),min(len(system),offsets[i][1]))}
                check(coverage==set(range(len(system))) and max(protected)<n,'system coverage')
                anchors=set(range(4))|set(range(n-64,n));required=sorted(anchors|set(protected));budget=n//2
                feasible=len(required)<=budget
                variants.append(dict(question_sha256=sha(question.encode()),prefix_ids_sha256=sha(json.dumps(ids[:n],separators=(',',':')).encode()),prefix_tokens=n))
                if question==case['question']:
                    row=dict(case_id=case['case_id'],split_role=case['split_role'],prompt_sha256=case['prompt_sha256'],input_ids=ids,offsets=offsets,prefix_tokens=n,suffix_tokens=len(ids)-n,budget_state='ok' if feasible else 'infeasible_budget',header_ids=protected,anchor_ids=sorted(anchors),required_pinned_ids=required,budget=budget,system_character_end=len(system),question_character_start=qchar,original_prefix_kv_bytes=n*57344,compressed_prefix_kv_bytes=budget*57344,position_mapping_checked=False)
            check(len({x['prefix_ids_sha256'] for x in variants})==1,'alternative query leaks into prefix')
            row['query_prefix_variants']=variants;rows.append(row);state['cases_completed']+=1
            save(out/'tokenized_cases.json',rows)
        check(state['tokenizer_encodes']==36 and 'torch' not in sys.modules,'encode cap/no torch')
        state.update(status='complete',stage='complete',native_boundary_gate=True,half_budget_gate=all(x['budget_state']=='ok' for x in rows),infeasible_budget_cases=sum(x['budget_state']!='ok' for x in rows),full_attention_layers=ac.layer_types,bytes_per_token=57344,protected_tokens_range=[min(len(x['header_ids']) for x in rows),max(len(x['header_ids']) for x in rows)],prefix_tokens_range=[min(x['prefix_tokens'] for x in rows),max(x['prefix_tokens'] for x in rows)],budget_range=[min(x['budget'] for x in rows),max(x['budget'] for x in rows)],full_support=None)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc));(out/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0);state['elapsed_seconds']=time.monotonic()-start;save(out/'summary.json',state)
        files=[p for p in out.iterdir() if p.is_file()];check(len(files)<32 and sum(p.stat().st_size for p in files)<33554432,'archive cap')
        save(out/'manifest.json',{p.name:sha(p.read_bytes()) for p in files});print(json.dumps(state),flush=True)
    return 0 if state['status']=='complete' else 1


if __name__=='__main__': raise SystemExit(main())
