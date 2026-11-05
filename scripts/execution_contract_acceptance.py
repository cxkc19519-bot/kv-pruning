"""Synthetic acceptance for condition admission. No generation or file I/O."""
import copy
from reliability_system_core import ContractError
from reliability_execution_contract import (VERSION,condition_fingerprint,plan_case,
    engineering_evidence,admission,execute_admitted,historical_observation)


def check(ok,s):
    if not ok:raise AssertionError(s)


def reject(fn,reason):
    try:fn()
    except ContractError as exc:check(reason in str(exc),'wrong rejection:'+str(exc))
    else:raise AssertionError('not rejected:'+reason)


def spec(pin=False):
    return dict(condition_id='pin' if pin else 'plain',retention='1/2',protect_system=pin,
        sink=4,recent=64,selector_version_digest='a'*64,engineering_cases_required=2,
        required_paths=['native','custom'],compare_trace=True)


def setup(pin=False,n=300):
    s=spec(pin);runtime='b'*64
    plans=[plan_case(c,n,list(range(56)),s,runtime) for c in ['e1','e2']]
    fp=condition_fingerprint(s,runtime)
    obs=[dict(case_id=c,path=p,condition_fingerprint=fp,execution_state='ok',ids=[7,9],truncated=False,
        case_input_digest='c'*64,trace=[dict(step=0,physical_start=150,logical_start=300,input_width=8)]) for c in ['e1','e2'] for p in ['native','custom']]
    return s,runtime,plans,obs


def validate_case(i):
    s,r,plans,obs=setup();e=engineering_evidence(s,r,plans,obs)
    p=plan_case('d',300,list(range(56)),s,r)
    if i==0:
        d=admission(p,e);check(d['launch_allowed'] and e['verified_engineering_cases']==2,'complete evidence')
    elif i==1:
        s,r,plans,obs=setup(True);e=engineering_evidence(s,r,plans,obs);p=plan_case('d',200,list(range(56)),s,r)
        d=admission(p,e);check(p['budget']['required_union_count']==120 and p['budget']['requested_slots']==100 and d['admission_state']=='blocked_budget','budget fixed')
    elif i==2:
        s,r,plans,obs=setup(True,200)
        obs=[dict(case_id=x['case_id'],path=None,condition_fingerprint=x['condition_fingerprint'],execution_state='infeasible_budget') for x in plans]
        e=engineering_evidence(s,r,plans,obs);p=plan_case('d',300,list(range(56)),s,r);d=admission(p,e)
        check(e['status']=='unverified_budget_infeasible' and d['admission_state']=='blocked_engineering_unverified','empty evidence not pass')
    elif i==3:
        obs[1]['ids']=[7,8];e=engineering_evidence(s,r,plans,obs);check(e['status']=='failed' and admission(p,e)['admission_state']=='blocked_engineering_failed','token mismatch')
    elif i==4:
        obs[1]['trace'][0]['logical_start']=299;e=engineering_evidence(s,r,plans,obs);check(e['status']=='failed','trace mismatch')
    elif i==5:
        e=engineering_evidence(s,r,plans,obs[:-1]);check(e['status']=='insufficient_coverage' and not admission(p,e)['launch_allowed'],'missing path')
    elif i==6:
        for x in obs:
            if x['case_id']=='e1':x['truncated']=True
        e=engineering_evidence(s,r,plans,obs);check(e['path_sequences_verified'] and e['sequence_verified_but_truncated_cases']==1 and e['cases'][0]['output_complete'] is False,'cap identity separate')
    elif i==7:
        obs[1]['truncated']=True;e=engineering_evidence(s,r,plans,obs);check(e['status']=='failed','termination disagreement')
    elif i==8:
        obs[0]['condition_fingerprint']='d'*64;reject(lambda:engineering_evidence(s,r,plans,obs),'stale_or_foreign')
    elif i==9:
        s2=copy.deepcopy(s);s2['retention']='3/4';p2=plan_case('d',300,list(range(56)),s2,r);reject(lambda:admission(p2,e),'scope_mismatch')
    elif i==10:
        reject(lambda:engineering_evidence(s,r,plans,obs+[obs[0]]),'duplicate_engineering_observation')
    elif i==11:
        obs[1]['case_input_digest']='d'*64;e=engineering_evidence(s,r,plans,obs);check(e['status']=='failed','wrong case input')
    elif i==12:
        s,r,plans,obs=setup(True,200);reject(lambda:engineering_evidence(s,r,plans,obs),'generated_engineering_on_infeasible')
    elif i==13:
        d=admission(p,e);v=historical_observation(d,None);check(v['execution_state']=='not_run' and d['launch_allowed'] and not v['actual_generated'],'admission not execution')
    elif i==14:
        s,r,plans,obs=setup(True,200);obs=[];e=engineering_evidence(s,r,plans,obs);p=plan_case('d',300,list(range(56)),s,r);d=admission(p,e)
        raw=dict(case_id='d',condition='pin',status='ok',truncated=False,metrics=dict(candidate_status='available'))
        v=historical_observation(d,raw);check(v['actual_generated'] and v['historical_diagnostic_only'] and not v['strict_future_launch_allowed'],'preserve historical diagnostic')
    elif i==15:
        s,r,plans,obs=setup(True);e=engineering_evidence(s,r,plans,obs);p=plan_case('d',200,list(range(56)),s,r);d=admission(p,e)
        reject(lambda:historical_observation(d,dict(case_id='d',condition='pin',status='ok',truncated=False)),'generation_on_infeasible')
    elif i==16:
        d=admission(p,e);called=[];result=execute_admitted(d,lambda:called.append('software_stub'))
        check(called==['software_stub'] and result is None,'once-only dispatcher')
        s,r,plans,obs=setup(True,200);e=engineering_evidence(s,r,plans,[]);p=plan_case('d',200,list(range(56)),s,r);d=admission(p,e)
        reject(lambda:execute_admitted(d,lambda:called.append('blocked_stub')),'launch_blocked');check(called==['software_stub'],'blocked operation invoked')
    elif i==17:
        obs[0]['ids']=[];reject(lambda:engineering_evidence(s,r,plans,obs),'invalid_engineering_token_sequence')
    elif i==18:
        e['status']='verified';e['verified_engineering_cases']=0
        reject(lambda:admission(p,e),'summary_inconsistent')
    elif i==19:
        d=admission(p,e);reject(lambda:historical_observation(d,dict(case_id='wrong',condition='plain',status='ok',truncated=False)),'cell_identity_mismatch')
    else:raise AssertionError('unknown acceptance')
    return dict(id=f'E{i+1:02d}',status='pass',model_outputs=0)
