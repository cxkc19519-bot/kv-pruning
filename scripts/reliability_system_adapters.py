"""Read-only adapters from frozen archived scalar records; no text scoring."""
import hashlib
import json
from reliability_system_core import SCHEMA, measure, metric, require


def hash_json(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def common(cohort,case,condition,state,truncated,reason,input_digest,gold_digest,comparison,metrics,costs,origin):
    return dict(schema=SCHEMA,cohort_id=cohort,case_id=case,condition_id=condition,execution_state=state,
        truncated=truncated,reason=reason,input_digest=input_digest,gold_digest=gold_digest,comparison_digest=comparison,
        metrics=metrics,costs=costs,origin=origin)


def trec(row,comparison_digest):
    metrics={name:metric(x['value'],'trec_v1:'+x['metric_id'],reason=x['reason']) for name,x in row['metrics'].items()}
    costs={name:measure(x['value'],x['reason']) for name,x in row['costs'].items()}
    return common(row['cohort_id'],row['case_id'],row['condition_id'],row['execution_state'],row['truncated'],row['reason'],
        row['input_sha256'],hash_json(row['gold']) if row['gold'] is not None else None,comparison_digest,
        metrics,costs,row['origin'])


def answer_format(row,cohort,comparison_digest,origin):
    require(row['status']=='ok','archive_adapter_expects_successful_execution_rows')
    raw=row['metrics']
    metrics=dict(task=metric(raw['em'],'squad_v11_bidaf_pinned_em_v1',reason=raw['reason'] if raw['em'] is None else None),
        constraint=metric(raw['format'],'json_answer_format_v1'),
        task_f1=metric(raw['f1'],'squad_v11_bidaf_pinned_f1_v1','unit_interval',raw['reason'] if raw['f1'] is None else None))
    costs=dict(prefix_kv_bytes=measure(row['prefix_kv_bytes']),final_live_kv_bytes=measure(row['final_live_kv_bytes'],'not_recorded'),
        peak_gpu_bytes=measure(row['peak_memory'],'not_measured'),latency_ms=measure(row['latency'],'not_measured'),
        extra_buffer_peak_bytes=measure(None,'not_measured'))
    return common(cohort,row['case_id'],row['condition'],row['status'],row['truncated'],None,row['prompt_sha256'],row['gold_sha256'],
        comparison_digest,metrics,costs,origin)


def archive_plan(cohort,rows,role,groups=None):
    cases=sorted({r['case_id'] for r in rows})
    names=sorted({r['condition_id'] for r in rows},key=lambda x:(x!='full',x))
    require(rows and all(r['cohort_id']==cohort for r in rows),'adapter_cohort')
    metric_specs={name:dict(kind=x['kind'],metric_id=x['metric_id']) for name,x in rows[0]['metrics'].items()}
    return dict(cohort_id=cohort,case_ids=cases,
        conditions=[dict(condition_id=n,budget_group='archived_same_prefix_bytes' if n!='full' else None) for n in names],
        metrics=metric_specs,scientific_role=role,context_group_ids=groups,
        selection='case/condition identities enumerated from pinned historical records; replay only, not prospective experiment plan')
