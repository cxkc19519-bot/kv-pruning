"""Strict group-paired delivery statistics. Standard library; no model imports.

Inputs are an explicit group plan and one normalized outcome per planned cell.
Adapters must bind the plan to the registered input/gold/runtime identities.
This module validates scalar analysis contracts, not model or source evidence.
"""
from collections import Counter
import hashlib
import json
import math
import random

PLAN_SCHEMA = 'kv_group_plan_v1'
ROW_SCHEMA = 'kv_group_outcome_v1'
STATES = ('ok', 'infeasible_budget', 'error', 'not_run', 'protocol_stopped')
IDENTITIES = ('cohort_id', 'case_id', 'context_group_id', 'role',
              'input_digest', 'gold_digest', 'comparison_digest')


class StatisticsContractError(ValueError):
    pass


def require(test, reason):
    if not test:
        raise StatisticsContractError(reason)


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def quantile_type7(values, probability):
    require(values and all(finite_number(x) for x in values), 'quantile_values')
    require(finite_number(probability) and 0 <= probability <= 1, 'quantile_probability')
    ordered = sorted(values)
    h = (len(ordered) - 1) * probability
    i = math.floor(h)
    return ordered[i] + (ordered[min(i + 1, len(ordered) - 1)] - ordered[i]) * (h - i)


def paired_bootstrap(vectors, group_order, resamples=10000, seed=20261030, draws=None):
    """Use the same n group indices for every condition in each resample.

    Explicit draws support exact software enumeration. Production calls use
    the frozen seed/resample count and record a digest of the full draw stream.
    """
    n = len(group_order)
    require(n > 0 and n == len(set(group_order)), 'bootstrap_groups')
    require(vectors and all(len(v) == n and all(finite_number(x) for x in v) for v in vectors.values()), 'bootstrap_vectors')
    require(type(resamples) is int and 1 <= resamples <= 100000, 'bootstrap_resamples')
    require(type(seed) is int, 'bootstrap_seed')
    rng = random.Random(seed)
    stream = ([rng.randrange(n) for _ in range(n)] for _ in range(resamples)) if draws is None else iter(draws)
    samples = {name: [] for name in sorted(vectors)}
    hasher = hashlib.sha256()
    count = 0
    for indices in stream:
        require(len(indices) == n and all(type(i) is int and 0 <= i < n for i in indices), 'bootstrap_indices')
        count += 1
        require(count <= resamples, 'bootstrap_draw_count')
        hasher.update((json.dumps(indices, separators=(',', ':')) + '\n').encode())
        for name in samples:
            samples[name].append(sum(vectors[name][i] for i in indices) / n)
    require(count == resamples, 'bootstrap_draw_count')
    return dict(resamples=count, seed=seed if draws is None else None,
                draw_mode='seeded' if draws is None else 'explicit', draw_sha256=hasher.hexdigest(),
                group_order=list(group_order), quantile='type7', interval='95% pointwise percentile',
                paired_shared_indices=True, simultaneous_interval=False, risk_certificate=False,
                methods={name: dict(delta=sum(vectors[name]) / n,
                                    ci95=[quantile_type7(values, .025), quantile_type7(values, .975)])
                         for name, values in samples.items()})


