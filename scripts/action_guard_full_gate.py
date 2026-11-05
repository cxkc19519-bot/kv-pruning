"""One preregistered Full/NoHistory gate, with native/cached equivalence first."""
import argparse
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, DynamicCache, GenerationConfig

from action_guard_native import encode_rendered, schema_ok, source_namespace, strict_judgment
from fetch_pinned_model import verify


def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def append(path,obj):
    with path.open('a') as f:f.write(json.dumps(obj,ensure_ascii=False)+'\n')


def clone(cache):
    result=DynamicCache()
    for i,l in enumerate(cache.layers):
        k,v=l.keys.clone(),l.values.clone()
        assert torch.equal(k,l.keys) and torch.equal(v,l.values) and k.data_ptr()!=l.keys.data_ptr()
        result.update(k,v,i)
    return result


def state(cache):return [(l.keys.data_ptr(),l.values.data_ptr(),l.keys._version,l.values._version,tuple(l.keys.shape)) for l in cache.layers]


@torch.no_grad()
def prefill(model,ids):
    # Reference caches need normal tensor version counters for state().
    # Inference-mode tensors omit those counters even outside the context.
    cache=DynamicCache();x=torch.tensor([ids],device=model.device);pos=torch.arange(len(ids),device=model.device)
    model.model(input_ids=x,past_key_values=cache,use_cache=True,position_ids=pos[None,:],cache_position=pos)
    assert len(cache.layers)==36 and all(l.keys.shape[2]==len(ids) for l in cache.layers)
    assert sum(t.numel()*t.element_size() for l in cache.layers for t in [l.keys,l.values])==147456*len(ids)
    return cache


@torch.inference_mode()
def native(model,ids,generation,cache=None,prefix=0):
    x=torch.tensor([ids],device=model.device);kwargs={}
    if cache is not None:
        assert cache.get_seq_length()==prefix
        kwargs=dict(past_key_values=cache,cache_position=torch.arange(prefix,prefix+len(ids),device=model.device))
    out=model.generate(input_ids=x,attention_mask=torch.ones((1,prefix+len(ids)),device=model.device,dtype=torch.long),
                       generation_config=generation,use_model_defaults=False,logits_to_keep=1,**kwargs)
    return out[0,len(ids):].tolist()


@torch.inference_mode()
def custom(model,cache,prefix,suffix,generation):
    x=torch.tensor([suffix],device=model.device);tokens=[]
    for step in range(generation.max_new_tokens):
        physical=cache.get_seq_length();logical=prefix if step==0 else prefix+len(suffix)+step-1
        assert physical==logical,'Full-only decoder'
        n=x.shape[1];pos=torch.arange(logical,logical+n,device=model.device)
        out=model(input_ids=x,past_key_values=cache,use_cache=True,position_ids=pos[None,:],cache_position=pos,logits_to_keep=1)
        token=int(out.logits[0,-1].argmax());tokens.append(token);del out
        if token in generation.eos_token_id:break
        x=torch.tensor([[token]],device=model.device)
    return tokens


