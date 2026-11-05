"""Condition-level admission and scoped engineering evidence; no model I/O."""
from reliability_system_core import budget_plan, digest, require
from reliability_system_adapters import hash_json

VERSION = 'condition_admission_v1'


def condition_fingerprint(spec, runtime_digest):
    require(digest(runtime_digest), 'invalid_runtime_digest')
    require(isinstance(spec.get('condition_id'),str) and spec['condition_id'], 'condition_identity')
    require(type(spec.get('protect_system')) is bool, 'protection_mode')
    require(type(spec.get('engineering_cases_required')) is int and spec['engineering_cases_required']>0,'engineering_case_requirement')
    paths=spec.get('required_paths')
    require(paths and len(paths)==len(set(paths)) and all(isinstance(x,str) and x for x in paths),'required_path_plan')
    require(type(spec.get('compare_trace')) is bool,'trace_comparison_flag')
    require(spec.get('selector_version_digest') and digest(spec['selector_version_digest']),'selector_version')
    return hash_json(dict(version=VERSION,runtime_digest=runtime_digest,condition=spec))


def plan_case(case_id, prefix_tokens, system_positions, spec, runtime_digest):
    protected=system_positions if spec['protect_system'] else []
    budget=budget_plan(prefix_tokens,spec['retention'],protected,spec['sink'],spec['recent'])
    return dict(case_id=case_id,condition_id=spec['condition_id'],
        condition_fingerprint=condition_fingerprint(spec,runtime_digest),budget=budget)


def engineering_evidence(spec, runtime_digest, engineering_plans, observations):
    fp=condition_fingerprint(spec,runtime_digest)
    require(len(engineering_plans)==spec['engineering_cases_required'],'engineering_plan_count')
    by_case={x['case_id']:x for x in engineering_plans}
    require(len(by_case)==len(engineering_plans),'duplicate_engineering_case')
    require(all(x['condition_id']==spec['condition_id'] and x['condition_fingerprint']==fp for x in engineering_plans),'engineering_plan_scope_mismatch')
    by={}
    for obs in observations:
        require(obs['case_id'] in by_case,'unplanned_engineering_case')
        require(obs['condition_fingerprint']==fp,'stale_or_foreign_engineering_scope')
        path=obs.get('path')
        require(path in spec['required_paths'] or path is None and obs['execution_state']=='infeasible_budget','unexpected_engineering_path')
        key=(obs['case_id'],path);require(key not in by,'duplicate_engineering_observation');by[key]=obs
    cases=[]
    for cid,plan in by_case.items():
        obs=[x for (c,p),x in by.items() if c==cid]
        if plan['budget']['state']=='infeasible_budget':
            require(all(x['execution_state']=='infeasible_budget' for x in obs),'generated_engineering_on_infeasible_budget')
            cases.append(dict(case_id=cid,status='budget_infeasible',generated_paths=0,
                verified=False,output_complete=None,reason='no_executable_engineering_case'))
            continue
        require(not any(x['execution_state']=='infeasible_budget' for x in obs),'false_engineering_infeasibility')
        paths=[by.get((cid,p)) for p in spec['required_paths']]
        if any(x and x['execution_state']=='error' for x in paths):
            cases.append(dict(case_id=cid,status='execution_error',verified=False,output_complete=None,generated_paths=sum(bool(x and x['execution_state']=='ok') for x in paths)))
            continue
        if any(x is None or x['execution_state']!='ok' for x in paths):
            cases.append(dict(case_id=cid,status='missing_path',verified=False,output_complete=None,generated_paths=sum(bool(x and x['execution_state']=='ok') for x in paths)))
            continue
        for x in paths:
            require(isinstance(x.get('ids'),list) and x['ids'] and all(type(v) is int and v>=0 for v in x['ids']),'invalid_engineering_token_sequence')
            require(type(x.get('truncated')) is bool and digest(x.get('case_input_digest')),'engineering_output_identity')
        same_identity=len({x['case_input_digest'] for x in paths})==1
        equal_ids=all(x['ids']==paths[0]['ids'] for x in paths)
        equal_termination=all(x['truncated']==paths[0]['truncated'] for x in paths)
        equal_trace=True
        if spec['compare_trace']:
            require(all(isinstance(x.get('trace'),list) and x['trace'] for x in paths),'missing_compact_position_trace')
            equal_trace=all(x['trace']==paths[0]['trace'] for x in paths)
        ok=same_identity and equal_ids and equal_termination and equal_trace
        cases.append(dict(case_id=cid,status='verified_at_decode_cap' if ok else 'path_mismatch',verified=ok,
            generated_paths=len(paths),output_complete=not any(x['truncated'] for x in paths),
            input_identity_equal=same_identity,token_sequences_equal=equal_ids,termination_equal=equal_termination,
            position_trace_equal=equal_trace if spec['compare_trace'] else None))
    verified=sum(x['verified'] for x in cases)
    infeasible=sum(x['status']=='budget_infeasible' for x in cases)
    failed=any(x['status'] in ['path_mismatch','execution_error'] for x in cases)
    state='failed' if failed else ('verified' if verified==len(cases) else ('unverified_budget_infeasible' if infeasible==len(cases) else 'insufficient_coverage'))
    return dict(version=VERSION,condition_id=spec['condition_id'],condition_fingerprint=fp,
        status=state,path_sequences_verified=state=='verified',required_engineering_cases=len(cases),
        verified_engineering_cases=verified,infeasible_engineering_cases=infeasible,
        sequence_verified_but_truncated_cases=sum(x['verified'] and x['output_complete'] is False for x in cases),
        cases=cases,scope='Only listed engineering cases at this exact runtime/selector/protection/retention/decode contract; not task support or all future inputs')


