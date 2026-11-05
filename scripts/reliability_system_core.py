"""Versioned scalar contract, KV budget planner and paired report; stdlib only."""
from collections import Counter
from fractions import Fraction
import math

SCHEMA = 'kv_reliability_scalar_v1'
STATES = ('ok', 'error', 'not_run', 'infeasible_budget')
TRANSITIONS = ('C2C', 'C2W', 'W2C', 'W2W')


class ContractError(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise ContractError(reason)


def digest(value):
    return isinstance(value, str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def measure(value, reason=None):
    require(value is not None or isinstance(reason,str) and reason, 'missing_value_requires_reason')
    return dict(value=value, reason=None if value is not None else reason)


def metric(value, metric_id, kind='boolean', reason=None):
    require(kind in ('boolean','unit_interval'), 'metric_kind')
    require(isinstance(metric_id,str) and metric_id, 'metric_id')
    if value is not None:
        require(type(value) is bool if kind=='boolean' else type(value) in (int,float) and math.isfinite(value) and 0<=value<=1, 'metric_value_type_or_range')
    item=measure(value,reason)
    item.update(metric_id=metric_id,kind=kind)
    return item


def kv_layout(layers):
    """Each layer declares actual K/V heads, dimensions and dtype element bytes.

    This function validates descriptors, not a model or physical tensors.
    Runtime adapters must derive them from tensors and verify this estimate.
    """
    require(isinstance(layers,list) and layers, 'empty_KV_layout')
    total=0
    for layer in layers:
        require(isinstance(layer,dict) and layer.get('attention_type')=='full_attention', 'unsupported_attention_type')
        require(layer.get('batch')==1 and type(layer.get('batch')) is int, 'batch1_only')
        for side in ('key','value'):
            for key in ('heads','dimension','element_bytes'):
                n=layer.get(side,{}).get(key)
                require(type(n) is int and n>0, 'invalid_KV_dimension')
            require(layer[side]['element_bytes'] in (2,4), 'unimplemented_KV_dtype')
            total+=layer[side]['heads']*layer[side]['dimension']*layer[side]['element_bytes']
    return dict(layer_count=len(layers),bytes_per_prefix_slot=total,
                tensor_verified=False,scope='batch1 homogeneous per-layer retained slot count; BF16/FP16/FP32 tensor elements')


def budget_plan(prefix_tokens, retention, protected_positions, sink=4, recent=64):
    require(type(prefix_tokens) is int and prefix_tokens>0, 'invalid_prefix_length')
    require(type(sink) is int and sink>=0 and type(recent) is int and recent>=0, 'invalid_anchors')
    require(isinstance(retention,str), 'retention_must_be_exact_string')
    try:
        ratio=Fraction(retention)
    except (ValueError,ZeroDivisionError) as exc:
        raise ContractError('invalid_retention') from exc
    require(0<ratio<=1, 'invalid_retention')
    require(isinstance(protected_positions,list) and all(type(i) is int and 0<=i<prefix_tokens for i in protected_positions), 'protection_outside_prefix')
    budget=prefix_tokens*ratio.numerator//ratio.denominator
    anchors=set(range(min(sink,prefix_tokens)))|set(range(max(0,prefix_tokens-recent),prefix_tokens))
    required=sorted(anchors|set(protected_positions))
    feasible=len(required)<=budget and budget>0
    return dict(state='ok' if feasible else 'infeasible_budget',prefix_tokens=prefix_tokens,
        retention=str(ratio),requested_slots=budget,effective_slots=budget,
        required_positions=required,anchor_count=len(anchors),protected_unique_count=len(set(protected_positions)),
        extra_protected_slots=len(required)-len(anchors),required_union_count=len(required),
        free_slots=budget-len(required) if feasible else None,protection_free=False)


def validate_record(row):
    require(row.get('schema')==SCHEMA,'schema_version')
    for k in ('cohort_id','case_id','condition_id'):
        require(isinstance(row.get(k),str) and row[k], 'record_identity')
    state=row.get('execution_state');require(state in STATES,'execution_state')
    if state=='ok':
        require(type(row.get('truncated')) is bool,'truncation_flag')
        for k in ('input_digest','gold_digest','comparison_digest'):
            require(digest(row.get(k)),'missing_or_invalid_'+k)
        require(type(row.get('costs',{}).get('prefix_kv_bytes',{}).get('value')) is int and row['costs']['prefix_kv_bytes']['value']>=0,'missing_actual_prefix_bytes')
    else:
        require(isinstance(row.get('reason'),str) and row['reason'],'execution_failure_reason')
    require(isinstance(row.get('metrics'),dict) and row['metrics'],'missing_metrics')
    for item in row['metrics'].values():
        check=metric(item.get('value'),item.get('metric_id'),item.get('kind'),item.get('reason'))
        require(check==item,'metric_contract')
    for item in row.get('costs',{}).values():
        require(measure(item.get('value'),item.get('reason'))==item,'cost_contract')
        if item['value'] is not None:
            require(type(item['value']) in (int,float) and math.isfinite(item['value']) and item['value']>=0,'invalid_cost')


def unavailable(row,name):
    if row is None:return 'not_run'
    if row['execution_state']!='ok':return row['execution_state']
    if row['truncated']:return 'truncated'
    item=row['metrics'].get(name)
    if item is None:return 'metric_not_supported'
    if item['value'] is None:return item['reason']
    return None


def summarize(plan,records):
    """Strict paired analysis without task/model/number-of-cases hardcoding."""
    cohort=plan['cohort_id'];cases=plan['case_ids'];conditions=plan['conditions'];metrics=plan['metrics']
    require(cases and len(cases)==len(set(cases)),'duplicate_or_empty_case_plan')
    names=[x['condition_id'] for x in conditions]
    require(len(names)==len(set(names)) and names.count('full')==1,'condition_plan')
    require(metrics and all(x['kind'] in ('boolean','unit_interval') for x in metrics.values()),'metric_plan')
    by={}
    for row in records:
        validate_record(row);key=(row['case_id'],row['condition_id'])
        require(row['cohort_id']==cohort and row['case_id'] in cases and row['condition_id'] in names,'record_outside_plan')
        require(key not in by,'duplicate_cell');by[key]=row
        for name,spec in metrics.items():
            item=row['metrics'].get(name)
            require(item is not None and item['kind']==spec['kind'] and item['metric_id']==spec['metric_id'],'metric_semantics_mismatch')
    for case in cases:
        base=by.get((case,'full'));budgets={}
        for spec in conditions:
            row=by.get((case,spec['condition_id']))
            if base and row:
                for k in ('input_digest','gold_digest','comparison_digest'):
                    if base.get(k) is not None and row.get(k) is not None:require(base[k]==row[k],'pair_identity_mismatch:'+k)
            group=spec.get('budget_group')
            if row and row['execution_state']=='ok' and group:
                value=row['costs']['prefix_kv_bytes']['value']
                require(group not in budgets or budgets[group]==value,'unequal_actual_KV_budget')
                budgets[group]=value
    results={};cells=[]
    for name in names:
        selected=[by.get((c,name)) for c in cases]
        for c,row in zip(cases,selected):
            cells.append(dict(case_id=c,condition_id=name,execution_state=row['execution_state'] if row else 'not_run',
                reason=row.get('reason') if row else 'scheduled_cell_missing',truncated=row.get('truncated') if row else None))
        execution={s:sum((r['execution_state'] if r else 'not_run')==s for r in selected) for s in STATES}
        execution.update(scheduled=len(cases),truncated=sum(bool(r and r['execution_state']=='ok' and r['truncated']) for r in selected))
        reports={}
        for mn,ms in metrics.items():
            reasons=Counter(unavailable(row,mn) for row in selected);reasons.pop(None,None)
            values=[row['metrics'][mn]['value'] for row in selected if unavailable(row,mn) is None]
            rec=dict(kind=ms['kind'],metric_id=ms['metric_id'],evaluated_count=len(values),unavailable_count=len(cases)-len(values),unavailable_reasons=dict(reasons),
                mean=sum(values)/len(values) if values else None)
            if ms['kind']=='boolean':rec['pass_count']=sum(values)
            if name!='full':
                transitions=Counter();paired=[];D=eligible=unknown=0;pair_reasons=Counter();deltas=[]
                for case,row in zip(cases,selected):
                    base=by.get((case,'full'));br,rr=unavailable(base,mn),unavailable(row,mn)
                    if ms['kind']=='boolean' and br is None and base['metrics'][mn]['value']:D+=1
                    if br or rr:
                        reason='full:'+br if br else 'method:'+rr;pair_reasons[reason]+=1
                        if ms['kind']=='boolean' and br is None and base['metrics'][mn]['value']:unknown+=1
                        paired.append(dict(case_id=case,transition=None,reason=reason,delta=None));continue
                    a,b=base['metrics'][mn]['value'],row['metrics'][mn]['value']
                    delta=float(b)-float(a);deltas.append(delta)
                    transition=('C' if a else 'W')+'2'+('C' if b else 'W') if ms['kind']=='boolean' else None
                    if transition:transitions[transition]+=1;eligible+=int(a)
                    paired.append(dict(case_id=case,transition=transition,reason=None,delta=delta))
                rec.update(paired_count=len(deltas),unavailable_pair_count=sum(pair_reasons.values()),pair_unavailable_reasons=dict(pair_reasons),pair_rows=paired,
                    mean_paired_delta=sum(deltas)/len(deltas) if deltas else None)
                if ms['kind']=='boolean':
                    damaged=transitions['C2W']
                    rec.update(transitions={s:transitions[s] for s in TRANSITIONS},available_Full_pass_count=D,eligible_Full_pass_pair_count=eligible,unassessed_Full_pass_count=unknown,
                        strict_conditional_damage=damaged/eligible if eligible else None,
                        all_Full_pass_damage_bounds=[damaged/D,(damaged+unknown)/D] if D else None,bounds_are_not_confidence_intervals=True)
            reports[mn]=rec
        costs={}
        cost_names=sorted({k for row in selected if row for k in row['costs']})
        for cost in cost_names:
            obs=[r['costs'].get(cost,measure(None,'not_recorded')) if r else measure(None,'no_output') for r in selected]
            vals=[x['value'] for x in obs if x['value'] is not None]
            costs[cost]=dict(observed_count=len(vals),unknown_count=len(obs)-len(vals),unknown_reasons=dict(Counter(x['reason'] for x in obs if x['value'] is None)),
                minimum=min(vals) if vals else None,maximum=max(vals) if vals else None)
        results[name]=dict(execution=execution,metrics=reports,costs=costs)
    return dict(schema=SCHEMA,cohort_id=cohort,case_count=len(cases),conditions=results,cells=cells,
                scientific_role=plan['scientific_role'],independent_confirmation=False,
                group_count=len(set(plan.get('context_group_ids',[]))) if plan.get('context_group_ids') else None,
                group_reason=None if plan.get('context_group_ids') else 'not_established',
                inference_performed=False,task_text_rescored=False)