def validate(plan, records):
    require(plan.get('schema') == PLAN_SCHEMA, 'plan_schema')
    names = plan.get('conditions')
    require(isinstance(names, list) and len(names) >= 2 and all(isinstance(x, str) and x for x in names)
            and len(names) == len(set(names)) and names.count('full') == 1, 'condition_plan')
    cases = plan.get('cases')
    require(isinstance(cases, list) and 0 < len(cases) <= 4096, 'case_plan')
    require(isinstance(plan.get('cohort_id'), str) and plan['cohort_id'] and isinstance(plan.get('role'), str) and plan['role'], 'plan_identity')
    excluded = plan.get('excluded_group_ids', [])
    require(isinstance(excluded, list) and all(isinstance(x, str) for x in excluded), 'excluded_groups')
    by_case = {}
    groups = set()
    for case in cases:
        require(isinstance(case, dict), 'case_contract')
        require(all(isinstance(case.get(k), str) and case[k] for k in IDENTITIES), 'case_identity')
        require(case['cohort_id'] == plan['cohort_id'] and case['role'] == plan['role'], 'case_cohort_or_role')
        require(case['case_id'] not in by_case, 'duplicate_case')
        require(case['context_group_id'] not in groups and case['context_group_id'] not in excluded, 'duplicate_or_cross_role_group')
        require(all(digest(case[k]) for k in ('input_digest', 'gold_digest', 'comparison_digest')), 'identity_digest')
        by_case[case['case_id']] = case
        groups.add(case['context_group_id'])
    by = {}
    for row in records:
        require(isinstance(row, dict) and row.get('schema') == ROW_SCHEMA, 'row_schema')
        case = by_case.get(row.get('case_id'))
        require(case is not None and row.get('condition_id') in names, 'foreign_cell')
        require(all(row.get(k) == case[k] for k in IDENTITIES), 'pair_identity_mismatch')
        key = (row['case_id'], row['condition_id'])
        require(key not in by, 'duplicate_cell')
        state = row.get('execution_state')
        require(state in STATES, 'execution_state')
        require(row.get('budget_state') in ('ok', 'infeasible_budget'), 'budget_state')
        require(row['condition_id'] != 'full' or row['budget_state'] == 'ok', 'full_budget')
        if state == 'ok':
            require(row['budget_state'] == 'ok', 'executed_infeasible_budget')
            require(type(row.get('truncated')) is bool and type(row.get('format')) is bool, 'boolean_flags')
            for metric in ('task_EM', 'task_F1'):
                require(metric in row, 'missing_metric')
                value = row.get(metric)
                require(value is None or finite_number(value) and 0 <= value <= 1, 'metric_number')
                if value is None:
                    require(isinstance(row.get(metric + '_reason'), str) and row[metric + '_reason'], 'metric_null_reason')
            require(row.get('task_EM') in (None, 0, 1), 'EM_binary')
        else:
            require(isinstance(row.get('reason'), str) and row['reason'], 'state_reason')
            require(all(k in row and row[k] is None for k in ('task_EM', 'task_F1', 'format', 'truncated')), 'unexecuted_metrics')
            if state == 'infeasible_budget':
                require(row['budget_state'] == 'infeasible_budget', 'budget_block_identity')
        by[key] = row
    require(len(by) == len(cases) * len(names), 'missing_planned_cell')
    return sorted(cases, key=lambda c: c['context_group_id']), ['full'] + sorted(set(names) - {'full'}), by


def strict_task(row):
    return row['task_EM'] if row['execution_state'] == 'ok' and not row['truncated'] else None


def joint(row):
    if row['execution_state'] in ('not_run', 'protocol_stopped'):
        return None
    return int(row['execution_state'] == 'ok' and not row['truncated']
               and row['format'] and row['task_EM'] == 1)


