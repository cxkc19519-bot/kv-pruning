"""Separate registered reserved-cohort dispatcher and explicit scalar adapters.

The legacy engineering/DEV dispatcher keeps its original role restrictions.
This dispatcher consumes fresh evidence from the current engineering instance.
"""
import copy
import hashlib
import json
from reliability_system_core import require, digest, SCHEMA, metric, measure, summarize as core_summarize
from reliability_system_adapters import hash_json
from reliability_execution_contract import plan_case, admission
from reliability_hf_orchestrator import HFOrchestrator
from reliability_group_statistics import PLAN_SCHEMA, ROW_SCHEMA, summarize as group_summarize
from answer_format_task import score_response

ROLE = 'sealed_descriptive_evaluation'
NAMES = ('full', 'adapted_snapkv', 'uniform_random')
MATERIAL = ('case_id', 'split_role', 'input_ids', 'prefix_tokens', 'header_ids', 'prompt_sha256', 'context_group_id')


def binding(case):
    require(case.get('split_role') == ROLE, 'study_role')
    ids, n = case.get('input_ids'), case.get('prefix_tokens')
    require(isinstance(ids, list) and ids and all(type(x) is int and x >= 0 for x in ids) and len(ids) <= 2048, 'study_ids')
    require(type(n) is int and 0 < n < len(ids), 'study_boundary')
    require(all(digest(case.get(k)) for k in ('prompt_sha256', 'gold_sha256', 'context_group_id')), 'study_identity')
    require(isinstance(case.get('header_ids'), list) and all(type(i) is int and 0 <= i < n for i in case['header_ids']), 'study_header')
    return hash_json({k: case[k] for k in MATERIAL})


def identity(case, runtime, cohort):
    return dict(cohort_id=cohort, case_id=case['case_id'], context_group_id=case['context_group_id'], role=ROLE,
                input_digest=hash_json(case['input_ids']), gold_digest=case['gold_sha256'],
                comparison_digest=hash_json(dict(runtime=runtime, cohort=cohort, case_binding=binding(case))))


