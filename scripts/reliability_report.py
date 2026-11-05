"""Pure stdlib pairing of archived outcomes. No inference or text scoring.

Profiles deliberately differ: legacy includes status-ok truncated results;
strict requires a complete result on both sides. Neither infers missing data.
"""
from collections import Counter

PROFILES = ('legacy_exact_replay', 'strict_complete_pair_preview')
STATES = ('ok', 'error', 'not_run', 'infeasible_budget')
TRANSITIONS = ('C2C', 'C2W', 'W2C', 'W2W')
METRICS = {'task': 'exact_correct', 'constraint': 'whole_response_label_format'}


class ReportError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReportError(message)


def metric(value=None, reason='annotation_not_recorded'):
    require(value is None or type(value) is bool, 'Metric must be bool or None')
    require(value is not None or isinstance(reason, str) and reason, 'N/A requires a reason')
    return dict(value=value, applicable=value is not None,
                reason=None if value is not None else reason)


def normalize(raw, cohort_id, condition_id, origin):
    """Adapt an archived TREC row without interpreting its output or token IDs."""
    case_id = raw.get('source_key')
    require(isinstance(case_id, str) and case_id, 'Missing case ID')
    state = raw.get('status')
    require(state in STATES, 'Unknown execution state')
    truncated = raw.get('truncated')
    if state == 'ok':
        require(type(truncated) is bool, 'Successful row requires truncation flag')
        require(isinstance(raw.get('gold'), str) and raw['gold'], 'Missing gold identity')
        h = raw.get('input_ids_sha256')
        require(isinstance(h, str) and len(h) == 64 and
                all(x in '0123456789abcdef' for x in h), 'Invalid input hash')
        require(type(raw.get('prefix_kv_bytes')) is int and
                raw['prefix_kv_bytes'] >= 0, 'Missing prefix-byte observation')
    metrics = {}
    for name, old in METRICS.items():
        reason = raw.get('metric_reasons', {}).get(name, 'annotation_not_recorded')
        metrics[name] = metric(raw.get('metrics', {}).get(old), reason) if state == 'ok' else metric(reason='no_output')
        metrics[name].update(metric_id=old, metric_version='trec_legacy_report_adapter_v1')
    reason = None if state == 'ok' else raw.get('reason', raw.get('error_message', state))
    compatibility = raw.get('metrics', {}).get('official_firstline_compatibility') if state == 'ok' else None
    require(compatibility is None or type(compatibility) in (int,float) and
            0 <= compatibility <= 1, 'Invalid archived compatibility score')
    return dict(cohort_id=cohort_id, case_id=case_id, condition_id=condition_id,
        execution_state=state, reason=reason, truncated=truncated,
        input_sha256=raw.get('input_ids_sha256'), gold=raw.get('gold'),
        context_group=dict(value=None, reason='independence_not_established'),
        metrics=metrics, origin=origin,
        compatibility_result=dict(value=compatibility,
            reason=None if compatibility is not None else ('no_output' if state != 'ok' else 'not_recorded'),
            metric_id='official_firstline_compatibility', metric_version='archived_no_rescoring'),
        costs=dict(prefix_kv_bytes=dict(value=raw.get('prefix_kv_bytes'),
                      reason=None if raw.get('prefix_kv_bytes') is not None else 'not_recorded'),
                   final_live_kv_bytes=dict(value=raw.get('final_live_kv_bytes'),
                      reason=None if raw.get('final_live_kv_bytes') is not None else 'not_recorded'),
                   peak_gpu_bytes=dict(value=None, reason='not_measured'),
                   latency_ms=dict(value=None, reason='not_measured'),
                   extra_buffer_peak_bytes=dict(value=None, reason='not_measured')))


def feasible_protection(required_union_count, budget):
    require(type(required_union_count) is int and type(budget) is int and
            required_union_count >= 0 and budget >= 0, 'Invalid protection budget')
    return dict(state='ok' if required_union_count <= budget else 'infeasible_budget',
        requested_budget=budget, effective_budget=budget,
        required_union_count=required_union_count)


def unavailable_reason(row, metric_name, profile):
    if row['execution_state'] != 'ok':
        return row['execution_state']
    if profile == 'strict_complete_pair_preview' and row['truncated']:
        return 'truncated'
    if not row['metrics'][metric_name]['applicable']:
        return row['metrics'][metric_name]['reason']
    return None


