"""Twelve software boundary fixtures; never model or scientific observations."""
from copy import deepcopy

from reliability_report import (ReportError, feasible_protection, normalize, report)

SPECS = [dict(condition_id='full'), dict(condition_id='plain', budget_group='compressed'),
         dict(condition_id='pinned', budget_group='compressed')]


def row(case='a', condition='full', correct=True, constraint=True, **changes):
    raw = dict(source_key=case, status='ok', truncated=False, gold='label',
        input_ids_sha256='a'*64, prefix_kv_bytes=100 if condition == 'full' else 50,
        metrics=dict(exact_correct=correct, whole_response_label_format=constraint))
    raw.update(changes)
    return normalize(raw, 'fixture', condition, dict(kind='synthetic_software_fixture'))


def result(rows, cases=('a',), profile='strict_complete_pair_preview'):
    return report('fixture', list(cases), SPECS, rows, profile)


def task(r, method='plain'):
    return r['methods'][method]['metrics']['task']


def rejects(action, text):
    try:
        action()
    except ReportError as exc:
        assert text in str(exc), (text, str(exc))
        return str(exc)
    raise AssertionError('Expected validation failure: '+text)


def check_fixture(index):
    base = row(); plain = row(condition='plain'); pinned = row(condition='pinned')
    if index == 0:
        r = result([row(correct=False), row(condition='plain', correct=False)])
        assert task(r)['conditional_loss'] == dict(numerator=0, denominator=0,
            value=None, reason='zero_eligible_full_pass_pairs')
        return task(r)['conditional_loss']
    if index == 1:
        failed = row(condition='plain', status='error', error_message='synthetic error')
        r = result([base, failed]); t = task(r)
        assert t['available_full_pass_count'] == t['unassessed_full_pass_count'] == 1
        assert t['conditional_loss']['value'] is None and t['unavailable_pair_count'] == 1
        old = task(result([base,failed], profile='legacy_exact_replay'))
        assert old['conditional_loss']['denominator'] == 1 and old['conditional_loss']['value'] == 0
        assert old['eligible_full_pass_pair_count'] == 0 and old['unassessed_full_pass_count'] == 1
        return dict(unassessed=t['unassessed_full_pass_count'], strict_loss=t['conditional_loss'],
            historical_loss=old['conditional_loss'], historical_zero_not_a_safety_claim=True)
    if index == 2:
        trunc = row(condition='plain', truncated=True)
        legacy = task(result([base, trunc], profile='legacy_exact_replay'))
        strict = task(result([base, trunc]))
        assert legacy['paired_count'] == 1 and strict['paired_count'] == 0
        assert trunc['metrics']['task']['value'] is True and trunc['truncated'] is True
        return dict(legacy_pairs=1, strict_pairs=0, archived_score_preserved=True)
    if index == 3:
        r = result([base]); e = r['methods']['plain']['execution']
        assert e['not_run'] == 1 and task(r)['unavailable_pair_reasons'] == {'method:not_run':1}
        assert next(x for x in r['cells'] if x['condition_id'] == 'plain')['reason'] == 'scheduled_cell_missing'
        return e
    if index == 4:
        return dict(rejected=rejects(lambda:result([base, plain, deepcopy(plain)]), 'Duplicate'))
    if index == 5:
        # Both identity axes are validated within this one frozen fixture.
        errors = []
        for key, value in [('input_sha256','b'*64),('gold','other')]:
            bad = deepcopy(plain); bad[key] = value
            errors.append(rejects(lambda:result([base,bad]), 'identity mismatch'))
        return dict(rejected=errors)
    if index == 6:
        r = result([base, row(condition='plain', correct=False),
                    row(case='b', correct=False), row(case='b', condition='plain')], cases=('a','b'))
        t = task(r)
        assert t['pass_count'] == r['methods']['full']['metrics']['task']['pass_count'] == 1
        assert t['transitions'] == dict(C2C=0,C2W=1,W2C=1,W2W=0)
        return t['transitions']
    if index == 7:
        pinned['costs']['prefix_kv_bytes']['value'] = 51
        return dict(rejected=rejects(lambda:result([base,plain,pinned]), 'budget mismatch'))
    if index == 8:
        r = result([base,plain]); c = r['cells'][0]['costs']
        for key in ['peak_gpu_bytes','latency_ms','extra_buffer_peak_bytes']:
            assert c[key] == dict(value=None,reason='not_measured')
        return {k:c[k] for k in ['peak_gpu_bytes','latency_ms','extra_buffer_peak_bytes']}
    if index == 9:
        f = feasible_protection(11,10)
        assert f['state'] == 'infeasible_budget' and f['effective_budget'] == 10
        bad = row(condition='plain', status=f['state'], reason='protected_union_exceeds_budget')
        r = result([base,bad]); assert r['methods']['plain']['execution']['infeasible_budget'] == 1
        assert task(r)['unassessed_full_pass_count'] == 1
        return f
    if index == 10:
        missing = row(condition='plain', constraint=None)
        r = result([base,missing]); m = r['methods']['plain']['metrics']
        assert m['task']['paired_count'] == 1 and m['constraint']['paired_count'] == 0
        assert m['constraint']['unavailable_pair_reasons'] == {'method:annotation_not_recorded':1}
        return dict(task_pairs=1,constraint_pairs=0,reason='annotation_not_recorded')
    if index == 11:
        other = deepcopy(base); other['cohort_id'] = 'other'
        a = result([base]); b = report('other',['a'],SPECS,[other],'strict_complete_pair_preview')
        assert a['cohort_id'] != b['cohort_id'] and a['case_count'] == b['case_count'] == 1
        assert a['independent_confirmation'] is b['independent_confirmation'] is False
        return dict(cohorts=['fixture','other'], same_case_id_allowed=True, independent_confirmation=False)
    raise AssertionError('Fixture outside frozen bound')


def validate_fixture(index, description):
    # The caller archives each success immediately; first failure propagates.
    return dict(index=index, description=description, status='pass', evidence=check_fixture(index))
