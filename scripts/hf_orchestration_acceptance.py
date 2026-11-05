"""Stage/lazy-load acceptance via software backends; never import HF/torch."""
import copy
from reliability_system_core import ContractError
from reliability_hf_orchestrator import HFOrchestrator


def check(ok,s):
    if not ok:raise AssertionError(s)


def reject(fn,why):
    try:fn()
    except ContractError as e:check(why in str(e),'unexpected rejection:'+str(e))
    else:raise AssertionError('missing rejection:'+why)


class SoftwareBackend:
    kind='software_stub'
    def __init__(self,mode=None):self.calls=0;self.mode=mode
    def execute(self,req,case,spec,budget):
        self.calls+=1
        result=dict(request_digest=req['request_digest'],execution_state='ok',ids=[7,9],truncated=False,
            trace=[dict(physical_start=budget['effective_slots'],logical_start=case['prefix_tokens'])])
        if self.mode=='mismatch' and req['path']=='custom':result['ids']=[8,9]
        if self.mode=='wrong_result':result['request_digest']='0'*64
        if self.mode=='truncated':result['truncated']=True
        return result


def setup(mode='software_fixture',pin=False,n=300,backend_mode=None):
    cases=[dict(case_id=c,split_role=role,input_ids=[5]*(n+8),prefix_tokens=n,header_ids=list(range(56)),prompt_sha256='a'*64,context_group_id='b'*64) for c,role in [('e1','engineering'),('e2','engineering'),('d','development')]]
    def spec(name,pin=False):return dict(condition_id=name,retention='1' if name=='full' else '1/2',protect_system=pin,sink=4,recent=64,selector_version_digest='c'*64,engineering_cases_required=2,required_paths=['native_whole','native_split','custom_split'] if name=='full' else ['native','custom'],compare_trace=name!='full')
    specs=[spec('full'),spec('pin' if pin else 'plain',pin)]
    runtime='d'*64;policy=dict(mode=mode,execution_enabled=True,bootstrap_generation_enabled=True,DEV_generation_enabled=True,
        runtime_digest=runtime,max_engineering_calls=10,max_DEV_calls=2,max_input_tokens=2048,wall_seconds=30)
    calls=[];backend=SoftwareBackend(backend_mode)
    def factory():calls.append('construct');return backend
    engine=HFOrchestrator(cases,specs,runtime,policy,factory)
    return engine,calls,backend


def bootstrap(engine,name='plain'):
    for cid in ['e1','e2']:
        for path in engine.specs[name]['required_paths']:engine.dispatch(engine.request(cid,name,'engineering',path))


