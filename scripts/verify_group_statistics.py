"""Independent readback: no imports from the statistics module or fixture runner."""
import sys
sys.dont_write_bytecode = True
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import signal
import time


def check(test, message):
    if not test:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def same(actual, expected, location='value'):
    if isinstance(expected, dict):
        check(isinstance(actual, dict) and set(actual) == set(expected), location + ':keys')
        for key in expected:
            same(actual[key], expected[key], location + '.' + key)
    elif isinstance(expected, list):
        check(isinstance(actual, list) and len(actual) == len(expected), location + ':length')
        for i, value in enumerate(expected):
            same(actual[i], value, location + '.' + str(i))
    elif type(expected) in (int, float):
        check(type(actual) in (int, float) and math.isfinite(actual) and abs(actual - expected) < 1e-12, location + ':number')
    else:
        check(type(actual) == type(expected) and actual == expected, location + ':exact')


def percentile(values, numerator):
    ordered = sorted(values)
    position = Fraction((len(ordered) - 1) * numerator, 1000)
    low = position.numerator // position.denominator
    high = min(len(ordered) - 1, low + 1)
    return float(Fraction(ordered[low]) * (1 - (position - low)) + Fraction(ordered[high]) * (position - low))


def audit_report(data, report):
    """Recalculate scalar estimands directly from serialized software rows."""
    cases = sorted(data['plan']['cases'], key=lambda c: c['context_group_id'])
    names = sorted(data['plan']['conditions'])
    n = len(cases)
    rows = {(r['case_id'], r['condition_id']): r for r in data['records']}
    check(len(rows) == n * len(names), 'audit_fixture_grid')
    check(report['groups'] == n and report['planned_cells'] == len(rows), 'report_denominator')
    counts = {}
    scores = {}
    semantic = {}
    for name in names:
        selected = [rows[c['case_id'], name] for c in cases]
        raw = [r['task_EM'] for r in selected if r['execution_state'] == 'ok' and r['task_EM'] is not None]
        strict = [r['task_EM'] for r in selected if r['execution_state'] == 'ok' and r['truncated'] is False and r['task_EM'] is not None]
        scores[name] = [None if r['execution_state'] in ('not_run', 'protocol_stopped') else
                        int(r['execution_state'] == 'ok' and r['truncated'] is False and r['format'] is True and r['task_EM'] == 1) for r in selected]
        semantic[name] = [r['task_EM'] if r['execution_state'] == 'ok' and r['truncated'] is False else None for r in selected]
        counts[name] = dict(scheduled=n, execution_counts=dict(Counter(r['execution_state'] for r in selected)),
            budget_infeasible=sum(r['budget_state'] == 'infeasible_budget' for r in selected),
            truncated=sum(r['execution_state'] == 'ok' and r['truncated'] is True for r in selected),
            raw_task_count=len(raw), raw_task_sum=sum(raw), strict_task_count=len(strict), strict_task_sum=sum(strict),
            task_NA=sum(r['execution_state'] == 'ok' and r['task_EM'] is None for r in selected),
            observed_joint_successes=sum(x == 1 for x in scores[name]), joint_rate=None)
    complete = data['phase'] == 'complete' and data['full_support'] is True and all(x is not None for v in scores.values() for x in v)
    if not complete:
        same(report['conditions'], counts)
        check(report['status'] == 'descriptive_only' and report['comparisons'] is None and report['bootstrap'] is None, 'incomplete_must_not_have_estimates')
        return
    for name in counts:
        counts[name]['joint_rate'] = sum(scores[name]) / n
    same(report['conditions'], counts)
    vectors = {name: [b - a for a, b in zip(scores['full'], scores[name])] for name in names if name != 'full'}
    # Recreate every shared draw independently and use rational type7 interpolation.
    distributions = {name: [] for name in vectors}
    rng = random.Random(20261030)
    stream_hash = hashlib.sha256()
    for _ in range(10000):
        indices = [rng.randrange(n) for unused in range(n)]
        stream_hash.update((json.dumps(indices, separators=(',', ':')) + '\n').encode())
        for name, values in vectors.items():
            distributions[name].append(sum(values[i] for i in indices) / n)
    bootstrap = dict(resamples=10000, seed=20261030, draw_mode='seeded', draw_sha256=stream_hash.hexdigest(),
        group_order=[c['context_group_id'] for c in cases], quantile='type7', interval='95% pointwise percentile',
        paired_shared_indices=True, simultaneous_interval=False, risk_certificate=False,
        methods={name: dict(delta=sum(values) / n, ci95=[percentile(distributions[name], 25), percentile(distributions[name], 975)]) for name, values in vectors.items()})
    same(report['bootstrap'], bootstrap)
    check(report['status'] == 'complete' and set(report['comparisons']) == set(vectors), 'complete_methods')
    for name, values in vectors.items():
        pairs = [(a, b) for a, b in zip(semantic['full'], semantic[name]) if a is not None and b is not None]
        transitions = {key: sum((('C' if a else 'W') + '2' + ('C' if b else 'W')) == key for a, b in pairs) for key in ('C2C', 'C2W', 'W2C', 'W2W')}
        denominator = sum(a == 1 for a, b in pairs)
        full_correct = sum(a == 1 for a in semantic['full'])
        damaged = transitions['C2W']
        expected = dict(groups=n, joint_delta=sum(values) / n, strict_task_pairs=len(pairs), unavailable_task_pairs=n - len(pairs),
            transitions=transitions, available_Full_correct=full_correct, eligible_Full_correct_pairs=denominator,
            unassessed_Full_correct=full_correct - denominator,
            strict_conditional_damage=damaged / denominator if denominator else None,
            all_Full_correct_damage_bounds=[damaged / full_correct, (damaged + full_correct - denominator) / full_correct] if full_correct else None,
            coverage_bounds_are_not_CI=True, joint_delta_ci95=bootstrap['methods'][name]['ci95'])
        same(report['comparisons'][name], expected)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--registration-sha256', required=True)
    args = parser.parse_args()
    start = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *unused: (_ for _ in ()).throw(TimeoutError('verification_CPU60_cap')))
    signal.alarm(60)
    root = Path(__file__).resolve().parent.parent
    check(str(root) == '/home/user/jhk/project/Directional Exploration/kv-pruning', 'server_only')
    out = (root / args.run).resolve()
    check(out.parent == (root / 'results').resolve(), 'output_boundary')
    reg_raw = (out / 'execution_registration.json').read_bytes()
    check(sha(reg_raw) == args.registration_sha256, 'registration_pin')
    reg = json.loads(reg_raw)
    cfg = read(out / 'proposal_snapshot.json')
    check(sha((out / 'proposal_snapshot.json').read_bytes()) == reg['proposal_sha256'], 'proposal_pin')
    check(out == root / cfg['run'], 'registered_run')
    for name, pin in read(out / 'manifest.json').items():
        check(sha((out / name).read_bytes()) == pin, 'manifest:' + name)
    for rel, pin in reg['source_sha256'].items():
        check(sha((root / rel).read_bytes()) == pin and sha((out / ('source_' + Path(rel).name)).read_bytes()) == pin, 'source:' + rel)
    for rel, pin in cfg['inputs'].items():
        check(sha((root / rel).read_bytes()) == pin, 'input:' + rel)
    check(read(out / 'summary.json')['status'] == 'complete', 'worker_complete')
    check(not any(read(out / 'CPU_guard_observations.json').values()), 'worker_guard')
    fixtures = read(out / 'software_fixtures.json')
    results = read(out / 'software_results.json')
    check([x['id'] for x in fixtures] == [x['id'] for x in results] == ['G%02d' % i for i in range(1, 19)], '18cases_exactly_once')
    check([x['id'] for x in fixtures] == [x['id'] for x in cfg['acceptance_cases']], 'proposal_cases')
    for spec, result in zip(fixtures, results):
        check(result['passed'] is True and result['action'] == spec['action'], 'case_pass')
        action = spec['action']
        value = result['output']
        if action == 'summary':
            audit_report(spec['input'], value)
        elif action == 'reject':
            known = {'G09': (['duplicate_cell'], ['duplicate_cell']), 'G10': (['missing_cell'], ['missing_planned_cell']),
                     'G11': (['input_digest', 'gold_digest', 'comparison_digest'], ['pair_identity_mismatch'] * 3),
                     'G12': (['duplicate_group', 'cross_role', 'excluded_group', 'duplicate_case'], ['duplicate_or_cross_role_group', 'case_cohort_or_role', 'duplicate_or_cross_role_group', 'duplicate_case']),
                     'G13': (['bool_EM', 'bool_F1', 'nan_F1', 'inf_F1'], ['metric_number'] * 4)}
            mutations, errors = known[spec['id']]
            same(spec['mutations'], mutations)
            same(spec['expected'], errors)
            same(value, [dict(mutation=m, error=e) for m, e in zip(mutations, errors)])
        elif action == 'exact_bootstrap':
            same(spec['vectors'], {'adapted_snapkv': [-1, 1]})
            same(spec['draws'], [[0, 0], [0, 1], [1, 0], [1, 1]])
            exact = [-1, 0, 0, 1]
            same(value['methods'], {'adapted_snapkv': dict(delta=0, ci95=[percentile(exact, 25), percentile(exact, 975)])})
            check(value['resamples'] == 4 and value['draw_mode'] == 'explicit' and value['seed'] is None, 'exact_not_10000_claim')
        elif action == 'reproducibility':
            check(len(value) == 3 and value[0] == value[1] == value[2], 'permutation_results')
            for report in value:
                audit_report(spec['input'], report)
        elif action == 'incomplete':
            check(len(value) == len(spec['inputs']) == 3, 'stopping_variants')
            check(spec['inputs'][0]['full_support'] is False and spec['inputs'][1]['phase'] == 'protocol_stopped'
                  and any(r['execution_state'] == 'not_run' for r in spec['inputs'][2]['records']), 'stopping_inputs')
            for data, report in zip(spec['inputs'], value):
                audit_report(data, report)
        elif action == 'quantiles':
            same(spec['values'], [0, 1])
            same(spec['probabilities'], [0, 1, .25])
            same(value, [0, 1, .25])
        elif action == 'native_pending_only':
            rel = next(p for p in cfg['inputs'] if p.endswith('planned_cells_with_budgets.jsonl'))
            cells = [json.loads(line) for line in (root / rel).read_text().splitlines()]
            check(len(cells) == 144 and len({(c['case_id'], c['condition_id']) for c in cells}) == 144, 'native144')
            check(len({c['case_id'] for c in cells}) == len({c['context_group_id'] for c in cells}) == 48, 'native48groups')
            check(all(c['execution_state'] == 'not_run' and c['model_called'] is False and all(x is None for x in c['metrics'].values()) for c in cells), 'native_no_answers')
            same(value, read(out / 'native48_pending_coverage.json'))
            check(value['groups'] == 48 and value['planned_cells'] == 144 and value['status'] == 'descriptive_only'
                  and value['comparisons'] is None and value['bootstrap'] is None, 'native_no_effects')
            for name in ('full', 'adapted_snapkv', 'uniform_random'):
                selected = [c for c in cells if c['condition_id'] == name]
                expected_blocked = 0 if name == 'full' else 3
                check(len(selected) == 48 and sum(c['budget_state'] == 'infeasible_budget' for c in selected) == expected_blocked, 'native_budget')
                rec = value['conditions'][name]
                check(rec['execution_counts'] == {'not_run': 48} and rec['budget_infeasible'] == expected_blocked
                      and rec['raw_task_count'] == rec['strict_task_count'] == 0 and rec['joint_rate'] is None, 'native_counts')
        else:
            raise ValueError('unknown_fixture')
    by = {r['id']: r['output'] for r in results}
    check(by['G01']['comparisons']['adapted_snapkv']['joint_delta'] == 0 and by['G01']['comparisons']['uniform_random']['joint_delta'] == -.5, 'gold_G01')
    for gid, want in [('G03', 0), ('G04', 1), ('G05', -1)]:
        check(all(x['joint_delta'] == want and x['joint_delta_ci95'] == [want, want] for x in by[gid]['comparisons'].values()), 'gold_' + gid)
    check(by['G06']['comparisons']['adapted_snapkv']['strict_task_pairs'] == 1 and by['G07']['conditions']['adapted_snapkv']['raw_task_sum'] == 2
          and by['G07']['conditions']['adapted_snapkv']['strict_task_count'] == 1 and by['G08']['conditions']['adapted_snapkv']['task_NA'] == 1, 'gold_NA_truncation')
    check(all(v['strict_conditional_damage'] is None for v in by['G16']['comparisons'].values()), 'gold_zero_denominator')
    check(not any(n.startswith(('reliability_group_statistics', 'accept_group_statistics', 'torch', 'transformers', 'tokenizers')) for n in sys.modules), 'independent_no_project_or_model_import')
    summary = dict(passed=True, method='Independent serialized-fixture scalar recomputation, full shared-draw stream digest and rational type7 interpolation; no statistics/runner imports',
        cases=18, rejecting_mutations=13, complete_synthetic_reports_recomputed=11, inputs_rehashed=len(cfg['inputs']),
        actual48_groups=48, actual48_planned_cells=144, actual48_effect_estimates=0,
        model_answers=0, tokenizer_encodes=0, GPU_queries=0, weight_bytes_read=0, network_requests=0,
        original_manifest_sha256=sha((out / 'manifest.json').read_bytes()), pid=__import__('os').getpid(), elapsed_seconds=time.monotonic() - start)
    signal.alarm(0)
    (out / 'independent_verification.json').write_text(json.dumps(summary, sort_keys=True, indent=2) + '\n')
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
