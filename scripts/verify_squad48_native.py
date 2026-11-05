"""Independent stdlib replay of Qwen48 native offsets and half-budget plans."""
import sys
sys.dont_write_bytecode=True
import ast
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path


def read(p):return json.loads(p.read_text())
def rows(p):return list(map(json.loads,p.read_text().splitlines()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def h(b):return hashlib.sha256(b).hexdigest()


def main():
    r=Path(__file__).resolve().parent.parent;assert str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning'
    d=r/'results/20261030-squad48-native-preflight-v1';cfg=read(d/'proposal_snapshot.json');s=read(d/'summary.json')
    assert s['status']=='complete' and s['tokenizer_encodes']==96 and s['cases_completed']==48 and s['planned_cells']==144
    for name,w in read(d/'manifest.json').items():assert sha(d/name)==w,name
    for path,w in cfg['inputs'].items():assert sha(r/path)==w,path
    snap=read(d/'execution_snapshot.json');assert sha(d/'proposal_snapshot.json')==snap['proposal_sha256']
    assert sha(d/'source_runner.py')==snap['runner_sha256']==sha(r/cfg['runner'])
    assert sha(d/'source_validator.py')==snap['validator_sha256']==sha(Path(__file__))
    for path,w in snap['helper_sources'].items():assert sha(r/path)==w==sha(d/('source_'+Path(path).name))
    for node in ast.walk(ast.parse((d/'source_runner.py').read_text())):
        if isinstance(node,ast.ImportFrom) and node.module=='transformers':assert {x.name for x in node.names}=={'AutoTokenizer','AutoConfig'}
    parent=(r/cfg['selected']).parent
    for manifest in ['manifest.json','derived_manifest.json']:
        for name,w in read(parent/manifest).items():assert sha(parent/name)==w,name
    source=rows(r/cfg['selected']);oldplan=rows(r/cfg['planned_cells']);encoded=read(d/'tokenized_cases.json');variants=read(d/'native_variants.json');plan=rows(d/'planned_cells_with_budgets.jsonl')
    assert len(source)==len(encoded)==len(variants)==48 and len(oldplan)==len(plan)==144
    assert [x['case_id'] for x in source]==[x['case_id'] for x in encoded]==[x['case_id'] for x in variants]
    assert len({x['context_group_id'] for x in source})==48
    model=cfg['model'];directory=Path(model['path']);assert directory.name==model['revision']
    for name,w in model['metadata_sha256'].items():assert sha(directory/name)==w,name
    tc=read(directory/'tokenizer_config.json');ac=read(directory/'config.json');assert h(tc['chat_template'].encode())==model['chat_template_sha256']
    assert ac['num_hidden_layers']==28 and ac['num_key_value_heads']==4 and not ac['use_sliding_window']
    bytes_per=ac['num_hidden_layers']*2*ac['num_key_value_heads']*(ac['hidden_size']//ac['num_attention_heads'])*2;assert bytes_per==57344
    special=read(d/'special_token_map.json');by={};crossings=zeromaps=0
    for c,e,v in zip(source,encoded,variants):
        assert e['split_role']==c['split_role']=='sealed_descriptive_evaluation' and v['original_question']==c['question']
        for field in ['context_group_id','prompt_sha256','gold_sha256']:assert e[field]==c[field]
        system=c['prompt']['system'];user=c['prompt']['user'];header='<|im_start|>system\n'+system+'<|im_end|>\n';before=header+'<|im_start|>user\n';text=before+user+'<|im_end|>\n<|im_start|>assistant\n'
        assert v['rendered']==text and h(text.encode())==v['rendered_sha256']
        assert user[c['question_start_user_character']:]==c['question']
        ids=e['input_ids'];assert ids==v['native_tokenized_ids'] and 0<len(ids)<=2048 and all(type(x) is int and x>=0 for x in ids)
        raw=e['offsets'];eff=e['effective_offsets'];assert len(raw)==len(eff)==len(ids)
        mappings={x['token_index']:x for x in e['zero_offset_control_mappings']}
        for i,(pair,span) in enumerate(zip(raw,eff)):
            if pair==[0,0]:
                item=mappings[i];assert item['token_id']==ids[i] and special[item['literal']]==ids[i] and item['character_span']==span and text[span[0]:span[1]]==item['literal'];zeromaps+=1
            else:assert pair==span
            assert 0<=span[0]<span[1]<=len(text)
        q=len(before)+c['question_start_user_character'];assert e['question_character_start']==q and e['user_character_start']==len(before) and e['system_character_end']==len(header)
        cached=[i for i,(a,b) in enumerate(eff) if b<=q];n=len(cached);assert cached==list(range(n)) and n==e['prefix_tokens'] and e['suffix_tokens']==len(ids)-n
        crossing=[i for i,(a,b) in enumerate(eff) if a<q<b];assert crossing==e['crossing_query_token_indices'] and all(i>=n for i in crossing);crossings+=len(crossing)
        protected=[i for i,(a,b) in enumerate(eff) if a<len(header) and b>0];assert protected==e['header_ids'] and all(i<n for i in protected)
        assert all(any(eff[i][0]<=p<eff[i][1] for i in protected) for p in range(len(header)))
        assert h(json.dumps(ids[:n],separators=(',',':')).encode())==e['prefix_ids_sha256']
        assert e['actual_KV_tensor_verified'] is False and e['predicted_KV_bytes_per_slot']==57344
        for retention,slots in [('1',n),('1/2',n//2)]:
            b=e['requested_budgets'][retention];required=set(range(min(4,n)))|set(range(max(0,n-64),n));ok=len(required)<=slots and slots>0
            assert b['state']==('ok' if ok else 'infeasible_budget') and b['requested_slots']==b['effective_slots']==slots and b['required_positions']==sorted(required)
            assert b['required_union_count']==b['anchor_count']==len(required) and b['protected_unique_count']==b['extra_protected_slots']==0
            assert b['free_slots']==(slots-len(required) if ok else None) and b['protection_free'] is False
        by[c['case_id']]=e
    assert [(x['case_id'],x['condition_id']) for x in plan]==[(x['case_id'],x['condition_id']) for x in oldplan]
    assert len({(x['case_id'],x['condition_id']) for x in plan})==144
    count={name:Counter() for name in ['full','adapted_snapkv','uniform_random']}
    for old,new in zip(oldplan,plan):
        assert all(new[k]==v for k,v in old.items() if k!='budget_state')
        e=by[new['case_id']];ret='1' if new['condition_id']=='full' else '1/2';b=e['requested_budgets'][ret]
        assert new['budget']==b and new['budget_state']==b['state'] and new['predicted_prefix_KV_bytes']==b['requested_slots']*57344
        assert new['input_ids_sha256']==h(json.dumps(e['input_ids'],separators=(',',':')).encode()) and new['prefix_tokens']==e['prefix_tokens'] and new['suffix_tokens']==e['suffix_tokens']
        assert new['admission_state']==('blocked_budget' if b['state']=='infeasible_budget' else 'await_current_cohort_engineering_and_GPU_protocol')
        assert new['execution_state']=='not_run' and not new['model_called'] and all(x is None for x in new['metrics'].values())
        count[new['condition_id']]['scheduled']+=1;count[new['condition_id']]['feasible' if b['state']=='ok' else 'infeasible']+=1
    coverage=read(d/'coverage.json')
    for name,c in count.items():assert coverage['conditions'][name]==dict(scheduled=c['scheduled'],feasible=c['feasible'],infeasible=c['infeasible'],executed=0)
    assert count['adapted_snapkv']==count['uniform_random'] and count['full']['feasible']==48
    guard=read(d/'CPU_guard_observations.json');assert all(guard[k]==0 for k in ['forbidden_file_attempts','forbidden_model_imports','network_attempts','subprocess_attempts']) and guard['blocked_loopback_capability_probes']==1
    probe=read(d/'blocked_socket_probes.json');assert len(probe)==1 and probe[0]['address']==['::1',0] and probe[0]['operation_allowed'] is False
    assert sha(Path(cfg['blocked_probe_source']['path']))==cfg['blocked_probe_source']['sha256']
    launch=read(Path(str(d)+'.launch.json'));assert launch['exit_code']==0 and not launch.get('watchdog_expired',False)
    for pid in [s['pid'],launch['launcher_pid']]:assert not Path('/proc/'+str(pid)).exists()
    assert not any(x.split('.')[0] in ['torch','transformers','tokenizers','vllm'] for x in sys.modules)
    result=dict(status='passed',checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)),original48_identity_and_order_preserved=True,native_inputs=48,encodes_observed_in_pinned_runner=96,extra_verifier_encodes=0,query_boundary_and_header_coverage_checked=True,zero_offset_control_mappings=zeromaps,query_crossing_tokens_kept_in_suffix=crossings,predicted_bytes_per_slot=57344,all144_plan_budget_states_recomputed=True,conditions=coverage['conditions'],ranges=coverage['ranges'],source_input_files_rehashed=len(cfg['inputs']),model_metadata_files=6,all_cells_still_not_run=True,all_metrics_null=True,Full_or_engineering_pass=False,model_or_weight_loads=0,GPU_queries=0,network_requests=0,own_worker_and_launcher_exited=True,independent_scientific_confirmation=False)
    p=d/'independent_verification.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':main()
