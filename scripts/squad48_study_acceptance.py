"""Synthetic integration fixtures. No torch/tokenizer/model imports."""
import copy
import hashlib
import json
from reliability_system_core import require, ContractError
from reliability_system_adapters import hash_json
from reliability_hf_orchestrator import HFOrchestrator, case_binding
from reliability_execution_contract import plan_case
from reliability_squad48_study import StudyDispatcher, ROLE, NAMES, scalar_report


def run_acceptance(specs):
    runtime = 'a' * 64
    answers = [dict(text='alpha', answer_start=0)]
    gold_sha = hashlib.sha256(json.dumps(answers, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    tests = []

    class Stub:
        kind = 'software_stub'
        def __init__(self):
            self.calls = 0
            self.truncated = False
        def execute(self, req, case, spec, budget):
            self.calls += 1
            trace = [dict(step=0, physical_start=budget['effective_slots'], logical_start=case['prefix_tokens'], input_width=len(case['input_ids']) - case['prefix_tokens'])]
            return dict(request_digest=req['request_digest'], execution_state='ok', ids=[42 if self.truncated else 151645],
                        truncated=self.truncated, trace=trace if req['path'] not in ('native_whole', 'native_split') else None,
                        actual_prefix_kv_bytes=budget['effective_slots'] * 57344,
                        final_live_kv_bytes=(budget['effective_slots'] + len(case['input_ids']) - case['prefix_tokens']) * 57344)

    def make(stage='all', change=None, cap=138):
        eng = [dict(case_id='eng' + str(i), split_role='engineering', input_ids=[1] * 170, prefix_tokens=160,
                    header_ids=list(range(56)), prompt_sha256=hash_json(['eng', i]), context_group_id=hash_json(['enggroup', i])) for i in range(2)]
        stub = Stub()
        policy = dict(mode='software_fixture', execution_enabled=True, bootstrap_generation_enabled=True, DEV_generation_enabled=False,
                      runtime_digest=runtime, max_engineering_calls=14, max_DEV_calls=0, wall_seconds=600, max_input_tokens=2048)
        engine = HFOrchestrator(eng, specs, runtime, policy, lambda: stub)
        for case in eng:
            for spec in specs:
                if stage == 'none' or stage == 'full' and spec['condition_id'] != 'full':
                    continue
                for path in spec['required_paths']:
                    engine.dispatch(engine.request(case['case_id'], spec['condition_id'], 'engineering', path))
        cases = [dict(case_id='main' + str(i), split_role=ROLE, input_ids=[2] * (n + 10), prefix_tokens=n,
                      header_ids=list(range(56)), prompt_sha256=hash_json(['main', i]), gold_sha256=gold_sha,
                      context_group_id=hash_json(['maingroup', i])) for i, n in enumerate((160, 100))]
        plans = []
        for case in cases:
            for spec in specs:
                p = plan_case(case['case_id'], case['prefix_tokens'], case['header_ids'], spec, runtime)
                plans.append(dict(p, cohort_id='software_only_study', role=ROLE, context_group_id=case['context_group_id'],
                                  prompt_sha256=case['prompt_sha256'], gold_sha256=gold_sha, input_ids_sha256=hash_json(case['input_ids'])))
        if change:
            change(cases, plans, engine)
        main_backend = Stub()
        controller = StudyDispatcher(cases, plans, specs, runtime, engine, main_backend, ['main0', 'main1'], 'software_only_study', mode='software_fixture', call_cap=cap)
        return controller, main_backend

    def good_full(controller, backend, text='{"answer":"alpha"}'):
        for cid in controller.cases:
            response = controller.dispatch(cid, 'full')
            controller.accept(cid, 'full', response['result'], text, answers)

    def reject(label, operation):
        try:
            operation()
        except ContractError as exc:
            tests.append(dict(id=label, passed=True, rejected=True, reason=str(exc), real_model_calls=0))
        else:
            raise ValueError(label + ':expected_rejection')

    c, b = make()
    good_full(c, b)
    gate = dict(task_min=1, format_min=1, errors_max=0, truncated_max=0)
    require(c.finalize_full(gate)['passed'], 'fixture_Full_pass')
    for name in NAMES[1:]:
        response = c.dispatch('main0', name)
        c.accept('main0', name, response['result'], '{"answer":"alpha"}', answers)
        before = b.calls
        require(c.dispatch('main1', name)['state'] == 'blocked' and b.calls == before, 'fixture_budget_block_calls')
    plan, rows, stats = c.statistics()
    scalar_plan, normalized, report = scalar_report(c, rows)
    require(len(rows) == 6 and b.calls == 4 and stats['status'] == 'complete'
            and all(x['joint_delta'] == -.5 for x in stats['comparisons'].values())
            and report['case_count'] == 2 and len(normalized) == 6, 'fixture_pipeline')
    tests.append(dict(id='S01', passed=True, synthetic_main_calls=b.calls, real_model_calls=0, budget_blocks=2, joint_delta=-.5))
    reject('S02', lambda: make(change=lambda cases, plans, engine: cases[0].update(split_role='development')))
    reject('S03', lambda: make(change=lambda cases, plans, engine: cases[1].update(context_group_id=cases[0]['context_group_id'])))
    reject('S04', lambda: make(change=lambda cases, plans, engine: plans[0].update(input_ids_sha256='f' * 64)))
    reject('S05', lambda: make(change=lambda cases, plans, engine: engine.__setattr__('runtime', 'f' * 64)))
    c, b = make(stage='none')
    require(c.dispatch('main0', 'full')['state'] == 'blocked' and b.calls == 0, 'unverified_engineering_block')
    tests.append(dict(id='S06', passed=True, real_model_calls=0, synthetic_main_calls=0))
    reject('S07', lambda: c.dispatch('main0', 'adapted_snapkv'))
    c, b = make(); good_full(c, b)
    reject('S08', lambda: c.dispatch('main0', 'full'))
    c, b = make(); c.cases['main0']['input_ids'][0] += 1
    reject('S09', lambda: c.dispatch('main0', 'full'))
    c, b = make(); response = c.dispatch('main0', 'full')
    altered = copy.deepcopy(response['result']); altered['ids'][0] += 1
    reject('S10', lambda: c.accept('main0', 'full', altered, '{"answer":"alpha"}', answers))
    reject('S11', lambda: c.accept('main0', 'full', response['result'], '{"answer":"alpha"}', [dict(text='beta', answer_start=0)]))
    c, b = make(); good_full(c, b, '[1]')
    require(c.finalize_full(gate)['passed'] is False, 'fixture_Full_failure')
    require(c.statistics(stopped=True)[2]['bootstrap'] is None, 'fixture_failure_CI')
    reject('S12', lambda: c.dispatch('main0', 'uniform_random'))
    c, b = make(); b.truncated = True; good_full(c, b)
    require(c.finalize_full(gate)['counts']['task'] == 0 and all(r['task_EM'] == 1 for r in c.results.values()), 'fixture_truncation_raw_preserved')
    tests.append(dict(id='S13', passed=True, real_model_calls=0, raw_correct=2, completed_correct=0))
    c, b = make(cap=1); response = c.dispatch('main0', 'full')
    c.accept('main0', 'full', response['result'], '{"answer":"alpha"}', answers)
    reject('S14', lambda: c.dispatch('main1', 'full'))
    reject('S15', lambda: c.finalize_full(gate))
    reject('S16', lambda: case_binding(c.cases['main0']))
    require([t['id'] for t in tests] == ['S%02d' % i for i in range(1, 17)], 'fixed_software_cases')
    return tests