def summarize(plan, records, phase, full_support, resamples=10000, seed=20261030):
    require(phase in ('pending', 'complete', 'protocol_stopped'), 'phase')
    require(full_support is None or type(full_support) is bool, 'full_support_flag')
    cases, names, by = validate(plan, records)
    n = len(cases)
    output = dict(schema='kv_group_statistics_v1', cohort_id=plan['cohort_id'], role=plan['role'],
                  groups=n, planned_cells=n * len(names), phase=phase, full_support=full_support,
                  conditions={}, comparisons=None, bootstrap=None,
                  primary_estimand='joint(method)-joint(full), denominator all planned groups',
                  scientific_sample_claim=False)
    for name in names:
        rows = [by[c['case_id'], name] for c in cases]
        raw = [r['task_EM'] for r in rows if r['execution_state'] == 'ok' and r['task_EM'] is not None]
        strict = [strict_task(r) for r in rows if strict_task(r) is not None]
        output['conditions'][name] = dict(scheduled=n, execution_counts=dict(Counter(r['execution_state'] for r in rows)),
            budget_infeasible=sum(r['budget_state'] == 'infeasible_budget' for r in rows),
            truncated=sum(r['execution_state'] == 'ok' and r['truncated'] for r in rows),
            raw_task_count=len(raw), raw_task_sum=sum(raw), strict_task_count=len(strict), strict_task_sum=sum(strict),
            task_NA=sum(r['execution_state'] == 'ok' and r['task_EM'] is None for r in rows),
            observed_joint_successes=sum(joint(r) == 1 for r in rows), joint_rate=None)
    pending = any(r['execution_state'] in ('not_run', 'protocol_stopped') for r in by.values())
    if phase != 'complete' or full_support is not True or pending:
        output.update(status='descriptive_only', no_primary_estimate_reason='phase_or_support_incomplete' if phase != 'complete' or full_support is not True else 'pending_cells')
        return output
    vectors = {}
    comparisons = {}
    for name in names:
        output['conditions'][name]['joint_rate'] = sum(joint(by[c['case_id'], name]) for c in cases) / n
        if name == 'full':
            continue
        vectors[name] = [joint(by[c['case_id'], name]) - joint(by[c['case_id'], 'full']) for c in cases]
        transitions = Counter()
        full_correct = eligible = damaged = 0
        for case in cases:
            a = strict_task(by[case['case_id'], 'full'])
            b = strict_task(by[case['case_id'], name])
            full_correct += a == 1
            if a is None or b is None:
                continue
            transitions[('C' if a else 'W') + '2' + ('C' if b else 'W')] += 1
            eligible += a == 1
            damaged += a == 1 and b == 0
        paired = sum(transitions.values())
        comparisons[name] = dict(groups=n, joint_delta=sum(vectors[name]) / n,
            strict_task_pairs=paired, unavailable_task_pairs=n - paired,
            transitions={k: transitions[k] for k in ('C2C', 'C2W', 'W2C', 'W2W')},
            available_Full_correct=full_correct, eligible_Full_correct_pairs=eligible,
            unassessed_Full_correct=full_correct - eligible,
            strict_conditional_damage=damaged / eligible if eligible else None,
            all_Full_correct_damage_bounds=[damaged / full_correct, (damaged + full_correct - eligible) / full_correct] if full_correct else None,
            coverage_bounds_are_not_CI=True)
    boot = paired_bootstrap(vectors, [c['context_group_id'] for c in cases], resamples, seed)
    for name in comparisons:
        comparisons[name]['joint_delta_ci95'] = boot['methods'][name]['ci95']
    output.update(status='complete', comparisons=comparisons, bootstrap=boot)
    return output


def pending_native_plan(cells):
    """Adapt ONLY a native preflight's still-unexecuted plan; never score it."""
    require(cells and all(c.get('execution_state') == 'not_run' and c.get('model_called') is False
                         and all(v is None for v in c['metrics'].values()) for c in cells), 'native_plan_not_pending')
    cases = {}
    outcomes = []
    for cell in cells:
        identity = dict(cohort_id=cell['cohort_id'], case_id=cell['case_id'], context_group_id=cell['context_group_id'],
                        role=cell['role'], input_digest=cell['input_ids_sha256'], gold_digest=cell['gold_sha256'],
                        comparison_digest=canonical_sha(dict(cohort=cell['cohort_id'], prompt=cell['prompt_sha256'], input=cell['input_ids_sha256'])))
        require(cell['case_id'] not in cases or cases[cell['case_id']] == identity, 'native_pair_identity')
        cases[cell['case_id']] = identity
        outcomes.append(dict(identity, schema=ROW_SCHEMA, condition_id=cell['condition_id'],
            execution_state='not_run', budget_state=cell['budget_state'], reason='pending_GPU_protocol',
            task_EM=None, task_F1=None, format=None, truncated=None))
    plan = dict(schema=PLAN_SCHEMA, cohort_id=cells[0]['cohort_id'], role=cells[0]['role'],
                conditions=sorted({c['condition_id'] for c in cells}), cases=list(cases.values()))
    validate(plan, outcomes)
    return plan, outcomes
