"""Use generic scalar core on prospectively frozen new-source DEV records."""
import sys
sys.dont_write_bytecode=True
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
from reliability_system_core import SCHEMA,measure,metric,summarize,require
from reliability_system_adapters import hash_json


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=True,allow_nan=False,indent=2)+'\n')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--proposal',required=True);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    r=Path(__file__).resolve().parent.parent;require(a.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning','server execute')
    raw=(r/a.proposal).read_bytes();cfg=json.loads(raw);o=r/cfg['run'];o.mkdir(exist_ok=False)
    start=time.monotonic();s=dict(status='running',pid=os.getpid(),main_outputs=0,engineering_outputs=0)
    try:
        (o/'proposal_snapshot.json').write_bytes(raw);(o/'source.py').write_bytes(Path(__file__).read_bytes())
        for f,v in cfg['inputs'].items():require(sha(r/f)==v,'input:'+f)
        for name in ['reliability_system_core.py','reliability_system_adapters.py']:(o/('source_'+name)).write_bytes((r/'scripts'/name).read_bytes())
        for key in ['full','compression']:
            out=r/cfg[key]
            for f,v in json.loads((out/'manifest.json').read_text()).items():require(sha(out/f)==v,'manifest:'+key+f)
        tokens=json.loads((r/cfg['tokenized']).read_text());cases={c['case_id']:c for c in map(json.loads,(r/cfg['cases']).read_text().splitlines()) if c['split_role']=='development'}
        tokmap={x['case_id']:x for x in tokens};require(len(cases)==12,'frozen12')
        fs=json.loads((r/cfg['full']/'execution_snapshot.json').read_text());cs=json.loads((r/cfg['compression']/'execution_snapshot.json').read_text())
        for k in ['model_path','decode_actual','runtime_full_layers','kv_heads','head_dim','kv_dtype']:require(fs[k]==cs[k],'comparison:'+k)
        comp=hash_json({k:fs[k] for k in ['model_path','decode_actual','runtime_full_layers','kv_heads','head_dim','kv_dtype']})
        rows=[];rawrows=[]
        for key in ['full','compression']:
            p=r/cfg[key]/'generations.jsonl'
            for rawrow in map(json.loads,p.read_text().splitlines()):
                cid=rawrow['case_id'];require(cid in cases,'no sealed inference')
                state=rawrow['status'];ok=state=='ok';c=cases[cid];rawrows.append(rawrow)
                m=rawrow.get('metrics',{})
                metrics=dict(task=metric(m.get('em'),'squad_v11_bidaf_pinned_em_v1',reason=m.get('reason','not_executed')),
                    constraint=metric(m.get('format'),'json_answer_format_v1',reason='not_executed'),
                    f1=metric(m.get('f1'),'squad_v11_bidaf_pinned_f1_v1','unit_interval',m.get('reason','not_executed')))
                rows.append(dict(schema=SCHEMA,cohort_id='new_squad_train_development12',case_id=cid,condition_id=rawrow['condition'],execution_state=state,
                    truncated=rawrow.get('truncated'),reason=rawrow.get('reason'),input_digest=c['prompt_sha256'],gold_digest=c['gold_sha256'],comparison_digest=comp,metrics=metrics,
                    costs=dict(prefix_kv_bytes=measure(rawrow.get('prefix_kv_bytes'),'no_tensor_infeasible' if not ok else 'not_recorded'),final_live_kv_bytes=measure(rawrow.get('final_live_kv_bytes'),'no_output' if not ok else 'not_recorded'),peak_gpu_bytes=measure(None,'not_measured'),latency_ms=measure(None,'not_measured'),extra_buffer_peak_bytes=measure(None,'not_measured')),origin=str(p.relative_to(r))))
        names=['full','adapted_snapkv','uniform_random','adapted_snapkv_system_pinned','uniform_random_system_pinned']
        plan=dict(cohort_id='new_squad_train_development12',case_ids=list(cases),scientific_role='prospectively_sampled_new_source_development_not_confirmation',context_group_ids=[c['context_group_id'] for c in cases.values()],conditions=[dict(condition_id=n,budget_group='half_prefix' if n!='full' else None) for n in names],metrics={k:dict(kind=v['kind'],metric_id=v['metric_id']) for k,v in rows[0]['metrics'].items()})
        report=summarize(plan,rows);require(len(rows)==len(report['cells'])==60,'all60plannedcells')
        delivery={}
        for name in names:
            rr=[x for x in rawrows if x['condition']==name];ok=[x for x in rr if x['status']=='ok']
            delivery[name]=dict(scheduled=12,delivered_joint_success=sum(not x['truncated'] and x['metrics']['joint_success'] for x in ok),completed=sum(not x['truncated'] for x in ok),infeasible=sum(x['status']=='infeasible_budget' for x in rr),scope='All12 scheduled cells, budget-infeasible means no deliverable output; semantic scores remain N/A, not false')
        for x in rawrows:
            if x['status']!='ok':
                t=tokmap[x['case_id']];require(x['condition'].endswith('_system_pinned') and len(t['required_pinned_ids'])>t['budget'],'infeasible correctness')
        eng=[json.loads(x) for x in (r/cfg['compression']/'engineering.jsonl').read_text().splitlines()]
        tested={n:sum(x['status']=='ok' and x['condition']==n for x in eng) for n in names[1:]}
        save(o/'report.json',dict(paired=report,delivery=delivery,compact_engineering_custom_rows_by_method=tested,protected_engineering_paths_verified=False,cross_task_split_final=False,independent_confirmation=False))
        (o/'normalized_records.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=True)+'\n' for x in rows));save(o/'plan.json',plan)
        lines=['# New-source12 DEV, fixed half budget','','| Condition | Executed | Infeasible | Task correct/evaluated | Format correct/evaluated | Joint delivery/12 |','| --- | --- | --- | --- | --- | --- |']
        for n,x in report['conditions'].items():
            e=x['execution'];t=x['metrics']['task'];f=x['metrics']['constraint'];d=delivery[n]
            lines.append(f"| {n} | {e['ok']} | {e['infeasible_budget']} | {t['pass_count']}/{t['evaluated_count']} | {f['pass_count']}/{f['evaluated_count']} | {d['delivered_joint_success']}/12 |")
        lines+=['','Only2/12 protected conditions are feasible; do not compare their conditional means as overall method ranking. Protected engineering cases were infeasible, so protected native/custom engineering path validation remains unavailable. Cross-task final split and independent scientific confirmation remain pending.']
        (o/'report.md').write_text('\n'.join(lines)+'\n')
        for f,v in cfg['inputs'].items():require(sha(r/f)==v,'input changed')
        s.update(status='complete',planned_cells=60,normalized_rows=len(rows),executed_main=sum(x['status']=='ok' for x in rawrows),infeasible_main=sum(x['status']=='infeasible_budget' for x in rawrows),independent_confirmation=False)
    except BaseException as exc:
        s.update(status='failed',error=repr(exc));(o/'failure.txt').write_text(traceback.format_exc())
    finally:
        s['elapsed_seconds']=time.monotonic()-start;save(o/'summary.json',s)
        files=[p for p in o.iterdir() if p.is_file()];require(len(files)<32 and sum(p.stat().st_size for p in files)<16777216,'archive cap')
        save(o/'manifest.json',{p.name:sha(p) for p in files});print(json.dumps(s),flush=True)
    return 0 if s['status']=='complete' else 1
if __name__=='__main__':raise SystemExit(main())