def summary(cases,rows):
    by={(r['key'],r['condition']):r for r in rows};out={}
    for condition in ['full','no_history']:
        subset=[by[(c['key'],condition)] for c in cases if (c['key'],condition) in by]
        out[condition]=dict(n=len(subset),correct=sum(r['strict_correct'] for r in subset),
                            valid_judgment=sum(r['strict_prediction'] is not None for r in subset),
                            schema=sum(r['schema_ok'] for r in subset),errors=sum(r['status']!='ok' for r in subset),
                            truncated=sum(r['truncated'] for r in subset),
                            by_class={str(g):dict(n=sum(r['gold']==g for r in subset),correct=sum(r['gold']==g and r['strict_correct'] for r in subset)) for g in [0,1]})
    pairs=[(by[(c['key'],'full')],by[(c['key'],'no_history')]) for c in cases if all((c['key'],cond) in by for cond in ['full','no_history'])]
    out['paired']=dict(n=len(pairs),transitions=dict(Counter(('C' if a['strict_correct'] else 'W')+'2'+('C' if b['strict_correct'] else 'W') for a,b in pairs)),
                       full_correct_no_history_wrong=sum(a['strict_correct'] and not b['strict_correct'] for a,b in pairs),
                       unsafe_full_correct_no_history_clear=sum(a['gold']==1 and a['strict_correct'] and b['strict_prediction']==0 for a,b in pairs))
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--out',required=True);args=p.parse_args()
    root=Path(args.out);root.mkdir(parents=True,exist_ok=False)
    raw_config=Path(args.config).read_bytes();c=json.loads(raw_config);assert c['execution_enabled'] is False
    m=dict(status='preflight',start_unix=time.time(),pid=os.getpid(),args=vars(args),rows=0,new_model_outputs=0,
           config_sha256=sha(raw_config),source_sha256={},model_execution_snapshot_created=False)
    save(root/'manifest.json',m);(root/'proposal.json').write_bytes(raw_config)
    for name in ['action_guard_full_gate.py','action_guard_native.py','fetch_pinned_model.py']:
        raw=Path(__file__).with_name(name).read_bytes();(root/('source_'+name)).write_bytes(raw);m['source_sha256'][name]=sha(raw)
    def timeout_handler(*_):raise TimeoutError('Frozen wall-time ceiling reached')
    signal.signal(signal.SIGALRM,timeout_handler);signal.alarm(c['limits']['wall_seconds'])
    rows=[]
    try:
        overlap=Path(c['overlap_run']);assert json.loads((overlap/'summary.json').read_text())['overlap_gate']
        cpu=Path(c['cpu_run']);assert json.loads((cpu/'summary.json').read_text())['cpu_gate']
        raw_cases=(overlap/'frozen_cases.jsonl').read_bytes();assert sha(raw_cases)==c['cases_sha256']
        (root/'cases.jsonl').write_bytes(raw_cases);cases=[json.loads(l) for l in raw_cases.splitlines()]
        assert len(cases)==32 and Counter(x['gold'] for x in cases)=={0:16,1:16}
        spec=json.loads(Path('configs/stepguard-model-artifacts-v1.json').read_text())
        assert spec['revision']==c['model_revision']
        download=json.loads((Path(c['download_run'])/'manifest.json').read_text());assert download['status']=='complete'
        modeldir=Path(c['model_dir']);checks=[verify(modeldir/e['rfilename'],e) for e in spec['files']];assert all(checks)
        save(root/'weight_checks.json',checks)
        ns,native_hashes=source_namespace(c['native_source_run'])
        tok=AutoTokenizer.from_pretrained(modeldir,local_files_only=True,trust_remote_code=False)
        for case in cases:
            for condition in c['conditions']:
                assert encode_rendered(case['rendered'][condition],tok)==case['encoded'][condition]
        snapshot=copy.deepcopy(c);snapshot.update(execution_enabled=True,stage='Full-only task-support gate',source_sha256=m['source_sha256'],native_source_sha256=native_hashes)
        save(root/'execution_snapshot.json',snapshot);m['model_execution_snapshot_created']=True
        torch.manual_seed(c['decoding']['seed']);torch.cuda.set_device(0)
        model=AutoModelForCausalLM.from_pretrained(modeldir,local_files_only=True,trust_remote_code=False,torch_dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda:0').eval()
        assert len(model.model.layers)==36 and all(l.attention_type=='full_attention' for l in model.model.layers)
        generation=GenerationConfig(do_sample=False,num_beams=1,repetition_penalty=1.,max_new_tokens=c['decoding']['max_new_tokens'],
                                    eos_token_id=c['decoding']['eos_token_ids'],pad_token_id=c['decoding']['pad_token_id'],bos_token_id=model.generation_config.bos_token_id,use_cache=True)
        save(root/'generation_config.json',generation.to_dict())
        # Transformers >=4.50 may otherwise replace explicit global-default
        # values (including do_sample=False) with this checkpoint's defaults.
        effective,_=model._prepare_generation_config(generation,use_model_defaults=False)
        for field in ['do_sample','num_beams','repetition_penalty','max_new_tokens','eos_token_id','pad_token_id']:
            assert getattr(effective,field)==getattr(generation,field),field
        save(root/'effective_generation_config.json',effective.to_dict())
        for case in cases[:3]:
            for condition in c['conditions']:
                encoded=case['encoded'][condition];ids=encoded['input_ids'];prefix=encoded['prefix_length'];suffix=ids[prefix:]
                reference=prefill(model,ids[:prefix]);before=state(reference)
                outputs={}
                outputs['native_whole']=native(model,ids,generation)
                outputs['native_cached']=native(model,suffix,generation,clone(reference),prefix)
                outputs['custom_cached']=custom(model,clone(reference),prefix,suffix,generation)
                for mode,tokens in outputs.items():append(root/'engineering.jsonl',dict(key=case['key'],condition=condition,mode=mode,generated_ids=tokens))
                assert outputs['native_whole']==outputs['native_cached']==outputs['custom_cached'],'Cached/native token mismatch'
                assert state(reference)==before
                assert outputs['native_whole'][-1] in generation.eos_token_id,'Engineering truncation'
                del reference
                print('ENGINEERING',case['key'],condition,len(outputs['native_whole']),flush=True)
        m.update(status='running',engineering_outputs=18);save(root/'manifest.json',m)
        for case in cases:
            for condition in c['conditions']:
                started=time.time();row=dict(key=case['key'],condition=condition,gold=case['gold'],status='ok')
                try:
                    tokens=native(model,case['encoded'][condition]['input_ids'],generation)
                    text=tok.decode(tokens,skip_special_tokens=True);prediction=strict_judgment(text)
                    row.update(generated_ids=tokens,response=text,strict_prediction=prediction,strict_correct=prediction==case['gold'],
                               schema_ok=schema_ok(text),native_compatibility_prediction=ns['_parse_safe_unsafe'](text)[0],
                               truncated=not tokens or tokens[-1] not in generation.eos_token_id,
                               output_tokens=len(tokens),elapsed_seconds=time.time()-started)
                except Exception as error:
                    row.update(status='error',error_type=type(error).__name__,error_message=str(error),strict_prediction=None,strict_correct=False,schema_ok=False,truncated=False,elapsed_seconds=time.time()-started)
                append(root/'generations.jsonl',row);rows.append(row);m.update(rows=len(rows),new_model_outputs=len(rows));save(root/'manifest.json',m)
                print('ROW',len(rows),case['key'],condition,row['strict_prediction'],case['gold'],row.get('output_tokens'),flush=True)
        s=summary(cases,rows);g=c['gate'];full=s['full'];paired=s['paired']
        passed=(full['correct']>=g['full_correct_min'] and all(full['by_class'][str(v)]['correct']>=g['each_class_correct_min'] for v in [0,1])
                and full['valid_judgment']==32 and full['errors']==0 and sum(s[x]['truncated'] for x in c['conditions'])==0
                and paired['full_correct_no_history_wrong']>=8 and paired['unsafe_full_correct_no_history_clear']>=4)
        s.update(task_support_gate=passed,compression_executed=False,new_method_claim=False,
                 interpretation='Full-only task support; NoHistory changes input length and position, not a KV pruning effect.')
        save(root/'summary.json',s);m.update(status='complete',end_unix=time.time(),task_support_gate=passed,compression_executed=False,
                                          gpu_peak_allocated=torch.cuda.max_memory_allocated(),gpu_peak_reserved=torch.cuda.max_memory_reserved())
        print('SUMMARY',json.dumps(s),flush=True)
    except Exception as error:
        m.update(status='failed',end_unix=time.time(),error_type=type(error).__name__,error_message=str(error),traceback=traceback.format_exc());raise
    finally:
        signal.alarm(0);save(root/'manifest.json',m)


if __name__=='__main__':main()