def report(cohort_id, case_ids, condition_specs, records, profile):
    require(profile in PROFILES, 'Unknown profile')
    require(case_ids and len(set(case_ids)) == len(case_ids), 'Invalid case plan')
    names = [x['condition_id'] for x in condition_specs]
    require(len(names) == len(set(names)) and names.count('full') == 1, 'Invalid condition plan')
    by = {}
    for row in records:
        key = (row['cohort_id'], row['case_id'], row['condition_id'])
        require(row['cohort_id'] == cohort_id and row['case_id'] in case_ids and
                row['condition_id'] in names, 'Record outside declared plan')
        require(key not in by, 'Duplicate record identity')
        by[key] = row
    cells = []
    for case in case_ids:
        for name in names:
            key = (cohort_id, case, name)
            if key not in by:
                by[key] = normalize(dict(source_key=case, status='not_run',
                    reason='scheduled_cell_missing'), cohort_id, name, None)
            cells.append(by[key])
    # Join checks apply even to unavailable rows when an identity was recorded.
    for case in case_ids:
        base = by[(cohort_id, case, 'full')]
        budgets = {}
        for spec in condition_specs:
            row = by[(cohort_id, case, spec['condition_id'])]
            if row is not base:
                for key in ('input_sha256', 'gold'):
                    if base[key] is not None and row[key] is not None:
                        require(base[key] == row[key], 'Full/method identity mismatch: '+key)
            group = spec.get('budget_group')
            if group and row['execution_state'] == 'ok':
                b = row['costs']['prefix_kv_bytes']['value']
                require(b is not None, 'Budget comparison lacks bytes')
                require(group not in budgets or budgets[group] == b,
                        'Compressed prefix-byte budget mismatch')
                budgets[group] = b
    methods = {}
    for name in names:
        selected = [by[(cohort_id, c, name)] for c in case_ids]
        execution = {s:sum(r['execution_state'] == s for r in selected) for s in STATES}
        execution.update(scheduled=len(case_ids),
            truncated=sum(r['execution_state'] == 'ok' and bool(r['truncated']) for r in selected))
        metric_reports = {}
        for metric_name in METRICS:
            own_reasons = [unavailable_reason(r, metric_name, profile) for r in selected]
            valid = [r for r, reason in zip(selected, own_reasons) if reason is None]
            rec = dict(pass_count=sum(r['metrics'][metric_name]['value'] for r in valid),
                evaluated_count=len(valid), unavailable_count=len(case_ids)-len(valid),
                unavailable_reasons=dict(Counter(x for x in own_reasons if x is not None)))
            if name != 'full':
                counts = {s:0 for s in TRANSITIONS}
                unavailable = Counter(); full_pass = 0; paired_full_pass = 0
                pair_rows = []
                for case, row in zip(case_ids, selected):
                    base = by[(cohort_id, case, 'full')]
                    br = unavailable_reason(base, metric_name, profile)
                    rr = unavailable_reason(row, metric_name, profile)
                    if br is None and base['metrics'][metric_name]['value']:
                        full_pass += 1
                    if br is not None or rr is not None:
                        reason = ('full:'+br) if br is not None else ('method:'+rr)
                        unavailable[reason] += 1
                        pair_rows.append(dict(case_id=case, transition=None, reason=reason))
                        continue
                    a = base['metrics'][metric_name]['value']; b = row['metrics'][metric_name]['value']
                    key = ('C' if a else 'W')+'2'+('C' if b else 'W')
                    counts[key] += 1; paired_full_pass += int(a)
                    pair_rows.append(dict(case_id=case, transition=key, reason=None))
                loss_denominator = full_pass if profile == 'legacy_exact_replay' else paired_full_pass
                rec.update(transitions=counts, paired_count=sum(counts.values()),
                    unavailable_pair_count=sum(unavailable.values()),
                    unavailable_pair_reasons=dict(unavailable), pair_rows=pair_rows,
                    available_full_pass_count=full_pass,
                    eligible_full_pass_pair_count=paired_full_pass,
                    unassessed_full_pass_count=full_pass-paired_full_pass,
                    conditional_loss=dict(numerator=counts['C2W'], denominator=loss_denominator,
                        value=counts['C2W']/loss_denominator if loss_denominator else None,
                        reason=None if loss_denominator else 'zero_eligible_full_pass_pairs'))
            metric_reports[metric_name] = rec
        methods[name] = dict(execution=execution, metrics=metric_reports)
    return dict(cohort_id=cohort_id, profile=profile, case_count=len(case_ids),
        methods=methods, cells=cells,
        costs_scope='Archived scalar prefix/final KV only; peak/latency/extra buffer not measured',
        inference_performed=False, text_rescored=False, independent_confirmation=False)
