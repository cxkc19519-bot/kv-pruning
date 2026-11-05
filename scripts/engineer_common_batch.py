"""Two-group operational contract acceptance; no development-task inference."""
import sys
sys.dont_write_bytecode=True
import gzip
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path


def save(out,name,value):
    (out/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def main():
    out=Path(sys.argv[1]);cfg=json.loads((out/'registration_snapshot.json').read_text());root=Path(cfg['root']);directory=Path(cfg['model_path'])
    from sdpa_profiler_adapter import run_cpu_checks
    save(out,'profiler_adapter_cpu_checks.json',run_cpu_checks())
    for name,h in cfg['weights'].items():
        actual=hashlib.sha256()
        with (directory/name).open('rb') as f:
            for b in iter(lambda:f.read(8388608),b''):actual.update(b)
        assert actual.hexdigest()==h
    for name,v in cfg['versions'].items():assert importlib.metadata.version(name)==v
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from pilot import WindowScores
    from common_batch_backend import CommonBatchBackend
    from decoder_objective import candidate_masks,distribution_kl,top_support
    from sdpa_profiler_adapter import SDPAObserver,profiler_inventory
    from observe_sdpa_gpu_v4 import event_snapshot
    torch.set_num_threads(4);torch.manual_seed(cfg['torch_seed'])
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    model=AutoModelForCausalLM.from_pretrained(str(directory),torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True,trust_remote_code=False).eval().to('cuda:0')
    assert len(model.model.layers)==28 and set(model.config.layer_types)=={'full_attention'} and not model.config.use_sliding_window
    assert model.config.num_key_value_heads==4 and all(p.dtype==torch.bfloat16 for p in model.parameters())
    tokenizer=AutoTokenizer.from_pretrained(str(directory),local_files_only=True,trust_remote_code=False,use_fast=True)
    cases=[c for c in json.loads((root/cfg['native_inputs']).read_text()) if c['role']=='engineering']
    sources={c['case_id']:c for c in json.loads((root/cfg['selected_cases']).read_text())}
    assert [c['case_id'] for c in cases]==cfg['engineering_case_ids']
    for case in cases:
        c=sources[case['case_id']];messages=[dict(role='system',content=c['system']),dict(role='user',content=c['user'])]
        text=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        assert text==case['rendered'] and tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)==case['full_input_ids']
        assert tokenizer(text+'{"answer":"',add_special_tokens=False)['input_ids']==case['branch_input_ids']
    save(out,'engineering_inputs.json',cases)
    save(out,'actual_runtime.json',dict(model_config=model.config.to_dict(),versions=cfg['versions'],Full_layers=28,KV_heads=4,bytes_per_slot=57344,
         attention='sdpa',dtype='bfloat16',tokenizer_encodes=4,tf32=False,operational_contract='common_batch_explicit_causal_v1'))
    backend=CommonBatchBackend(model,out,cfg['compute_bounds'])
    observer=SDPAObserver(torch.nn.functional,marker_factory=torch.profiler.record_function,max_records=2048)
    original=torch.nn.functional.scaled_dot_product_attention
    profiles=[];checks=[];plans=[];objectives=[];integrity=[]
    with torch.inference_mode():
        for case in cases:
            cid=case['case_id'];backend.case_id=cid;prefix,suffix=case['prefix_ids'],case['suffix_ids'];n=len(prefix);b=case['budget_slots']
            backend.path='plain_prefix';reference,plain_logits=backend.forward(prefix,0)
            old_hooks=[tuple(layer.self_attn._forward_hooks) for layer in model.model.layers]
            scorer=WindowScores(window=64,kernel=5)
            handles=[layer.self_attn.register_forward_hook(scorer.hook,with_kwargs=True) for layer in model.model.layers]
            try:
                backend.path='scored_prefix';scored,scored_logits=backend.forward(prefix,0)
            finally:
                for handle in handles:handle.remove()
            assert [tuple(layer.self_attn._forward_hooks) for layer in model.model.layers]==old_hooks
            assert torch.equal(plain_logits,scored_logits) and backend.fingerprint(reference)==backend.fingerprint(scored)
            assert set(scorer.scores)==set(range(28))
            values={str(layer):scores.tolist() for layer,scores in scorer.scores.items()}
            assert all(tuple(s.shape)==(1,4,n) and bool(torch.isfinite(s).all()) for s in scorer.scores.values())
            aggregate=[math.fsum(float(scorer.scores[layer][0,head,i]) for layer in range(28) for head in range(4))/112 for i in range(n)]
            (out/(cid+'.prefix_scores.json.gz')).write_bytes(gzip.compress(json.dumps(values,allow_nan=False).encode(),mtime=0))
            maskplan=candidate_masks(n,b,aggregate,cfg['random_seeds'],[28,4,128,2]);assert maskplan['status']=='feasible_index_plan'
            plans.append(dict(case_id=cid,score_aggregate=aggregate,mask_plan=maskplan,score_source='prefix_only_window64_avgpool5_layer_head_mean',hook_cache_equal=True,hook_logits_equal=True,hook_restored=True))
            before=backend.fingerprint(reference);backend.snapshot(reference,'reference',list(range(n)))
            states=[dict(name='full',indices=None)]+maskplan['candidates']
            by_repeat=[{},{}]
            first=observer.calls+1
            with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA],record_shapes=True) as profile:
                with observer:
                    for repeat in range(2):
                        for state in (states if repeat==0 else list(reversed(states))):
                            name=state['name'];compact=backend.copy_cache(reference,state['indices'])
                            backend.validate(compact,n if name=='full' else b)
                            if repeat==0 and name!='full':backend.snapshot(compact,name,state['indices'])
                            backend.path=name+'.repeat'+str(repeat)
                            logits=backend.suffix(compact,suffix,n,tokenwise=False)
                            backend.record_vector(backend.path,logits);by_repeat[repeat][name]=logits
                            assert backend.fingerprint(reference)==before
                            del compact
            assert torch.nn.functional.scaled_dot_product_attention is original and not observer.errors
            events=list(profile.events());inv=profiler_inventory(events)
            assert len(inv['markers'])==504 and observer.calls-first+1==504
            assert all(m['backend_operators'] and m['kernels'] and {x['family'] for x in m['backend_operators']}=={'efficient'} for m in inv['markers'])
            profile_file=cid+'.trace.json.gz';profile.export_chrome_trace(str(out/profile_file))
            event_file=cid+'.events.json.gz';(out/event_file).write_bytes(gzip.compress(json.dumps(event_snapshot(events)).encode(),mtime=0))
            profiles.append(dict(case_id=cid,first_call=first,last_call=observer.calls,trace=profile_file,events=event_file,inventory=inv))
            full=[x.tolist() for x in [by_repeat[0]['full'],by_repeat[1]['full']]]
            supports={'global':list(range(152064)),'top128':top_support(full[0],128),'top256':top_support(full[0],256),'legal':[32,33,34,35]}
            for state in states:
                name=state['name'];assert torch.equal(by_repeat[0][name],by_repeat[1][name])
                metrics=[]
                for repeat in range(2):
                    q=by_repeat[repeat][name].tolist()
                    metrics.append({key:distribution_kl(full[repeat],q,ids) for key,ids in supports.items()})
                assert metrics[0]==metrics[1] and all(x['status']=='finite' for x in metrics[0].values())
                checks.append(dict(case_id=cid,name=name,logits_exact_repeat=True,KL_scores_exact_repeat=True))
                objectives.append(dict(case_id=cid,name=name,repeats=metrics))
            integrity.append(dict(case_id=cid,reference_sha256_before=before,reference_sha256_after=backend.fingerprint(reference)))
            save(out,'candidate_plans.json',plans);save(out,'repeat_checks.json',checks);save(out,'objective_repeats.json',objectives)
            save(out,'reference_integrity.json',integrity);save(out,'vectors.json',backend.vectors);save(out,'cache_snapshots.json',backend.cache_records)
            save(out,'mask_records.json',list(backend.mask_records.values()))
            (out/'profiles.json.gz').write_bytes(gzip.compress(json.dumps(profiles).encode(),mtime=0))
            (out/'sdpa_records.json.gz').write_bytes(gzip.compress(json.dumps(observer.records).encode(),mtime=0))
            del reference,scored,scorer,by_repeat
    assert backend.calls==40 and backend.tokens==2356 and backend.vector_count==36 and observer.calls==1008
    save(out,'contract_summary.json',dict(operational_contract_passed=True,engineering_groups=2,candidates_per_group=8,repeat_states=18,
        archived_logit_vectors=36,forward_calls=40,input_tokens=2356,tokenizer_encodes=4,actual_SDPA_calls=1008,
        actual_masks_recorded=True,all_suffix_backend_families=['efficient'],old_cross_path_gate_passed=False,
        candidate_rankings_computed=False,Full12_support_tested=False,development_model_calls=0,generated_tokens=0,model_answers=0))
    print(json.dumps(dict(operational_contract_passed=True,vectors=36,actual_SDPA_calls=1008)),flush=True)


if __name__=='__main__':main()
