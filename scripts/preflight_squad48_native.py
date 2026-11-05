"""Offline Qwen48 native inputs and unprotected half-budget plan checks."""
import os
os.environ.update(USE_TORCH='0',USE_TF='0',USE_FLAX='0',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',PYTHONDONTWRITEBYTECODE='1')
import sys
sys.dont_write_bytecode=True
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import signal
import time
import traceback

HELPER_PINS={'scripts/preflight_independent_evidence_frontends_v2.py':'2a356d6d8a37580b8ad66bb5c7f54e52b12592cb23cfd3b44b2670a52f95fcb3','scripts/reliability_system_core.py':'ea87bd0d1cff69014336cd59f61b4e77d2d0e43b6f679bf340d77c6f5c8ed546'}


def check(ok,message):
    if not ok:raise ValueError(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=True,allow_nan=False,indent=2)+'\n')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--proposal-sha256',required=True);ap.add_argument('--runner-sha256',required=True);ap.add_argument('--validator-sha256',required=True);a=ap.parse_args()
    r=Path(__file__).resolve().parent.parent;check(a.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning','server_CPU_only')
    raw=(r/'configs/squad48-native-preflight-v1.json').read_bytes();check(sha(raw)==a.proposal_sha256,'proposal_pin');cfg=json.loads(raw);out=r/cfg['run'];check(out.resolve().parent==(r/'results').resolve(),'run_boundary');out.mkdir(exist_ok=False)
    start=time.monotonic();active=None;state=dict(status='running',stage='pins',pid=os.getpid(),main_outputs=0,engineering_outputs=0,tokenizer_encodes=0,native_variants=0,cases_completed=0,planned_cells=0,model_forward_calls=0,GPU_queries=0,network_requests=0,weight_bytes_read=0)
    guard=dict(metadata_open_events=0,forbidden_file_attempts=0,forbidden_model_imports=0,network_attempts=0,subprocess_attempts=0,blocked_loopback_capability_probes=0);probes=[]
    def timeout(*args):raise TimeoutError('CPU90_second_cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(cfg['bounds']['wall_seconds'])
    try:
        save(out/'summary.json',state);(out/'proposal_snapshot.json').write_bytes(raw)
        check(os.environ.get('KV_NATIVE48_CPU_WATCHDOG')=='registered_120_seconds','outer_watchdog_required')
        check(sha(Path(__file__).read_bytes())==a.runner_sha256 and sha((r/cfg['validator']).read_bytes())==a.validator_sha256,'source_pin')
        (out/'source_runner.py').write_bytes(Path(__file__).read_bytes());(out/'source_validator.py').write_bytes((r/cfg['validator']).read_bytes())
        for rel,w in HELPER_PINS.items():
            b=(r/rel).read_bytes();check(sha(b)==w,'helper_source:'+rel);(out/('source_'+Path(rel).name)).write_bytes(b)
        dependency=Path(cfg['blocked_probe_source']['path']);check(sha(dependency.read_bytes())==cfg['blocked_probe_source']['sha256'] and importlib.metadata.version('urllib3')==cfg['blocked_probe_source']['urllib3_version'],'blocked_probe_source_version')
        model=cfg['model'];directory=Path(model['path']);check(directory.name==model['revision'],'model_revision');root=directory.resolve();blobroot=(directory.parent.parent/'blobs').resolve();allowed={(directory/name).resolve() for name in model['metadata_sha256']}
        def audit(event,args):
            if event=='import' and args[0].split('.')[0] in ['torch','tensorflow','jax','vllm']:
                guard['forbidden_model_imports']+=1;raise RuntimeError('heavy_model_import_forbidden')
            if event=='open' and isinstance(args[0],(str,bytes)):
                original=Path(os.fsdecode(args[0])).absolute();p=original.resolve()
                if original.is_relative_to(directory) or p.is_relative_to(root) or p.is_relative_to(blobroot):
                    if p not in allowed:guard['forbidden_file_attempts']+=1;raise RuntimeError('model_metadata_not_allowlisted')
                    guard['metadata_open_events']+=1
                if original.suffix in ['.safetensors','.pt','.pth','.bin'] or p.suffix in ['.safetensors','.pt','.pth','.bin'] or original.is_relative_to(r/'models'):
                    guard['forbidden_file_attempts']+=1;raise RuntimeError('weights_or_other_model_forbidden')
            if event in ['socket.connect','socket.connect_ex','socket.bind']:
                caller=sys._getframe(1)
                if event=='socket.bind' and args[1]==('::1',0) and caller.f_code.co_name=='_has_ipv6' and caller.f_code.co_filename==str(dependency):
                    guard['blocked_loopback_capability_probes']+=1;probes.append(dict(event=event,address=list(args[1]),source=str(dependency),caller=caller.f_code.co_name,operation_allowed=False));raise OSError('deny optionalloopbackcapability bind')
                guard['network_attempts']+=1;raise RuntimeError('network_forbidden')
            if event in ['subprocess.Popen','os.system']:guard['subprocess_attempts']+=1;raise RuntimeError('subprocess_forbidden')
        sys.addaudithook(audit)
        nbytes=0
        for rel,w in cfg['inputs'].items():
            b=(r/rel).read_bytes();check(sha(b)==w,'input_pin:'+rel);nbytes+=len(b)
        save(out/'input_manifest.json',dict(files=cfg['inputs'],bytes=nbytes,helper_sources=HELPER_PINS))
        parent=(r/cfg['selected']).parent
        for manifest in ['manifest.json','derived_manifest.json']:
            for name,w in json.loads((parent/manifest).read_text()).items():check(sha((parent/name).read_bytes())==w,'parent_manifest:'+name)
        check(json.loads((parent/'independent_verification.json').read_text())['status']=='passed','source_freeze_not_verified')
        meta={}
        for name,w in model['metadata_sha256'].items():
            b=(directory/name).read_bytes();check(sha(b)==w,'model_metadata:'+name);meta[name]=dict(sha256=w,bytes=len(b))
        tc=json.loads((directory/'tokenizer_config.json').read_text());check(sha(tc['chat_template'].encode())==model['chat_template_sha256'],'template_pin');save(out/'metadata_checks.json',dict(files=meta,template_sha256=model['chat_template_sha256']))
        versions={k:importlib.metadata.version(k) for k in cfg['versions']};check(versions==cfg['versions'],'package_versions')
        save(out/'execution_snapshot.json',dict(execution_enabled=True,runner_implemented=True,original_proposal_flags_unchanged=True,proposal_sha256=sha(raw),runner_sha256=a.runner_sha256,validator_sha256=a.validator_sha256,helper_sources=HELPER_PINS,versions=versions,python=sys.version,environment={k:os.environ[k] for k in cfg['environment']},scope='Native48CPU only,no model actions'))
        from reliability_system_core import budget_plan,kv_layout
        from preflight_independent_evidence_frontends_v2 import effective_offsets
        from transformers import AutoTokenizer,AutoConfig
        ac=AutoConfig.from_pretrained(str(directory),local_files_only=True,trust_remote_code=False)
        check(ac.model_type=='qwen2' and ac.num_hidden_layers==28 and ac.num_key_value_heads==4 and ac.num_attention_heads==28 and ac.hidden_size//ac.num_attention_heads==128 and not ac.use_sliding_window and set(ac.layer_types)=={'full_attention'},'Qwen_layout_changed')
        desc=kv_layout([dict(attention_type='full_attention',batch=1,key=dict(heads=4,dimension=128,element_bytes=2),value=dict(heads=4,dimension=128,element_bytes=2)) for _ in range(28)]);check(desc['bytes_per_prefix_slot']==57344,'layout_bytes');save(out/'layout_prediction.json',desc)
        tok=AutoTokenizer.from_pretrained(str(directory),local_files_only=True,trust_remote_code=False,use_fast=True);check(tok.is_fast,'fast_tokenizer_required');specials={literal:tok.convert_tokens_to_ids(literal) for literal in tok.all_special_tokens};save(out/'special_token_map.json',specials)
        selected=[json.loads(x) for x in (r/cfg['selected']).read_text().splitlines()];plan=[json.loads(x) for x in (r/cfg['planned_cells']).read_text().splitlines()];check(len(selected)==len({c['case_id'] for c in selected})==48 and len(plan)==144 and all(c['split_role']=='sealed_descriptive_evaluation' for c in selected),'fixed48_identity')
        encoded=[];variants=[];updated=[];by={};state['stage']='native48'
        for case in selected:
            active=case['case_id'];prompt=case['prompt'];qchar_user=case['question_start_user_character'];check(prompt['user'][qchar_user:]==case['question'],'stored_question_boundary')
            messages=[dict(role='system',content=prompt['system']),dict(role='user',content=prompt['user'])];text=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            header='<|im_start|>system\n'+prompt['system']+'<|im_end|>\n';user_start=len(header)+len('<|im_start|>user\n');check(text==header+'<|im_start|>user\n'+prompt['user']+'<|im_end|>\n<|im_start|>assistant\n','Qwen_native_render_changed')
            enc=tok(text,add_special_tokens=False,return_offsets_mapping=True);state['tokenizer_encodes']+=1;native=tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True);state['tokenizer_encodes']+=1
            ids=enc['input_ids'];check(ids==native and len(ids)<=cfg['bounds']['max_input_tokens'],'native_encoding_or_input_cap');offsets=[list(v) for v in enc['offset_mapping']];effective,mappings=effective_offsets(text,ids,offsets,specials)
            qchar=user_start+qchar_user;n=next(i for i,(a,b) in enumerate(effective) if b>qchar);check(0<n<len(ids) and all(b<=qchar for a,b in effective[:n]) and all(b>qchar for a,b in effective[n:]),'query_in_prefix_or_noncontiguous_boundary')
            protected=[i for i,(a,b) in enumerate(effective) if a<len(header) and b>0];coverage={j for i in protected for j in range(max(0,effective[i][0]),min(len(header),effective[i][1]))};check(coverage==set(range(len(header))) and max(protected)<n,'incomplete_header_coverage')
            crossing=[i for i,(a,b) in enumerate(effective) if a<qchar<b];check(all(i>=n for i in crossing),'query_crossing_token_cached')
            budgets={ret:budget_plan(n,ret,[],cfg['budget']['sink'],cfg['budget']['recent']) for ret in ['1','1/2']}
            variant=dict(case_id=case['case_id'],rendered=text,rendered_sha256=sha(text.encode()),native_tokenized_ids=native,original_question=case['question']);variants.append(variant)
            row=dict(case_id=case['case_id'],split_role=case['split_role'],context_group_id=case['context_group_id'],prompt_sha256=case['prompt_sha256'],gold_sha256=case['gold_sha256'],input_ids=ids,offsets=offsets,effective_offsets=effective,zero_offset_control_mappings=mappings,prefix_tokens=n,suffix_tokens=len(ids)-n,user_character_start=user_start,question_character_start=qchar,system_character_end=len(header),header_ids=protected,crossing_query_token_indices=crossing,prefix_ids_sha256=sha(json.dumps(ids[:n],separators=(',',':')).encode()),predicted_KV_bytes_per_slot=57344,actual_KV_tensor_verified=False,requested_budgets=budgets)
            encoded.append(row);by[row['case_id']]=row;state['cases_completed']+=1;state['native_variants']+=1
            save(out/'tokenized_cases.json',encoded);save(out/'native_variants.json',variants);save(out/'summary.json',state);active=None
        for old in plan:
            row=by[old['case_id']];ret='1' if old['condition_id']=='full' else '1/2';budget=row['requested_budgets'][ret]
            check(old['prompt_sha256']==row['prompt_sha256'] and old['gold_sha256']==row['gold_sha256'] and old['context_group_id']==row['context_group_id'],'plan_pair_identity_changed')
            new=dict(old);new.update(budget=budget,budget_state=budget['state'],predicted_prefix_KV_bytes=budget['requested_slots']*57344,input_ids_sha256=sha(json.dumps(row['input_ids'],separators=(',',':')).encode()),prefix_tokens=row['prefix_tokens'],suffix_tokens=row['suffix_tokens'],actual_KV_tensor_verified=False,admission_state='blocked_budget' if budget['state']=='infeasible_budget' else 'await_current_cohort_engineering_and_GPU_protocol')
            check(new['execution_state']=='not_run' and not new['model_called'] and all(v is None for v in new['metrics'].values()),'CPU_accidentally_scored');updated.append(new)
        (out/'planned_cells_with_budgets.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=True)+'\n' for x in updated));state['planned_cells']=len(updated)
        check(state['tokenizer_encodes']==96 and len(encoded)==48 and len(updated)==144,'expected48_coverage')
        check(not any(n.split('.')[0] in ['torch','tensorflow','jax','vllm'] for n in sys.modules),'heavy_library_loaded')
        check(all(guard[k]==0 for k in ['forbidden_file_attempts','forbidden_model_imports','network_attempts','subprocess_attempts']) and guard['blocked_loopback_capability_probes']==1,'CPU_boundary_guard')
        save(out/'blocked_socket_probes.json',probes);save(out/'CPU_guard_observations.json',guard)
        coverage={name:dict(scheduled=48,feasible=sum(x['budget_state']=='ok' for x in updated if x['condition_id']==name),infeasible=sum(x['budget_state']=='infeasible_budget' for x in updated if x['condition_id']==name),executed=0) for name in ['full','adapted_snapkv','uniform_random']}
        ranges=dict(input_tokens=[min(len(x['input_ids']) for x in encoded),max(len(x['input_ids']) for x in encoded)],prefix_tokens=[min(x['prefix_tokens'] for x in encoded),max(x['prefix_tokens'] for x in encoded)],suffix_tokens=[min(x['suffix_tokens'] for x in encoded),max(x['suffix_tokens'] for x in encoded)],header_token_counts=sorted({len(x['header_ids']) for x in encoded}),half_slots=[min(x['requested_budgets']['1/2']['requested_slots'] for x in encoded),max(x['requested_budgets']['1/2']['requested_slots'] for x in encoded)])
        save(out/'coverage.json',dict(conditions=coverage,ranges=ranges,zero_offset_control_mappings=sum(len(x['zero_offset_control_mappings']) for x in encoded),crossing_query_tokens=sum(len(x['crossing_query_token_indices']) for x in encoded),all_source_rows_retained=True,Full_support=False,engineering_pass=False,model_inference_enabled=False))
        (out/'report.md').write_text('# Qwen48 native CPU preflight\n\n48originalnative inputs/96encodes verified;144plans retainbudgetstates,allnot_run/metricsnull. Predicted57344K+Vbytesperslot;no tensorsorFull/engineeringpassed.\n\n'+json.dumps(coverage,indent=2)+'\n')
        for rel,w in {**cfg['inputs'],**HELPER_PINS}.items():check(sha((r/rel).read_bytes())==w,'input_changed:'+rel)
        state.update(status='complete',stage='complete',all48_source_cases_retained=True,half_budget_infeasible_cases=coverage['adapted_snapkv']['infeasible'],conditions=coverage,ranges=ranges,Full_support=False,engineering_gate=False,scientific_confirmation=False)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc),active_case=active);(out/'failure.txt').write_text(traceback.format_exc());save(out/'CPU_guard_at_stop.json',guard)
    finally:
        signal.alarm(0);state['elapsed_seconds']=time.monotonic()-start;save(out/'summary.json',state);files=[p for p in out.iterdir() if p.is_file()]
        if len(files)>=cfg['bounds']['max_archive_files'] or sum(p.stat().st_size for p in files)>=cfg['bounds']['max_archive_bytes']:state.update(status='failed',archive_cap_exceeded=True);save(out/'summary.json',state)
        save(out/'manifest.json',{p.name:sha(p.read_bytes()) for p in files});print(json.dumps(state),flush=True)
    return 0 if state['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
