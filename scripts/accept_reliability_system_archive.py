"""Bounded server-only acceptance of modular reports on frozen scalar archives."""
import sys
sys.dont_write_bytecode=True
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback
from reliability_system_core import require, kv_layout, summarize
from reliability_system_adapters import trec, answer_format, archive_plan, hash_json
from reliability_system_acceptance import acceptance

PROPOSAL_SHA='8988fd99ee706891ac678fd057b6a6c3c0eae6cf383a14a8c9f1c3456c633023'


def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,j):p.write_text(json.dumps(j,ensure_ascii=True,allow_nan=False,indent=2)+'\n')


def verify_trec(report,old):
    for method,c in report['conditions'].items():
        prior=old['methods'][method]
        require(c['execution']==prior['execution'],'TREC execution mismatch')
        for name in ['task','constraint']:
            new=c['metrics'][name];p=prior['metrics'][name]
            for k in ['pass_count','evaluated_count','unavailable_count']:
                require(new[k]==p[k],'TREC count mismatch:'+k)
            if method!='full':
                require(new['transitions']==p['transitions'],'TREC transitions')
                for nk,pk in [('available_Full_pass_count','available_full_pass_count'),('eligible_Full_pass_pair_count','eligible_full_pass_pair_count'),('unassessed_Full_pass_count','unassessed_full_pass_count')]:
                    require(new[nk]==p[pk],'TREC denominator')


