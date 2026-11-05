"""Two-group live SDPA/profiler observation; no development inputs are inferred."""
import sys
sys.dont_write_bytecode=True
import hashlib
import gzip
import importlib.metadata
import json
from pathlib import Path
import random


def save(out,name,value):
    (out/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def event_snapshot(events):
    nodes=list(events);seen={id(e) for e in nodes}
    for e in nodes:
        parent=getattr(e,'cpu_parent',None)
        if parent is not None and id(parent) not in seen:
            seen.add(id(parent));nodes.append(parent)
        if len(nodes)>500000:raise ValueError('profiler_event_cap')
    ids={id(e):i for i,e in enumerate(nodes)}
    return [dict(uid=ids[id(e)],event_id=e.id,name=e.name,
                 parent_uid=None if getattr(e,'cpu_parent',None) is None else ids[id(e.cpu_parent)],
                 kernels=[dict(name=k.name,device=k.device) for k in getattr(e,'kernels',[])]) for e in nodes]


def main():
    out=Path(sys.argv[1]);cfg=json.loads((out/'registration_snapshot.json').read_text());root=Path(cfg['root']);directory=Path(cfg['model_path'])
    weights={}
    for name,expected in cfg['weights'].items():
        h=hashlib.sha256()
        with (directory/name).open('rb') as f:
            for b in iter(lambda:f.read(8388608),b''):h.update(b)
        assert h.hexdigest()==expected;weights[name]=dict(sha256=expected,bytes=(directory/name).stat().st_size)
    for name,v in cfg['versions'].items():assert importlib.metadata.version(name)==v
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from decoder_kv_backend import SamePrefixBackend,compare_vectors
    from sdpa_observer import SDPAObserver,profiler_inventory
    torch.set_num_threads(4);torch.manual_seed(cfg['torch_seed'])
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    model=AutoModelForCausalLM.from_pretrained(str(directory),torch_dtype=torch.bfloat16,attn_implementation='sdpa',
                                             local_files_only=True,trust_remote_code=False).eval().to('cuda:0')
    assert len(model.model.layers)==28 and set(model.config.layer_types)=={'full_attention'} and not model.config.use_sliding_window
    assert model.config.num_key_value_heads==4 and model.config._attn_implementation=='sdpa'
    assert all(p.dtype==torch.bfloat16 for p in model.parameters())
    tok=AutoTokenizer.from_pretrained(str(directory),local_files_only=True,trust_remote_code=False,use_fast=True)
    rows=[c for c in json.loads((root/cfg['native_inputs']).read_text()) if c['role']=='engineering']
    source={c['case_id']:c for c in json.loads((root/cfg['selected_cases']).read_text())}
    assert [r['case_id'] for r in rows]==cfg['engineering_case_ids']
    for row in rows:
        c=source[row['case_id']];messages=[dict(role='system',content=c['system']),dict(role='user',content=c['user'])]
        render=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        assert render==row['rendered'] and tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)==row['full_input_ids']
        assert tok(render+'{"answer":"',add_special_tokens=False)['input_ids']==row['branch_input_ids']
    save(out,'engineering_inputs.json',rows)
    save(out,'actual_runtime.json',dict(model_config=model.config.to_dict(),versions=cfg['versions'],weights=weights,
         Full_layers=28,KV_heads=4,bytes_per_slot=57344,dtype='bfloat16',attention='sdpa',device=str(model.device),tokenizer_encodes=4,tf32=False))
    backend=SamePrefixBackend(model,out,cfg['compute_bounds'])
    target=torch.nn.functional;original=target.scaled_dot_product_attention
    observer=SDPAObserver(target,marker_factory=torch.profiler.record_function,max_records=4096)
    profiles=[];controls=[];integrity=[];plans=[];differences=[]
    with torch.inference_mode():
        for row in rows:
            backend.case_id=row['case_id'];prefix,suffix=row['prefix_ids'],row['suffix_ids'];n=len(prefix);b=row['budget_slots']
            backend.path='prefix';ref,_=backend.forward(prefix,0);ref_hash=backend.fingerprint(ref)
            backend.snapshot(ref,'reference',list(range(n)))
            anchors=row['anchors'];free=[i for i in range(n) if i not in anchors]
            maps=dict(recency=sorted(anchors+sorted(free,reverse=True)[:b-len(anchors)]),
                      uniform_random=sorted(anchors+random.Random(cfg['random_seeds'][0]).sample(free,b-len(anchors))))
            branches={'full':ref}
            for name,indices in maps.items():
                branches[name]=backend.copy_cache(ref,indices);backend.validate(branches[name],b)
                backend.snapshot(branches[name],name,indices)
                plans.append(dict(case_id=row['case_id'],name=name,indices=indices,actual_prefix_bytes=backend.cache_bytes(branches[name])))
            outputs={}
            paths=[('full_batch_plain','full',False,False),('full_batch_observed','full',False,True),
                   ('recency_batch_plain','recency',False,False),('recency_batch_observed','recency',False,True),
                   ('recency_tokenwise_observed','recency',True,True),('uniform_random_batch_observed','uniform_random',False,True),
                   ('uniform_random_tokenwise_observed','uniform_random',True,True)]
            for path,name,tokenwise,observed in paths:
                backend.path=path
                if observed:
                    first=observer.calls+1
                    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA],record_shapes=True) as profile:
                        with observer:logits=backend.suffix(branches[name],suffix,n,tokenwise=tokenwise)
                    assert target.scaled_dot_product_attention is original and not observer.errors
                    events=list(profile.events());inventory=profiler_inventory(events)
                    expected=28*(len(suffix) if tokenwise else 1)
                    save(out,'early_profile_evidence.json',dict(expected=expected,markers=len(inventory['markers']),calls=observer.calls-first+1,records=observer.records,inventory=inventory))
                    filename=row['case_id']+'.'+path+'.early.trace.json.gz'
                    profile.export_chrome_trace(str(out/filename))
                    (out/(filename+'.events.json.gz')).write_bytes(gzip.compress(json.dumps(event_snapshot(events),allow_nan=False).encode(),mtime=0))
                    assert len(inventory['markers'])==expected and observer.calls-first+1==expected, 'profile_marker_count_mismatch'
                    assert all(m['backend_operators'] and m['kernels'] for m in inventory['markers']), 'missing_live_kernel_lineage'
                    filename=row['case_id']+'.'+path+'.trace.json.gz'
                    profile.export_chrome_trace(str(out/filename))
                    event_file=filename+'.events.json.gz'
                    (out/event_file).write_bytes(gzip.compress(json.dumps(event_snapshot(events),allow_nan=False).encode(),mtime=0))
                    profiles.append(dict(case_id=row['case_id'],path=path,first_observer_call=first,last_observer_call=observer.calls,
                        raw_trace=filename,event_snapshot=event_file,inventory=inventory))
                else:logits=backend.suffix(branches[name],suffix,n,tokenwise=tokenwise)
                backend.record_vector(path,logits);outputs[path]=logits
                save(out,'vectors.json',backend.vectors);save(out,'profiles.json',profiles);save(out,'sdpa_records.json',observer.records)
                save(out,'cache_snapshots.json',backend.cache_records);save(out,'gather_plans.json',plans)
            for name in ['full','recency']:
                plain,observed=outputs[name+'_batch_plain'],outputs[name+'_batch_observed']
                exact=torch.equal(plain,observed);controls.append(dict(case_id=row['case_id'],name=name,exact_logits_equal=exact))
                assert exact,'observer_or_profiler_same_path_control_failed'
            for name in ['recency','uniform_random']:
                value=compare_vectors(outputs[name+'_batch_observed'],outputs[name+'_tokenwise_observed'],[32,33,34,35])
                differences.append(dict(case_id=row['case_id'],name=name,metrics=value,diagnostic_only=True))
            assert backend.fingerprint(ref)==ref_hash
            integrity.append(dict(case_id=row['case_id'],reference_sha256_before=ref_hash,reference_sha256_after=backend.fingerprint(ref)))
            save(out,'transparency_controls.json',controls);save(out,'path_differences.json',differences);save(out,'reference_integrity.json',integrity)
            del branches,ref,outputs
    assert backend.calls==108 and backend.tokens==1082 and backend.vector_count==14 and observer.calls==2856
    assert target.scaled_dot_product_attention is original and not observer.errors
    save(out,'observation_summary.json',dict(observation_completed=True,old_numeric_engineering_accepted=False,
        forward_calls=108,teacher_forced_input_tokens=1082,archived_logit_vectors=14,observed_SDPA_calls=2856,
        profiles=len(profiles),same_path_controls=4,exact_controls_passed=True,callable_restored=True,observer_errors=observer.errors,
        tokenizer_encodes=4,development_model_calls=0,generated_tokens=0,model_answers=0,H3_tested=False))
    print(json.dumps(dict(observation_completed=True,profiles=len(profiles),observed_SDPA_calls=2856)),flush=True)


if __name__=='__main__':main()
