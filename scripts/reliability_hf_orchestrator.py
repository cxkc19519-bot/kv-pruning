"""Stage-aware orchestration, input binding and lazy backend dispatch; stdlib."""
import copy
import time
from reliability_system_core import digest, require
from reliability_system_adapters import hash_json
from reliability_execution_contract import (condition_fingerprint,plan_case,
    engineering_evidence,admission,execute_admitted)

VERSION='hf_orchestration_v1'


def case_binding(case):
    require(case.get('split_role') in ['engineering','development'],'sealed_or_unknown_role')
    ids=case.get('input_ids');n=case.get('prefix_tokens')
    require(isinstance(ids,list) and ids and all(type(x) is int and x>=0 for x in ids),'invalid_input_ids')
    require(type(n) is int and 0<n<len(ids),'invalid_prefix_boundary')
    require(digest(case.get('prompt_sha256')),'invalid_prompt_identity')
    require(digest(case.get('context_group_id')),'invalid_context_group_identity')
    require(isinstance(case.get('header_ids'),list) and all(type(i) is int and 0<=i<n for i in case['header_ids']),'invalid_system_positions')
    return hash_json({k:case[k] for k in ['case_id','split_role','input_ids','prefix_tokens','header_ids','prompt_sha256','context_group_id']})


class HFOrchestrator:
    def __init__(self,cases,specs,runtime_digest,policy,backend_factory=None):
        require(digest(runtime_digest),'runtime_digest')
        self.runtime=runtime_digest;self.policy=copy.deepcopy(policy);self.factory=backend_factory
        require(policy.get('mode') in ['dry_run','software_fixture','registered_gpu'],'orchestration_mode')
        require(type(policy.get('max_engineering_calls')) is int and policy['max_engineering_calls']>=0 and type(policy.get('max_DEV_calls')) is int and policy['max_DEV_calls']>=0,'call_caps')
        require(type(policy.get('wall_seconds')) in (int,float) and policy['wall_seconds']>0,'wall_cap')
        self.cases={};self.bindings={};self.specs={};self.obs={};self.executed=set()
        for c in cases:
            cid=c['case_id'];require(cid not in self.cases,'duplicate_case')
            self.bindings[cid]=case_binding(c);require(len(c['input_ids'])<=policy.get('max_input_tokens',2048),'prepared_input_token_cap');self.cases[cid]=copy.deepcopy(c)
        require(self.cases,'empty_case_plan')
        for s in specs:
            name=s['condition_id'];require(name not in self.specs,'duplicate_condition')
            condition_fingerprint(s,runtime_digest);self.specs[name]=copy.deepcopy(s);self.obs[name]=[]
        require('full' in self.specs,'Full_condition_required')
        for s in specs:require(len([c for c in cases if c['split_role']=='engineering'])==s['engineering_cases_required'],'engineering_case_plan_count')
        self.backend=None;self.loader_attempts=0;self.backend_calls=0;self.phase_calls=dict(engineering=0,development=0)
        self.failed=False;self.started=time.monotonic()

    def _plan(self,case,name):
        return plan_case(case['case_id'],case['prefix_tokens'],case['header_ids'],self.specs[name],self.runtime)

    def evidence(self,name):
        spec=self.specs[name]
        eng=[self._plan(c,name) for c in self.cases.values() if c['split_role']=='engineering']
        return engineering_evidence(spec,self.runtime,eng,self.obs[name])

    def offer_evidence(self,evidence):
        """Only diagnoses reuse eligibility; evidence must be produced via dispatch."""
        name=evidence['condition_id'];require(name in self.specs,'unknown_evidence_condition')
        require(evidence['condition_fingerprint']==condition_fingerprint(self.specs[name],self.runtime),'stale_engineering_for_new_backend')
        require(evidence==self.evidence(name),'evidence_not_produced_by_current_stage')
        return True

    def request(self,cid,name,phase,path):
        require(cid in self.cases and name in self.specs,'unplanned_cell')
        case=self.cases[cid];spec=self.specs[name]
        require(phase in ['engineering','development'] and case['split_role']==phase,'stage_role_mismatch')
        allowed=spec['required_paths'] if phase=='engineering' else (['custom_split'] if name=='full' else ['custom'])
        require(path in allowed,'stage_path_mismatch')
        req=dict(version=VERSION,case_id=cid,condition_id=name,phase=phase,path=path,
            case_input_digest=self.bindings[cid],runtime_digest=self.runtime,
            condition_fingerprint=condition_fingerprint(spec,self.runtime))
        req['request_digest']=hash_json(req)
        return req

    def _validate_request(self,req):
        body={k:v for k,v in req.items() if k!='request_digest'}
        require(hash_json(body)==req['request_digest'],'mutated_dispatch_request')
        expected=self.request(req['case_id'],req['condition_id'],req['phase'],req['path'])
        require(req==expected,'dispatch_scope_mismatch')
        require(case_binding(self.cases[req['case_id']])==req['case_input_digest'],'mutated_prepared_input')

    def decision(self,req):
        self._validate_request(req);c=self.cases[req['case_id']];p=self._plan(c,req['condition_id'])
        if req['phase']=='development':d=admission(p,self.evidence(req['condition_id']))
        else:
            feasible=p['budget']['state']=='ok'
            d=dict(launch_allowed=feasible,admission_state='eligible_bootstrap_under_separate_protocol' if feasible else 'blocked_budget',
                reason=None if feasible else 'required_union_exceeds_requested_slots',
                evidence_scope='Bootstrap engineering only;no DEV permission implied')
        return dict(request=copy.deepcopy(req),case_plan=p,decision=d)

    def dispatch(self,req):
        require(not self.failed,'orchestrator_halted_after_failure')
        item=self.decision(req);d=item['decision']
        if not d['launch_allowed']:return dict(state='blocked',decision=item,model_called=False)
        if self.policy['mode']=='dry_run':return dict(state='planned_no_execution',decision=item,model_called=False)
        phase=req['phase'];enabled='bootstrap_generation_enabled' if phase=='engineering' else 'DEV_generation_enabled'
        require(self.policy.get('execution_enabled') is True and self.policy.get(enabled) is True,'stage_execution_disabled')
        require(self.policy.get('runtime_digest')==self.runtime,'policy_runtime_mismatch')
        require(time.monotonic()-self.started<=self.policy['wall_seconds'],'orchestration_wall_cap')
        cap='max_engineering_calls' if phase=='engineering' else 'max_DEV_calls'
        require(self.phase_calls[phase]<self.policy[cap],'orchestration_call_cap')
        require(req['request_digest'] not in self.executed,'duplicate_model_dispatch')
        require(self.factory is not None,'missing_backend_factory')
        # Both request/input validation and all gates precede construction/import/load.
        self.executed.add(req['request_digest']);self.phase_calls[phase]+=1
        try:
            if self.backend is None:
                self.loader_attempts+=1;self.backend=self.factory()
                expected_kind='software_stub' if self.policy['mode']=='software_fixture' else 'real_hf'
                require(getattr(self.backend,'kind',None)==expected_kind,'backend_kind_mismatch')
            self.backend_calls+=1
            c=copy.deepcopy(self.cases[req['case_id']]);spec=copy.deepcopy(self.specs[req['condition_id']])
            run=lambda:self.backend.execute(copy.deepcopy(req),c,spec,copy.deepcopy(item['case_plan']['budget']))
            result=execute_admitted(d,run) if phase=='development' else run()
            require(result.get('request_digest')==req['request_digest'],'backend_result_request_mismatch')
            require(result.get('execution_state')=='ok','backend_execution_failed')
            require(isinstance(result.get('ids'),list) and result['ids'] and all(type(x) is int and x>=0 for x in result['ids']),'backend_token_sequence')
            require(type(result.get('truncated')) is bool,'backend_termination_flag')
            if phase=='engineering':
                self.obs[req['condition_id']].append(dict(case_id=req['case_id'],path=req['path'],
                    condition_fingerprint=req['condition_fingerprint'],case_input_digest=req['case_input_digest'],
                    execution_state='ok',ids=result['ids'],trace=result.get('trace'),truncated=result['truncated']))
                require(self.evidence(req['condition_id'])['status']!='failed','engineering_sequence_mismatch')
            return dict(state='executed',result=result,decision=item,model_called=self.policy['mode']=='registered_gpu')
        except BaseException:
            self.failed=True;raise

    def dry_run_plan(self):
        require(self.policy['mode']=='dry_run','dry_run_mode_required')
        eng=[];dev=[]
        for c in self.cases.values():
            for name,spec in self.specs.items():
                if c['split_role']=='engineering':
                    p=self._plan(c,name)
                    if p['budget']['state']=='infeasible_budget':
                        eng.append(dict(case_id=c['case_id'],condition_id=name,state='blocked_budget',case_plan=p));continue
                    for path in spec['required_paths']:
                        req=self.request(c['case_id'],name,'engineering',path);eng.append(self.dispatch(req))
                else:
                    path='custom_split' if name=='full' else 'custom'
                    req=self.request(c['case_id'],name,'development',path);dev.append(self.dispatch(req))
        return dict(version=VERSION,engineering=eng,development=dev,
            current_evidence=[self.evidence(n) for n in self.specs],loader_attempts=self.loader_attempts,
            backend_calls=self.backend_calls,real_model_called=False,
            note='Bootstrap requests are only a future bounded-stage plan. No engineering observations are manufactured by dry-run.')