def verify_qa(report,old):
    for method,c in report['conditions'].items():
        p=old['conditions'][method];exe=c['execution']
        for nk,pk in [('scheduled','scheduled'),('ok','ok'),('truncated','truncated'),('error','errors'),('not_run','not_run')]:require(exe[nk]==p[pk],'QA execution')
        for name,count,paired in [('task','task_em','paired_em'),('constraint','format','paired_format')]:
            v=c['metrics'][name];require(v['pass_count']==p[count],'QA count')
            if method!='full':
                q=p[paired];require(v['transitions']=={k:q['transitions'][k] for k in ['C2C','C2W','W2C','W2W']},'QA transition')
                require(v['unavailable_pair_count']==q['transitions']['N/A'],'QA unavailable')
                require(v['all_Full_pass_damage_bounds']==q['all_Full_correct_damage_bounds'],'QA bounds')
                require(v['unassessed_Full_pass_count']==q['unassessed_Full_correct'],'QA unknown')
        f=c['metrics']['task_f1'];require(f['evaluated_count']==p['f1_denominator'] and abs(f['mean']-p['f1_mean'])<1e-12,'QA F1')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');args=ap.parse_args()
    r=Path(__file__).resolve().parent.parent
    require(args.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning','server explicit execute')
    raw=(r/'configs/reliability-system-archive-acceptance-v1.json').read_bytes();require(sha(raw)==PROPOSAL_SHA,'proposal pin')
    cfg=json.loads(raw);out=r/cfg['run'];require(out.resolve().parent==(r/'results').resolve(),'run boundary');out.mkdir(exist_ok=False)
    started=time.monotonic();s=dict(status='running',stage='verify_inputs',pid=os.getpid(),main_outputs=0,engineering_outputs=0,software_cases_passed=0,cohorts_completed=0)
    def timeout(*a):raise TimeoutError('60_second_cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(cfg['bounds']['wall_seconds'])
    try:
        save(out/'summary.json',s);(out/'proposal_snapshot.json').write_bytes(raw)
        sourcehash={};allowed={'sys','argparse','ast','hashlib','json','os','pathlib','signal','time','traceback','collections','fractions','math','copy','reliability_system_core','reliability_system_adapters','reliability_system_acceptance'}
        for name in ['reliability_system_core.py','reliability_system_adapters.py','reliability_system_acceptance.py','accept_reliability_system_archive.py']:
            b=(r/'scripts'/name).read_bytes();tree=ast.parse(b)
            for n in ast.walk(tree):
                mods=[x.name.split('.')[0] for x in n.names] if isinstance(n,ast.Import) else ([n.module.split('.')[0]] if isinstance(n,ast.ImportFrom) and n.module else [])
                require(set(mods)<=allowed,'unexpected import')
                require(not(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ['exec','eval','compile','__import__']),'dynamic execution')
            sourcehash[name]=sha(b);(out/('source_'+name)).write_bytes(b)
        save(out/'execution_snapshot.json',dict(execution_enabled=True,runner_implemented=True,proposal_sha256=PROPOSAL_SHA,source_sha256=sourcehash,python=sys.version,model_loading=False,network=False,gpu=False,bounds=cfg['bounds']))
        bodies={};byte_count=line_count=0
        for path,expected in cfg['inputs'].items():
            b=(r/path).read_bytes();require(sha(b)==expected,'input pin:'+path);bodies[path]=b;byte_count+=len(b)
            if path.endswith('.jsonl'):line_count+=len(b.splitlines())
        require(byte_count<=cfg['bounds']['input_bytes_max'] and line_count<=cfg['bounds']['input_jsonl_rows_max'],'input cap')
        save(out/'input_manifest.json',dict(files=cfg['inputs'],bytes=byte_count,jsonl_rows=line_count))
        fixtures=[];save(out/'software_acceptance.json',fixtures)
        s['stage']='software_acceptance'
        for i in range(16):
            v=acceptance(i);require(v['id']==cfg['acceptance_ids'][i],'acceptance identity');fixtures.append(v);s['software_cases_passed']+=1;save(out/'software_acceptance.json',fixtures)
        def readj(path):return json.loads(bodies[path])
        def readrows(path):return [json.loads(x) for x in bodies[path].splitlines()]
        normalized=readrows('results/20261030-reliability-report-replay-v2/normalized_records.jsonl')
        oldtrec=readj('results/20261030-reliability-report-replay-v2/report.json')
        fullsnap=readj('results/20261030-answer-format-full-v1/execution_snapshot.json');compsnap=readj('results/20261030-answer-format-compression-v1/execution_snapshot.json')
        for k in ['model_path','decode_actual','runtime_full_layers','kv_heads','head_dim','kv_dtype','bytes_per_token']:
            require(fullsnap[k]==compsnap[k],'QA runtime identity:'+k)
        layout=[dict(attention_type='full_attention',batch=1,key=dict(heads=fullsnap['kv_heads'],dimension=fullsnap['head_dim'],element_bytes=2),value=dict(heads=fullsnap['kv_heads'],dimension=fullsnap['head_dim'],element_bytes=2)) for _ in range(fullsnap['runtime_full_layers'])]
        descriptor=kv_layout(layout);require(descriptor['bytes_per_prefix_slot']==fullsnap['bytes_per_token'],'QA layout byte agreement');save(out/'layout_descriptor_check.json',descriptor)
        qa_comparison=hash_json({k:fullsnap[k] for k in ['model_path','decode_actual','runtime_full_layers','kv_heads','head_dim','kv_dtype']})
        qa_paths=['results/20261030-answer-format-full-v1/generations.jsonl','results/20261030-answer-format-compression-v1/generations.jsonl']
        qa=[]
        for path in qa_paths:
            for line,row in enumerate(readrows(path),1):qa.append(answer_format(row,'used_squad_json_development16',qa_comparison,dict(path=path,line=line,sha256=cfg['inputs'][path])))
        sourcecases={x['case_id']:x for x in readrows('results/20261030-answer-format-task-preflight-v1/selected_cases.jsonl')}
        reports=[];allrows=[];plans=[]
        s['stage']='three_cohort_replay'
        for item in cfg['cohorts']:
            cohort=item['id']
            if cohort.startswith('legacy_trec'):
                adapted=[trec(x,hash_json(dict(cohort=cohort,comparison_scope='archived_prior_runtime_identity_checks_not_recomputed',evidence=cfg['inputs']['results/20261030-reliability-report-replay-v2/report.json']))) for x in normalized if x['cohort_id']==cohort]
                groups=None
            else:
                adapted=qa;groups=[sourcecases[c]['context_group_id'] for c in sorted({x['case_id'] for x in qa})]
            plan=archive_plan(cohort,adapted,item['role'],groups);require(len(plan['case_ids'])==item['n'],'cohort count')
            report=summarize(plan,adapted)
            if cohort.startswith('legacy_trec'):
                old=next(c for c in oldtrec['cohorts'] if c['cohort_id']==cohort)['profiles']['strict_complete_pair_preview'];verify_trec(report,old)
            else:verify_qa(report,readj('results/20261030-answer-format-analysis-v1/report.json'))
            require(report['conditions']['full']['metrics']['task']['pass_count']==item['full_task'] and report['conditions']['full']['metrics']['constraint']['pass_count']==item['full_constraint'],'frozen Full expected')
            reports.append(report);plans.append(plan);allrows.extend(adapted);s['cohorts_completed']+=1;save(out/'summary.json',s)
        require(len(allrows)==cfg['bounds']['output_records']==290,'normalized record count')
        (out/'normalized_records.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=True,allow_nan=False)+'\n' for x in allrows))
        save(out/'cohort_plans.json',plans);save(out/'report.json',dict(version='system_modular_v1',cohorts=reports,independent_confirmation=False))
        text=['# Modular system archive acceptance','','Historical scalar replay only; no new model results or independent confirmation.','','| Cohort | Cases | Cells | Full task | Full constraint |','| --- | --- | --- | --- | --- |']
        for v in reports:
            f=v['conditions']['full']['metrics'];text.append(f"| {v['cohort_id']} | {v['case_count']} | {len(v['cells'])} | {f['task']['pass_count']} | {f['constraint']['pass_count']} |")
        text+=['','All prior strict counts, transitions, eligible/unassessed denominators and QA F1 matched. One truncated QA random result remains unavailable. Costs without observations remain unknown.','', 'Descriptor-only budget validation supports varying layer/head/dtype shapes; no new model tensor or performance validation.']
        (out/'report.md').write_text('\n'.join(text)+'\n')
        for path,expected in cfg['inputs'].items():require(sha((r/path).read_bytes())==expected,'input changed')
        require(not any(x.split('.')[0] in ['torch','transformers','vllm'] for x in sys.modules),'unexpected model library')
        s.update(status='complete',stage='complete',input_files=len(bodies),input_bytes=byte_count,input_jsonl_rows=line_count,normalized_records=290,all_archived_strict_reports_matched=True,model_libraries_loaded=False,gpu_queried=False,independent_confirmation=False)
    except BaseException as exc:
        s.update(status='failed',error=repr(exc));(out/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0);s['elapsed_seconds']=time.monotonic()-started;save(out/'summary.json',s)
        files=[p for p in out.iterdir() if p.is_file()];require(len(files)<cfg['bounds']['archive_files_max'] and sum(p.stat().st_size for p in files)<cfg['bounds']['archive_bytes_max'],'archive cap')
        save(out/'manifest.json',{p.name:sha(p.read_bytes()) for p in files});print(json.dumps(s),flush=True)
    return 0 if s['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