def validate_case(i):
    engine,calls,backend=setup()
    if i==0:
        engine,calls,backend=setup(mode='dry_run');p=engine.dry_run_plan()
        check(not calls and backend.calls==0 and engine.loader_attempts==0 and all(x['state']=='planned_no_execution' for x in p['engineering']),'dry lazy')
    elif i==1:
        engine,calls,backend=setup(mode='dry_run',pin=True,n=200);p=engine.dry_run_plan()
        check(not calls and sum(x.get('state')=='blocked_budget' for x in p['engineering'])==2,'infeasible bootstrap')
    elif i==2:
        x=engine.dispatch(engine.request('d','plain','development','custom'))
        check(x['state']=='blocked' and not calls,'DEV before engineering')
    elif i==3:
        bootstrap(engine);x=engine.dispatch(engine.request('d','plain','development','custom'))
        check(x['state']=='executed' and engine.backend_calls==5 and calls==['construct'],'bootstrap not self-locked')
    elif i==4:
        bootstrap(engine,'full');x=engine.dispatch(engine.request('d','full','development','custom_split'))
        check(x['state']=='executed' and engine.backend_calls==7,'Full3paths')
    elif i==5:
        req=engine.request('e1','plain','engineering','native');req['case_input_digest']='e'*64
        reject(lambda:engine.dispatch(req),'mutated_dispatch_request');check(not calls,'mutated request loaded')
    elif i==6:
        req=engine.request('e1','plain','engineering','native');engine.cases['e1']['input_ids'][0]=99
        reject(lambda:engine.dispatch(req),'mutated_prepared_input');check(not calls,'mutated input loaded')
    elif i==7:
        req=engine.request('e1','plain','engineering','native');engine.cases['e1']['context_group_id']='e'*64
        reject(lambda:engine.dispatch(req),'mutated_prepared_input');check(not calls,'mutated selector key loaded')
    elif i==8:
        reject(lambda:engine.request('d','plain','engineering','native'),'stage_role_mismatch');check(not calls,'DEV as engineering')
    elif i==9:
        reject(lambda:engine.request('missing','plain','development','custom'),'unplanned_cell')
        bad=copy.deepcopy(list(engine.cases.values()));bad[0]['split_role']='sealed'
        reject(lambda:HFOrchestrator(bad,list(engine.specs.values()),engine.runtime,engine.policy),'sealed_or_unknown_role')
    elif i==10:
        ev=engine.evidence('plain');ev['condition_fingerprint']='e'*64
        reject(lambda:engine.offer_evidence(ev),'stale_engineering_for_new_backend');check(not calls,'old evidence loaded')
    elif i==11:
        engine.policy['bootstrap_generation_enabled']=False
        reject(lambda:engine.dispatch(engine.request('e1','plain','engineering','native')),'stage_execution_disabled');check(not calls,'disabled bootstrap loaded')
    elif i==12:
        engine.policy['max_engineering_calls']=0
        reject(lambda:engine.dispatch(engine.request('e1','plain','engineering','native')),'orchestration_call_cap');check(not calls,'overcap loaded')
    elif i==13:
        req=engine.request('e1','plain','engineering','native');engine.dispatch(req)
        reject(lambda:engine.dispatch(req),'duplicate_model_dispatch');check(backend.calls==1,'repeated output')
    elif i==14:
        engine,calls,backend=setup(backend_mode='mismatch')
        engine.dispatch(engine.request('e1','plain','engineering','native'))
        reject(lambda:engine.dispatch(engine.request('e1','plain','engineering','custom')),'engineering_sequence_mismatch')
        reject(lambda:engine.dispatch(engine.request('e2','plain','engineering','native')),'orchestrator_halted_after_failure');check(backend.calls==2,'continued after failure')
    elif i==15:
        engine,calls,backend=setup(backend_mode='wrong_result')
        reject(lambda:engine.dispatch(engine.request('e1','plain','engineering','native')),'backend_result_request_mismatch');check(engine.failed,'unbound result accepted')
    elif i==16:
        engine,calls,backend=setup(backend_mode='truncated');bootstrap(engine)
        check(engine.evidence('plain')['path_sequences_verified'] and engine.evidence('plain')['sequence_verified_but_truncated_cases']==2,'truncated equality changed into complete')
    elif i==17:
        def failed_factory():calls.append('failed_load');raise RuntimeError('synthetic load failure')
        engine.factory=failed_factory
        try:engine.dispatch(engine.request('e1','plain','engineering','native'))
        except RuntimeError:pass
        else:raise AssertionError('no failure')
        reject(lambda:engine.dispatch(engine.request('e2','plain','engineering','native')),'orchestrator_halted_after_failure');check(calls==['failed_load'],'automatic load retry')
    elif i==18:
        engine.policy['runtime_digest']='e'*64
        reject(lambda:engine.dispatch(engine.request('e1','plain','engineering','native')),'policy_runtime_mismatch');check(not calls,'wrong policy runtime loaded')
    elif i==19:
        req=engine.request('e1','plain','engineering','native');engine.started-=31
        reject(lambda:engine.dispatch(req),'orchestration_wall_cap');check(not calls,'wallcap loaded')
    elif i==20:
        from reliability_qwen_hf_backend import QwenHFBackend
        b=QwenHFBackend(dict(registered_runtime_digest=engine.runtime))
        req=engine.request('e1','plain','engineering','native');c=copy.deepcopy(engine.cases['e1']);p=engine.decision(req)['case_plan']
        reject(lambda:b.execute(req,c,engine.specs['plain'],p['budget']),'GPU_protocol_not_registered')
        check(b.model is None,'real adapter loaded without GPU protocol')
    elif i==21:
        from reliability_qwen_hf_backend import QwenHFBackend
        b=QwenHFBackend(dict(registered_runtime_digest=engine.runtime))
        req=engine.request('e1','plain','engineering','native');c=copy.deepcopy(engine.cases['e1']);c['input_ids'][0]=98
        p=engine.decision(req)['case_plan'];reject(lambda:b.execute(req,c,engine.specs['plain'],p['budget']),'backend_input_binding')
        check(b.model is None,'real adapter loaded mutated input')
    else:raise AssertionError('unknown orchestration case')
    return dict(id=f'H{i+1:02d}',status='pass',scope='software-only,no real model output')
