"""Fixed acceptance cases for reliability scalar contracts, no model execution."""
import copy
from reliability_system_core import (SCHEMA, ContractError, budget_plan, kv_layout,
                                     measure, metric, summarize)


def check(ok,reason):
    if not ok:raise AssertionError(reason)


def expect_error(fn,reason):
    try:fn()
    except ContractError as exc:check(reason in str(exc),'unexpected rejection:'+str(exc))
    else:raise AssertionError('missing rejection:'+reason)


def layer(heads=4,dim=128,bytes_=2):
    return dict(attention_type='full_attention',batch=1,key=dict(heads=heads,dimension=dim,element_bytes=bytes_),value=dict(heads=heads,dimension=dim,element_bytes=bytes_))


def row(case,condition,task=True,constraint=True,f1=1.0):
    return dict(schema=SCHEMA,cohort_id='software',case_id=case,condition_id=condition,execution_state='ok',truncated=False,reason=None,
        input_digest='a'*64,gold_digest='b'*64,comparison_digest='c'*64,
        metrics=dict(task=metric(task,'task-v1',reason='extraction_unavailable' if task is None else None),
            constraint=metric(constraint,'format-v1'),f1=metric(f1,'f1-v1','unit_interval',reason='extraction_unavailable' if f1 is None else None)),
        costs=dict(prefix_kv_bytes=measure(100 if condition=='full' else 50),peak_gpu_bytes=measure(None,'not_measured')),origin='software')


def plan(cases=None,conditions=None):
    return dict(cohort_id='software',case_ids=cases or ['a'],scientific_role='software_acceptance',
        conditions=[dict(condition_id=n,budget_group='same' if n!='full' else None) for n in (conditions or ['full','m'])],
        metrics=dict(task=dict(metric_id='task-v1',kind='boolean'),constraint=dict(metric_id='format-v1',kind='boolean'),f1=dict(metric_id='f1-v1',kind='unit_interval')))


def acceptance(index):
    if index==0:
        check(kv_layout([layer() for _ in range(28)])['bytes_per_prefix_slot']==57344,'GQA bytes')
        check(kv_layout([layer(32) for _ in range(32)])['bytes_per_prefix_slot']==524288,'MHA bytes')
    elif index==1:
        check(kv_layout([layer(2,64,2),layer(1,32,4)])['bytes_per_prefix_slot']==768,'mixed layout bytes')
    elif index==2:
        bad=layer();bad['attention_type']='sliding_attention'
        expect_error(lambda:kv_layout([bad]),'unsupported_attention_type')
        bad=layer();bad['key']['element_bytes']=1
        expect_error(lambda:kv_layout([bad]),'unimplemented_KV_dtype')
    elif index==3:
        p=budget_plan(101,'1/2',list(range(20)),sink=4,recent=4)
        check(p['requested_slots']==p['effective_slots']==50 and p['required_union_count']==24 and p['free_slots']==26,'budget union')
    elif index==4:
        p=budget_plan(100,'1/10',list(range(20)),sink=4,recent=4)
        check(p['state']=='infeasible_budget' and p['effective_slots']==10 and p['free_slots'] is None,'infeasible not enlarged')
    elif index==5:
        expect_error(lambda:budget_plan(10,'1/2',[10]),'protection_outside_prefix')
        expect_error(lambda:budget_plan(10,0.5,[]),'retention_must_be_exact_string')
    elif index==6:
        rr=row('a','m');expect_error(lambda:summarize(plan(),[row('a','full'),rr,rr]),'duplicate_cell')
    elif index==7:
        a=row('a','m');b=row('a','n');b['costs']['prefix_kv_bytes']=measure(51)
        expect_error(lambda:summarize(plan(conditions=['full','m','n']),[row('a','full'),a,b]),'unequal_actual_KV_budget')
    elif index==8:
        a=row('a','m');a['input_digest']='d'*64
        expect_error(lambda:summarize(plan(),[row('a','full'),a]),'pair_identity_mismatch')
        a=row('a','m');a['comparison_digest']='d'*64
        expect_error(lambda:summarize(plan(),[row('a','full'),a]),'pair_identity_mismatch')
    elif index==9:
        rr=summarize(plan(),[row('a','full'),row('a','m',None,False,None)])['conditions']['m']['metrics']['task']
        check(rr['unassessed_Full_pass_count']==1 and rr['strict_conditional_damage'] is None and rr['all_Full_pass_damage_bounds']==[0,1],'N/A risk')
    elif index==10:
        rr=summarize(plan(),[row('a','full',False),row('a','m',True)])['conditions']['m']['metrics']['task']
        check(rr['all_Full_pass_damage_bounds'] is None and rr['transitions']['W2C']==1,'zero denominator')
    elif index==11:
        a=row('a','m');a['truncated']=True
        rr=summarize(plan(),[row('a','full'),a])['conditions']['m']
        check(rr['execution']['truncated']==1 and rr['metrics']['constraint']['unassessed_Full_pass_count']==1,'truncation explicit')
    elif index==12:
        rr=summarize(plan(),[row('a','full')]);x=rr['conditions']['m']
        check(len(rr['cells'])==2 and x['execution']['not_run']==1 and x['metrics']['task']['all_Full_pass_damage_bounds']==[0,1],'scheduled missing')
    elif index==13:
        a=row('a','m');a.update(execution_state='infeasible_budget',truncated=None,reason='complete protection too large')
        rr=summarize(plan(),[row('a','full'),a])['conditions']['m']
        check(rr['execution']['infeasible_budget']==1 and rr['metrics']['task']['evaluated_count']==0,'infeasible not task failure')
    elif index==14:
        rr=summarize(plan(['a','b']),[row('a','full',True),row('b','full',False),row('a','m',False),row('b','m',True)])['conditions']['m']['metrics']['task']
        check(rr['transitions']['C2W']==rr['transitions']['W2C']==1 and rr['mean_paired_delta']==0 and rr['strict_conditional_damage']==1,'net zero hides changes')
    elif index==15:
        rr=summarize(plan(),[row('a','full',f1=.75),row('a','m',f1=.25)])['conditions']['m']
        check(rr['metrics']['f1']['mean_paired_delta']==-.5 and 'transitions' not in rr['metrics']['f1'],'float not bool')
        check(rr['costs']['peak_gpu_bytes']['unknown_count']==1 and rr['costs']['peak_gpu_bytes']['minimum'] is None,'unknown cost not zero')
        expect_error(lambda:metric(float('nan'),'bad','unit_interval'),'metric_value_type_or_range')
        expect_error(lambda:metric(1,'bad'),'metric_value_type_or_range')
        expect_error(lambda:measure(None),'missing_value_requires_reason')
        a=row('a','m');a['metrics']['task']['metric_id']='different'
        expect_error(lambda:summarize(plan(),[row('a','full'),a]),'metric_semantics_mismatch')
    else:raise AssertionError('unknown acceptance case')
    return dict(id=f'S{index+1:02d}',status='pass',scope='software_only')
