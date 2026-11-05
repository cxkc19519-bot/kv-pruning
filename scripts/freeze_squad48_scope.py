"""CPU-only revalidation of original SQuAD48 identities and planned cells."""
import os
os.environ.update(USE_TORCH='0',USE_TF='0',USE_FLAX='0',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1')
import sys
sys.dont_write_bytecode=True
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import signal
import time
import traceback


def require(value,message):
    if not value:raise ValueError(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=True,allow_nan=False,indent=2)+'\n')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--proposal-sha256',required=True);ap.add_argument('--runner-sha256',required=True);ap.add_argument('--validator-sha256',required=True);a=ap.parse_args()
    r=Path(__file__).resolve().parent.parent;require(a.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning','server_CPU_only')
    raw=(r/'configs/squad48-scope-freeze-v1.json').read_bytes();require(sha(raw)==a.proposal_sha256,'proposal_pin');cfg=json.loads(raw);out=r/cfg['run']
    require(out.resolve().parent==(r/'results').resolve(),'output_boundary');out.mkdir(exist_ok=False)
    started=time.monotonic();s=dict(status='running',stage='pins',pid=os.getpid(),main_outputs=0,engineering_outputs=0,tokenizer_encodes=0,model_forward_calls=0,GPU_queries=0,network_requests=0,weight_bytes_read=0)
    bounds=cfg['resource_bounds'];guard=dict(forbidden_library_imports=0,forbidden_model_file_opens=0,network_attempts=0,subprocess_attempts=0)
    def timeout(*args):raise TimeoutError('CPU90_second_cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(bounds['wall_seconds'])
    try:
        save(out/'summary.json',s);(out/'proposal_snapshot.json').write_bytes(raw)
        require(os.environ.get('KV_SCOPE_FREEZE_WATCHDOG')=='registered_120_seconds','outer_watchdog_required')
        require(sha(Path(__file__).read_bytes())==a.runner_sha256,'runner_pin')
        require(sha((r/cfg['independent_verifier']).read_bytes())==a.validator_sha256,'validator_pin')
        (out/'source_runner.py').write_bytes(Path(__file__).read_bytes());(out/'source_validator.py').write_bytes((r/cfg['independent_verifier']).read_bytes())
        def audit(event,args):
            if event=='import' and args[0].split('.')[0] in ['torch','transformers','tokenizers','tensorflow','jax','vllm']:
                guard['forbidden_library_imports']+=1;raise RuntimeError('model_or_tokenizer_import_forbidden')
            if event=='open' and isinstance(args[0],(str,bytes)):
                p=Path(os.fsdecode(args[0])).absolute();resolved=p.resolve()
                if p.suffix in ['.safetensors','.pt','.pth','.bin'] or resolved.suffix in ['.safetensors','.pt','.pth','.bin'] or p.is_relative_to(r/'models') or '/huggingface/hub/' in str(p):
                    guard['forbidden_model_file_opens']+=1;raise RuntimeError('model_file_read_forbidden')
            if event in ['socket.connect','socket.connect_ex','socket.bind']:
                guard['network_attempts']+=1;raise RuntimeError('network_forbidden')
            if event in ['subprocess.Popen','os.system']:
                guard['subprocess_attempts']+=1;raise RuntimeError('subprocess_forbidden')
        sys.addaudithook(audit)
        inputmap=dict(cfg['inputs']);inputmap[cfg['historical_source']['path']]=cfg['historical_source']['sha256'];totalbytes=0
        for path,w in inputmap.items():
            b=(r/path).read_bytes();require(sha(b)==w,'input_pin:'+path);totalbytes+=len(b)
        sourcebytes=(r/cfg['train_source']['path']).stat().st_size+(r/cfg['historical_source']['path']).stat().st_size
        require(sourcebytes<=bounds['max_source_bytes'],'raw_source_byte_cap');save(out/'input_manifest.json',dict(files=inputmap,total_input_bytes=totalbytes,raw_source_bytes=sourcebytes))
        parent=r/Path(cfg['parent_split']).parent;parent_manifest=json.loads((parent/'manifest.json').read_text())
        for path in inputmap:
            p=r/path
            if p.parent==parent and p.name in parent_manifest:require(sha(p.read_bytes())==parent_manifest[p.name],'parent_manifest:'+p.name)
        require(sha((r/'scripts/answer_format_task.py').read_bytes())==cfg['inputs'][str((parent/'source_answer_format_task.py').relative_to(r))],'task_library_pin')
        (out/'source_task_library.py').write_bytes((r/'scripts/answer_format_task.py').read_bytes())
        save(out/'execution_snapshot.json',dict(proposal_sha256=sha(raw),runner_sha256=a.runner_sha256,validator_sha256=a.validator_sha256,execution_enabled=True,runner_implemented=True,original_proposal_flags_unchanged=True,python=sys.version,mode='CPUsource_components_and_plans_only',model_inference_allowed=False))
        from answer_format_task import strict_json,validate_dataset,article_components,normalized_title,normalized_paragraph
        s['stage']='source_integrity';save(out/'summary.json',s)
        body=(r/cfg['train_source']['path']).read_bytes();require(len(body)==cfg['train_source']['bytes'],'train_byte_count')
        train=strict_json(body.decode());old=strict_json((r/cfg['historical_source']['path']).read_text());counts=validate_dataset(train);save(out/'dataset_revalidation.json',counts)
        identity=json.loads((parent/'source_identity.json').read_text());require(identity['sha256']==sha(body) and identity['git_blob_sha1']==hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest(),'original_git_blob_identity')
        pp=json.loads((parent/'proposal_snapshot.json').read_text());ps=json.loads((r/cfg['parent_split']).read_text());original=[json.loads(x) for x in (r/cfg['selection']['source']).read_text().splitlines()]
        require(Counter(c['split_role'] for c in original)=={'engineering':4,'development':12,'sealed_descriptive_evaluation':48},'original64_roles')
        require(len({c['case_id'] for c in original})==len({c['context_group_id'] for c in original})==64,'duplicate_original_identity')
        oldtitles={normalized_title(a['title']) for a in old['data']};oldcontexts={normalized_paragraph(p['context']) for a in old['data'] for p in a['paragraphs']}
        components,links=article_components(train['data']);eligible=[];excluded=[]
        for g in components:
            overlap=any(normalized_title(train['data'][i]['title']) in oldtitles or any(normalized_paragraph(p['context']) in oldcontexts for p in train['data'][i]['paragraphs']) for i in g['article_indices'])
            g['rank_sha256']=sha(pp['selection_seed'].encode()+g['component_id'].encode());(excluded if overlap else eligible).append(g)
        eligible.sort(key=lambda g:(g['rank_sha256'],g['component_id']))
        require(len(components)==ps['total_components']==442 and len(eligible)==ps['eligible_components'] and excluded==ps['excluded_historical_groups'],'component_or_historical_exclusion_changed')
        require(eligible[:64]==ps['selected_components'] and links==ps['source_links'] and len(old['data'])==ps['historical_article_count'],'original_component_selection_changed')
        roles=[role for role,n in pp['target'].items() for _ in range(n)];system=original[0]['prompt']['system'];rebuilt=[];sourcechecks=[]
        for g,role,prior in zip(eligible[:64],roles,original):
            options=[(sha(q['id'].encode()),q['id'],ai,pi,q) for ai in g['article_indices'] for pi,p in enumerate(train['data'][ai]['paragraphs']) for q in p['qas']]
            _,_,ai,pi,q=min(options,key=lambda x:x[:4]);context=train['data'][ai]['paragraphs'][pi]['context'];prefix='Passage:\n'+context+'\n\nQuestion:\n';prompt=dict(system=system,user=prefix+q['question'])
            row=dict(case_id=q['id'],task_id='squad_train_json_v1',split_role=role,context_group_id=g['component_id'],source_article_index=ai,source_paragraph_index=pi,source_title=train['data'][ai]['title'],context=context,question=q['question'],answers=q['answers'],prompt=prompt,prompt_sha256=sha(json.dumps(prompt,ensure_ascii=False,separators=(',',':')).encode()),gold_sha256=sha(json.dumps(q['answers'],ensure_ascii=False,separators=(',',':')).encode()),question_start_user_character=len(prefix),context_words=len(context.split()),provisional_cross_task_overlap=True)
            require(row==prior,'original_case_or_prompt_changed:'+prior['case_id']);rebuilt.append(row)
            sourcechecks.append(dict(case_id=row['case_id'],role=role,group_id=g['component_id'],article_index=ai,paragraph_index=pi,original_selection_exact=True,all_answer_slices_exact=all(context[a['answer_start']:a['answer_start']+len(a['text'])]==a['text'] for a in q['answers'])))
        s['stage']='freeze_exact48';save(out/'summary.json',s)
        selected=[c for c in rebuilt if c['split_role']==cfg['selection']['role']];require(len(selected)==48,'reserved48_count')
        (out/'selected48.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=True)+'\n' for c in selected))
        save(out/'source_case_checks.json',sourcechecks);save(out/'component_revalidation.json',dict(all_components=components,eligible_count=len(eligible),excluded=excluded,original_selected64_components=eligible[:64],source_links=links,entire_historical_article_count=len(old['data']),historical_title_or_paragraph_overlap=0,roles=dict(Counter(roles)),exact_original_selection=True,independent_unit='SQuADarticle_or_exact_title_context_component',semantic_near_duplicate_or_pretraining_clean_guarantee=False))
        contract=json.loads((r/cfg['decision_contract']).read_text());conditions=contract['candidate_conditions'];require([c['id'] for c in conditions]==['full','adapted_snapkv','uniform_random'],'fixed_three_conditions')
        plan=[]
        for c in selected:
            for condition in conditions:
                plan.append(dict(cohort_id='Qwen_SQuAD_reserved48_descriptive_v1',case_id=c['case_id'],context_group_id=c['context_group_id'],role='sealed_descriptive_evaluation',condition_id=condition['id'],condition_contract=condition,prompt_sha256=c['prompt_sha256'],gold_sha256=c['gold_sha256'],plan_state='planned',execution_state='not_run',budget_state='not_checked',engineering_evidence_state='not_registered_for_new_cohort',model_called=False,metrics=dict(task_EM=None,task_F1=None,format=None,joint=None),reason='await_native_frontend_budget_and_separate_GPU_protocol'))
        require(len(plan)==len({(x['case_id'],x['condition_id']) for x in plan})==144,'all144_planned_identity')
        (out/'planned_cells.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=True)+'\n' for x in plan))
        save(out/'scope_manifest.json',dict(scope='QwenSQuAD-only reserved48,not completion ofoldcross-taskstudy',source_selection_sha256=cfg['inputs'][cfg['selection']['source']],groups=48,question_ids=[c['case_id'] for c in selected],context_groups=[c['context_group_id'] for c in selected],conditions=conditions,main_answers_ceiling=144,engineering_answers_resource_ceiling=14,Full_support=False,engineering_pass=False,tokenizer_checked=False,model_inference_enabled=False,oldcross_task_BoolQ_audit_complete=False,old_QA_gate=False,Mistral_currentadaptation_support=False))
        require(not any(x.split('.')[0] in ['torch','transformers','tokenizers','tensorflow','jax','vllm'] for x in sys.modules),'model_library_imported')
        require(not any(guard.values()),'CPU_guard_failed');save(out/'CPU_guard_observations.json',guard)
        for p,h in inputmap.items():require(sha((r/p).read_bytes())==h,'input_changed:'+p)
        (out/'report.md').write_text('# Exact48 source/group freeze\n\nAll442train components rebuilt;original64case/role/prompt/gold identities unchanged.48reserved groups matchoriginalselection,disjointfrom4engineering12DEV andentirehistorical48article sources.144cells planned only;no tokenizer,budget feasibility,engineering ormodel support inferred.\n')
        s.update(status='complete',stage='complete',source_files_rehashed=2,train_articles=442,train_questions=counts['questions'],all_source_answer_spans_exact=counts['answer_spans'],original_cases_rebuilt=64,reserved_groups=48,planned_cells=144,exact_original_selection=True,old_historical_article_count=len(old['data']),source_input_bytes=sourcebytes,independent_scientific_confirmation=False)
    except BaseException as exc:
        s.update(status='failed',error=repr(exc));(out/'failure.txt').write_text(traceback.format_exc());save(out/'CPU_guard_at_stop.json',guard)
    finally:
        signal.alarm(0);s['elapsed_seconds']=time.monotonic()-started;save(out/'summary.json',s);files=[p for p in out.iterdir() if p.is_file()]
        if len(files)>=bounds['max_archive_files'] or sum(p.stat().st_size for p in files)>=bounds['max_archive_bytes']:s.update(status='failed',archive_bounds_exceeded=True);save(out/'summary.json',s)
        save(out/'manifest.json',{p.name:sha(p.read_bytes()) for p in files});print(json.dumps(s),flush=True)
    return 0 if s['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
