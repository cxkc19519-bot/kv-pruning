"""Stdlib independent replay of archived frontend offsets and budget arithmetic."""
import sys
sys.dont_write_bytecode=True
import ast
from collections import Counter
import datetime
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def byte_sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):
    assert not p.exists(),p
    p.write_text(json.dumps(x,ensure_ascii=True,allow_nan=False,indent=2)+'\n')


def main():
    r=Path(__file__).resolve().parent.parent;assert str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning'
    d=r/'results/20261030-independent-evidence-frontends-preflight-v1';cfg=read(d/'proposal_snapshot.json');summary=read(d/'summary.json')
    assert summary['status']=='complete' and summary['tokenizer_encodes']==96 and summary['full_native_variants']==48 and summary['model_case_rows']==32 and summary['budget_evaluations']==128
    for name,w in read(d/'manifest.json').items():assert sha(d/name)==w,name
    for name,w in cfg['inputs'].items():assert sha(r/name)==w,name
    snap=read(d/'execution_snapshot.json');assert snap['proposal_sha256']==sha(d/'proposal_snapshot.json')
    assert sha(d/'source_runner.py')==snap['runner_sha256']==sha(r/cfg['runner'])
    assert sha(d/'source_validator.py')==snap['validator_sha256']==sha(Path(__file__))
    for path in [d/'source_runner.py',d/'source_validator.py']:
        for n in ast.walk(ast.parse(path.read_text())):
            if isinstance(n,ast.Import):assert not any(x.name.split('.')[0] in ['torch','tensorflow','jax','vllm'] for x in n.names)
            if isinstance(n,ast.ImportFrom) and n.module=='transformers':assert {x.name for x in n.names}<={'AutoConfig','AutoTokenizer'}
    source=[json.loads(s) for s in (r/cfg['cases']).read_text().splitlines()]
    selected=[c for c in source if c['split_role'] in ['engineering','development']]
    assert Counter(c['split_role'] for c in selected)=={'engineering':4,'development':12}
    cases={c['case_id']:c for c in selected};assert len(cases)==16
    variants=read(d/'native_variants.json');rows=read(d/'tokenized_cases.json');evaluations=read(d/'budget_evaluations.json');probes=read(d/'native_layout_probes.json')
    assert len(variants)==48 and len(rows)==32 and len(evaluations)==128
    models={m['key']:m for m in cfg['models']};slots_bytes={};metadata_files=0;metadata_bytes=0
    for model in models.values():
        path=Path(model['path']);assert path.name==model['revision']
        for name,w in model['metadata_sha256'].items():assert sha(path/name)==w,name;metadata_files+=1;metadata_bytes+=(path/name).stat().st_size
        ac=read(path/'config.json');tc=read(path/'tokenizer_config.json');assert byte_sha(tc['chat_template'].encode())==model['chat_template_sha256']
        layers=ac['num_hidden_layers'];kv=ac['num_key_value_heads'];dimension=ac['hidden_size']//ac['num_attention_heads'];slots_bytes[model['key']]=layers*2*kv*dimension*2
        assert slots_bytes[model['key']]==model['config_layout']['bytes_per_prefix_slot_expected']
    assert metadata_files==16 and metadata_bytes<=cfg['bounds']['max_metadata_bytes']
    by={};zero_controls=query_crossings=0
    for v in variants:
        model,cid,index=v['model'],v['case_id'],v['variant'];key=(model,cid,index);assert key not in by;by[key]=v
        case=cases[cid];assert v['split_role']==case['split_role']
        assert index==0 or case['split_role']=='engineering' and index in (1,2)
        question=case['question'] if index==0 else cfg['query_boundary']['alternatives_for_engineering_only'][index-1]
        assert v['question']==question and case['prompt']['user'][case['question_start_user_character']:]==case['question']
        user=case['prompt']['user'][:case['question_start_user_character']]+question;system=case['prompt']['system']
        if model=='Qwen':
            frame='<|im_start|>system\n'+system+'<|im_end|>\n';prefix=frame+'<|im_start|>user\n';expected=prefix+user+'<|im_end|>\n<|im_start|>assistant\n'
            assert probes[model]['system_only_render']==frame
        else:
            tc=read(Path(models[model]['path'])/'tokenizer_config.json');bos=tc['bos_token'];bos=bos['content'] if isinstance(bos,dict) else bos
            frame=bos+'[INST] '+system+'\n\n';prefix=frame;expected=prefix+user+'[/INST]'
            assert probes[model]['system_only_render']==bos and not probes[model]['system_only_contains_original_content']
        assert v['rendered']==expected and byte_sha(expected.encode())==v['rendered_sha256']
        ids=v['input_ids'];assert ids==v['native_tokenized_ids'] and 0<len(ids)<=2048 and all(type(i) is int and i>=0 for i in ids)
        raw=v['offsets'];eff=v['effective_offsets'];assert len(raw)==len(eff)==len(ids)
        mapped={x['token_index']:x for x in v['zero_offset_control_mappings']};assert len(mapped)==len(v['zero_offset_control_mappings'])
        for i,((a,b),pair) in enumerate(zip(raw,eff)):
            if [a,b]!=[0,0]:assert pair==[a,b]
            else:
                item=mapped[i];assert item['token_id']==ids[i] and item['character_span']==pair
                assert probes[model]['special_token_map'][item['literal']]==ids[i] and expected[pair[0]:pair[1]]==item['literal'];zero_controls+=1
                occurrences=[];at=0
                while True:
                    p=expected.find(item['literal'],at)
                    if p<0:break
                    occurrences.append([p,p+len(item['literal'])]);at=p+len(item['literal'])
                indices=[k for k,t in enumerate(ids) if t==ids[i]];assert len(indices)==len(occurrences) and pair==occurrences[indices.index(i)]
            assert 0<=pair[0]<pair[1]<=len(expected)
        q=len(prefix)+case['question_start_user_character'];assert q==v['question_character_start'] and len(frame)==v['system_character_end'] and len(prefix)==v['user_character_start']
        cached=[i for i,(a,b) in enumerate(eff) if b<=q];n=len(cached);assert cached==list(range(n)) and n==v['prefix_tokens'] and v['suffix_tokens']==len(ids)-n
        crossed=[i for i,(a,b) in enumerate(eff) if a<q<b];assert crossed==v['crossing_query_token_indices'] and all(i>=n for i in crossed);query_crossings+=len(crossed)
        header=[i for i,(a,b) in enumerate(eff) if a<len(frame) and b>0];assert header==v['header_ids'] and all(i<n for i in header)
        assert all(any(eff[i][0]<=position<eff[i][1] for i in header) for position in range(len(frame)))
        assert byte_sha(json.dumps(ids[:n],separators=(',',':')).encode())==v['prefix_ids_sha256']
    byrow={}
    for row in rows:
        key=(row['model'],row['case_id']);assert key not in byrow;byrow[key]=row
        base=by[(*key,0)];case=cases[key[1]]
        for field in ['input_ids','prefix_tokens','suffix_tokens','header_ids','offsets','effective_offsets','question_character_start','system_character_end']:assert row[field]==base[field]
        assert row['prompt_sha256']==case['prompt_sha256'] and row['context_group_id']==case['context_group_id'] and row['gold_sha256']==case['gold_sha256']
        assert row['actual_KV_tensor_verified'] is False and row['KV_bytes_per_slot_predicted']==slots_bytes[key[0]]
        expected_variants=range(3) if case['split_role']=='engineering' else range(1)
        assert all(by[(*key,i)]['input_ids'][:by[(*key,i)]['prefix_tokens']]==base['input_ids'][:base['prefix_tokens']] for i in expected_variants)
    old={x['case_id']:x for x in read(r/cfg['Qwen_regression_reference'])}
    for cid,prior in old.items():
        current=byrow[('Qwen',cid)]
        for field in ['input_ids','prefix_tokens','suffix_tokens','header_ids','prompt_sha256']:assert current[field]==prior[field]
    seen=set();coverage={}
    for e in evaluations:
        key=(e['model'],e['case_id'],e['retention'],e['protection_mode']);assert key not in seen;seen.add(key)
        row=byrow[key[:2]];n=row['prefix_tokens'];ratio=Fraction(e['retention']);slots=n*ratio.numerator//ratio.denominator
        anchors=set(range(min(4,n)))|set(range(max(0,n-64),n));protected=set(row['header_ids']) if e['protection_mode']=='complete_system_union_anchors' else set();required=anchors|protected;ok=slots>0 and len(required)<=slots
        b=e['budget'];assert b['state']==('ok' if ok else 'infeasible_budget') and b['requested_slots']==b['effective_slots']==slots and b['required_positions']==sorted(required)
        assert b['anchor_count']==len(anchors) and b['protected_unique_count']==len(protected) and b['extra_protected_slots']==len(required)-len(anchors) and b['required_union_count']==len(required)
        assert b['free_slots']==(slots-len(required) if ok else None) and b['protection_free'] is False
        assert e['requested_prefix_KV_bytes_predicted']==slots*slots_bytes[e['model']] and e['actual_KV_tensor_verified'] is False
        ckey=(e['model'],e['retention'],e['protection_mode'],e['split_role']);coverage.setdefault(ckey,Counter());coverage[ckey]['scheduled']+=1;coverage[ckey]['feasible' if ok else 'infeasible']+=1
    assert seen=={(m,cid,ret,mode) for m in models for cid in cases for ret in cfg['retentions'] for mode in cfg['budget']['protected_modes']}
    table=read(d/'budget_coverage.json');assert len(table)==8
    for row in table:
        for role,count in [('engineering',4),('development',12)]:
            actual=coverage[(row['model'],row['retention'],row['protection_mode'],role)]
            assert row[role]=={k:actual[k] for k in ['scheduled','feasible','infeasible']} and actual['scheduled']==count
    guard=read(d/'CPU_guard_observations.json');assert all(guard[k]==0 for k in ['forbidden_read_attempts','network_attempts','subprocess_attempts','model_forward_calls','network_requests','weight_bytes_read','GPU_queries']) and guard['torch_loaded'] is False
    launch=read(Path(str(d)+'.launch.json'));assert launch['exit_code']==0 and not launch.get('watchdog_expired',False)
    for pid in [summary['pid'],launch['launcher_pid']]:assert not Path('/proc/'+str(pid)).exists()
    assert not any(x.split('.')[0] in ['torch','transformers','vllm'] for x in sys.modules)
    value=dict(status='passed',checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)),pinned_inputs_unchanged=len(cfg['inputs']),model_metadata_files=metadata_files,model_metadata_bytes=metadata_bytes,model_case_rows=32,full_native_variants=48,encodes_observed_in_pinned_runner=96,extra_verifier_encodes=0,Qwen_original14_exact=True,complete_system_coverage_checked=True,all_engineering_query_prefixes_equal=True,zero_offset_control_mappings=zero_controls,query_crossing_tokens_kept_in_suffix=query_crossings,independently_recomputed_budget_evaluations=128,coverage=table,predicted_bytes_per_slot=slots_bytes,model_or_tensor_verified=False,task_support_verified=False,sealed_encodes=0,weights_read=0,GPU_queries=0,network_requests=0,own_worker_and_launcher_exited=True)
    save(d/'independent_verification.json',value);print(json.dumps(value),flush=True)


if __name__=='__main__':main()