def admission(case_plan,evidence):
    require(case_plan['condition_id']==evidence['condition_id'] and case_plan['condition_fingerprint']==evidence['condition_fingerprint'],'admission_evidence_scope_mismatch')
    require(evidence.get('version')==VERSION,'engineering_evidence_version')
    cases=evidence.get('cases',[])
    require(cases and len(cases)==evidence['required_engineering_cases'] and len({x['case_id'] for x in cases})==len(cases),'engineering_evidence_case_coverage')
    verified=sum(x['verified'] is True for x in cases)
    infeasible=sum(x['status']=='budget_infeasible' for x in cases)
    failed=any(x['status'] in ['path_mismatch','execution_error'] for x in cases)
    expected='failed' if failed else ('verified' if verified==len(cases) else ('unverified_budget_infeasible' if infeasible==len(cases) else 'insufficient_coverage'))
    require(evidence['status']==expected and evidence['verified_engineering_cases']==verified and evidence['infeasible_engineering_cases']==infeasible and evidence['path_sequences_verified']==(expected=='verified'),'engineering_evidence_summary_inconsistent')
    if case_plan['budget']['state']=='infeasible_budget':
        state,reason='blocked_budget','required_union_exceeds_requested_slots'
    elif evidence['status']=='failed':
        state,reason='blocked_engineering_failed','engineering_path_mismatch_or_error'
    elif evidence['status']!='verified' or evidence['path_sequences_verified'] is not True:
        state,reason='blocked_engineering_unverified','required_condition_engineering_not_verified'
    else:
        state,reason='eligible_for_configured_run',None
    return dict(version=VERSION,case_id=case_plan['case_id'],condition_id=case_plan['condition_id'],
        condition_fingerprint=case_plan['condition_fingerprint'],budget_state=case_plan['budget']['state'],
        evidence_state=evidence['status'],admission_state=state,launch_allowed=state=='eligible_for_configured_run',
        reason=reason,scope='Pre-execution eligibility, not a claim that this DEV output is path-verified or correct')


def execute_admitted(decision, operation):
    """Dispatcher boundary: blocked cells never call the model operation."""
    require(decision.get('launch_allowed') is True and decision.get('admission_state')=='eligible_for_configured_run','launch_blocked_by_condition_contract')
    return operation()


def historical_observation(decision, raw):
    """Annotate existing output without deleting, rescoring or rerunning it."""
    state='not_run' if raw is None else raw['status']
    if raw is not None:
        require(raw['case_id']==decision['case_id'] and raw['condition']==decision['condition_id'],'historical_cell_identity_mismatch')
    require(state in ['ok','not_run','error','infeasible_budget'],'unknown_archived_execution_state')
    if decision['budget_state']=='infeasible_budget':
        require(state!='ok','historical_generation_on_infeasible_budget')
    else:
        require(state!='infeasible_budget','historical_false_infeasibility')
    if state=='ok':
        require(type(raw.get('truncated')) is bool,'historical_truncation_flag')
    diagnostic=state=='ok' and not decision['launch_allowed']
    return dict(case_id=decision['case_id'],condition_id=decision['condition_id'],execution_state=state,
        actual_generated=state=='ok',truncated=raw.get('truncated') if raw else None,
        task_candidate_status=raw.get('metrics',{}).get('candidate_status') if raw else None,
        evidence_scope='historical_unverified_condition_diagnostic' if diagnostic else 'within_configured_admission' if state=='ok' else 'no_generated_output',
        historical_diagnostic_only=diagnostic,strict_future_launch_allowed=decision['launch_allowed'],
        archived_record_preserved=True,reason=raw.get('reason') if raw else 'scheduled_cell_missing')