class StudyDispatcher:
    def __init__(self, cases, plans, specs, runtime, engineering, backend, expected_ids, cohort,
                 mode='registered_gpu', call_cap=138):
        require(mode in ('registered_gpu', 'software_fixture') and type(call_cap) is int and 0 < call_cap <= 138, 'study_mode_cap')
        require(digest(runtime) and isinstance(engineering, HFOrchestrator) and engineering.runtime == runtime, 'fresh_engineering_runtime')
        require(engineering.policy['mode'] == mode, 'engineering_mode')
        require(len(cases) == len(expected_ids) == len(set(expected_ids)) and [c['case_id'] for c in cases] == expected_ids, 'study_case_registry')
        require(mode != 'registered_gpu' or len(cases) == 48, 'registered48_only')
        require(len({c['context_group_id'] for c in cases}) == len(cases), 'study_group_duplicate')
        require(not ({c['context_group_id'] for c in cases} & {c['context_group_id'] for c in engineering.cases.values()}), 'study_engineering_group_overlap')
        self.cases = {c['case_id']: copy.deepcopy(c) for c in cases}
        self.bindings = {c['case_id']: binding(c) for c in cases}
        require(set(s['condition_id'] for s in specs) == set(NAMES) and len(specs) == 3, 'study_conditions')
        self.specs = {s['condition_id']: copy.deepcopy(s) for s in specs}
        require(all(not s['protect_system'] and s['sink'] == 4 and s['recent'] == 64 and s['retention'] == ('1' if s['condition_id'] == 'full' else '1/2') for s in specs), 'study_budget_policy')
        self.runtime, self.cohort, self.engineering, self.backend = runtime, cohort, engineering, backend
        self.plans = {}
        for p in plans:
            key = (p['case_id'], p['condition_id'])
            require(key not in self.plans and key[0] in self.cases and key[1] in self.specs, 'study_plan_registry')
            c = self.cases[key[0]]
            expected = plan_case(c['case_id'], c['prefix_tokens'], c['header_ids'], self.specs[key[1]], runtime)
            require(p['cohort_id'] == cohort and p['role'] == ROLE and p['context_group_id'] == c['context_group_id']
                    and p['prompt_sha256'] == c['prompt_sha256'] and p['gold_sha256'] == c['gold_sha256']
                    and p['input_ids_sha256'] == hash_json(c['input_ids']) and p['budget'] == expected['budget'], 'study_plan_input_or_budget')
            self.plans[key] = expected
        require(len(self.plans) == len(cases) * 3, 'study_plan_missing')
        self.calls = 0
        self.cap = call_cap
        self.attempted = set()
        self.results = {}
        self.returned = {}
        self.full_support = None

    def dispatch(self, cid, name):
        require((cid, name) in self.plans, 'study_foreign_cell')
        case = self.cases[cid]
        require(binding(case) == self.bindings[cid], 'study_input_mutated')
        require(name == 'full' or self.full_support is True, 'study_Full_support_required')
        item = self.plans[cid, name]
        evidence = self.engineering.evidence(name)
        decision = admission(item, evidence)
        if not decision['launch_allowed']:
            return dict(state='blocked', decision=decision, model_called=False)
        require((cid, name) not in self.attempted and self.calls < self.cap, 'study_duplicate_or_cap')
        path = 'custom_split' if name == 'full' else 'custom'
        request = dict(version='squad48_reserved_study_v1', case_id=cid, condition_id=name, phase=ROLE,
                       path=path, case_input_digest=self.bindings[cid], runtime_digest=self.runtime,
                       condition_fingerprint=item['condition_fingerprint'])
        request['request_digest'] = hash_json(request)
        self.attempted.add((cid, name)); self.calls += 1
        result = self.backend.execute(request, copy.deepcopy(case), copy.deepcopy(self.specs[name]), copy.deepcopy(item['budget']))
        require(result['request_digest'] == request['request_digest'] and result['execution_state'] == 'ok', 'study_result_scope')
        require(isinstance(result['ids'], list) and result['ids'] and len(result['ids']) <= 128 and all(type(x) is int and x >= 0 for x in result['ids']) and type(result['truncated']) is bool, 'study_result_sequence')
        require(result['actual_prefix_kv_bytes'] == item['budget']['effective_slots'] * 57344, 'study_actual_budget')
        self.returned[cid, name] = copy.deepcopy(result)
        return dict(state='executed', request=request, result=result, decision=decision)

    def accept(self, cid, name, result, text, answers):
        require((cid, name) in self.attempted and (cid, name) not in self.results, 'study_accept_once')
        case = self.cases[cid]
        require(result == self.returned.get((cid, name)), 'study_accepted_result_changed')
        require(hashlib.sha256(json.dumps(answers, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == case['gold_sha256'], 'study_gold_binding')
        scores = score_response(text, [a['text'] for a in answers])
        row = dict(identity(case, self.runtime, self.cohort), schema=ROW_SCHEMA, condition_id=name,
                   execution_state='ok', budget_state='ok', truncated=result['truncated'], format=scores['format'],
                   task_EM=None if scores['em'] is None else int(scores['em']), task_F1=scores['f1'],
                   task_EM_reason=scores['reason'] if scores['em'] is None else None,
                   task_F1_reason=scores['reason'] if scores['f1'] is None else None,
                   actual_prefix_kv_bytes=result['actual_prefix_kv_bytes'], final_live_kv_bytes=result['final_live_kv_bytes'])
        self.results[cid, name] = row
        return row, scores

    def finalize_full(self, gate):
        rows = [self.results.get((cid, 'full')) for cid in self.cases]
        require(all(r and r['execution_state'] == 'ok' for r in rows), 'study_Full_phase_incomplete')
        good = [r for r in rows if not r['truncated']]
        counts = dict(scheduled=len(rows), generated=len(rows), errors=0, task=sum(r['task_EM'] == 1 for r in good),
                      format=sum(r['format'] for r in good), joint=sum(r['format'] and r['task_EM'] == 1 for r in good),
                      truncated=sum(r['truncated'] for r in rows), candidates=sum(r['task_EM'] is not None for r in good))
        self.full_support = counts['task'] >= gate['task_min'] and counts['format'] >= gate['format_min'] and counts['errors'] <= gate['errors_max'] and counts['truncated'] <= gate['truncated_max']
        return dict(passed=self.full_support, counts=counts, thresholds=gate, score_scope='completed nontruncated outputs; truncation separately bounded')

    def matrix(self, stopped=False):
        output = []
        for cid, case in self.cases.items():
            for name in NAMES:
                if (cid, name) in self.results:
                    output.append(copy.deepcopy(self.results[cid, name])); continue
                budget = self.plans[cid, name]['budget']['state']
                state = 'infeasible_budget' if budget == 'infeasible_budget' else 'protocol_stopped' if stopped else 'not_run'
                output.append(dict(identity(case, self.runtime, self.cohort), schema=ROW_SCHEMA, condition_id=name,
                    execution_state=state, budget_state=budget, task_EM=None, task_F1=None, format=None, truncated=None,
                    actual_prefix_kv_bytes=None, final_live_kv_bytes=None,
                    reason='anchor_capacity' if state == 'infeasible_budget' else 'phase_stopped' if stopped else 'pending_phase'))
        return output

    def statistics(self, stopped=False):
        plan = dict(schema=PLAN_SCHEMA, cohort_id=self.cohort, role=ROLE, conditions=list(NAMES),
                    cases=[identity(c, self.runtime, self.cohort) for c in self.cases.values()])
        rows = self.matrix(stopped)
        phase = 'protocol_stopped' if stopped else 'complete' if len(self.results) + sum(p['budget']['state'] == 'infeasible_budget' for p in self.plans.values()) == len(self.plans) else 'pending'
        return plan, rows, group_summarize(plan, rows, phase, self.full_support)


def scalar_report(dispatcher, rows):
    normalized = []
    for row in rows:
        state = 'not_run' if row['execution_state'] == 'protocol_stopped' else row['execution_state']
        reason = row.get('reason', 'not_available')
        normalized.append(dict(schema=SCHEMA, cohort_id=row['cohort_id'], case_id=row['case_id'], condition_id=row['condition_id'],
            input_digest=row['input_digest'], gold_digest=row['gold_digest'], comparison_digest=row['comparison_digest'],
            execution_state=state, reason=reason, truncated=row['truncated'],
            metrics=dict(task=metric(None if row['task_EM'] is None else bool(row['task_EM']), 'squad_v11_bidaf_pinned_em_v1', reason=row.get('task_EM_reason') or reason),
                         f1=metric(row['task_F1'], 'squad_v11_bidaf_pinned_f1_v1', 'unit_interval', row.get('task_F1_reason') or reason),
                         constraint=metric(row['format'], 'json_answer_format_v1', reason=reason)),
            costs=dict(prefix_kv_bytes=measure(row['actual_prefix_kv_bytes'], 'no_output'), final_live_kv_bytes=measure(row['final_live_kv_bytes'], 'no_output'),
                       peak_gpu_bytes=measure(None, 'not_benchmarked'), latency_ms=measure(None, 'not_benchmarked'), extra_buffer_peak_bytes=measure(None, 'not_benchmarked'))))
    plan = dict(cohort_id=dispatcher.cohort, case_ids=list(dispatcher.cases),
                conditions=[dict(condition_id=name, budget_group=None if name == 'full' else 'half_prefix') for name in NAMES],
                metrics={k: dict(kind=v['kind'], metric_id=v['metric_id']) for k, v in normalized[0]['metrics'].items()},
                scientific_role=ROLE, context_group_ids=[c['context_group_id'] for c in dispatcher.cases.values()])
    report = core_summarize(plan, normalized)
    report.update(inference_performed=bool(dispatcher.results), task_text_rescored=bool(dispatcher.results), independent_confirmation=False)
    return plan, normalized, report
