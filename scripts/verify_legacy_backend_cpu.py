"""Recompute finite acceptance from raw masks and original public labels."""
import hashlib
import json
from pathlib import Path
import sys


def need(ok, message):
    if not ok:
        raise AssertionError(message)


def verify(out):
    for name, digest in json.loads((out / 'worker_manifest.json').read_text()).items():
        path = (out / name).resolve()
        need(path.is_relative_to(out), 'manifest_path')
        need(hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'hash:' + name)
    selection = json.loads((out / 'input_public_schema_selection.json').read_text())
    report = dict(status='complete', backends={}, total_official_instances=90,
                  qualification='finite byte-vocab semantic check; no service isolation or exhaustive language equivalence')
    all_masks = 0
    for backend in ('xgrammar', 'llguidance'):
        path = out / (backend + '-result.json')
        eventpath = out / (backend + '-events.jsonl')
        rows = [json.loads(line) for line in eventpath.read_text().splitlines()] if eventpath.exists() else []
        calls = {}
        open_calls = {}
        beats = {}
        for i, event in enumerate(rows):
            need(event['seq'] == i+1 and event['backend'] == backend, 'event_identity')
            if i:
                need(event['ns'] >= rows[i-1]['ns'], 'event_clock')
            if event['event'] == 'call_begin':
                open_calls[event['call_id']] = event
            elif event['event'] == 'call_end':
                begin = open_calls.pop(event['call_id'])
                need(begin['kind'] == event['kind'], 'call_kind')
                calls[event['call_id']] = (begin, event)
            elif event['event'] == 'heartbeat':
                beats.setdefault(event['call_id'], []).append(event)
        control = {}
        native_span_with_beats = 0
        native_span_without_beats = 0
        for cid, (begin, end) in calls.items():
            count = sum(begin['ns'] <= beat['ns'] <= end['ns'] and beat['tid'] != begin['tid']
                        for beat in beats.get(cid, []))
            if begin['kind'].startswith('control_'):
                control[begin['kind']] = dict(heartbeats_in_call_span=count, duration_ns=end['ns']-begin['ns'])
            elif begin['kind'] != 'import':
                if count:
                    native_span_with_beats += 1
                else:
                    native_span_without_beats += 1
        controls_passed = (control.get('control_python_holds_GIL', {}).get('heartbeats_in_call_span') == 0
                           and control.get('control_sleep_releases_GIL', {}).get('heartbeats_in_call_span', 0) > 0)
        summary = dict(worker_status='missing_result', counts=dict(label_match=0, valid_rejected=0,
                       invalid_accepted=0, error_or_unavailable=0), GIL_controls=control,
                       GIL_controls_passed=controls_passed, unfinished_calls=len(open_calls),
                       native_call_spans_with_heartbeats=native_span_with_beats,
                       native_call_spans_without_heartbeats=native_span_without_beats,
                       GIL_qualification='coarse Python wrapper call span, not exact native-entry tracing; no heartbeat is inconclusive')
        report['backends'][backend] = summary
        if not path.exists():
            summary['counts']['error_or_unavailable'] = 45
            continue
        result = json.loads(path.read_text())
        summary['worker_status'] = result['status']
        summary['guard'] = result['guard']
        summary['counters'] = result['counters']
        need(all(row['pid'] == result['pid'] for row in rows), 'worker_pid')
        maskpath = out / (backend + '-masks.jsonl')
        masks = [json.loads(line) for line in maskpath.read_text().splitlines()] if maskpath.exists() else []
        all_masks += len(masks)
        need(len(masks) <= 1215, 'mask_limit')
        groups = {g['case_id']:g for g in result['cases']}
        seen = set()
        for source in selection['cases']:
            group = groups.get(source['case_id'])
            tests = {t['index']:t for t in group.get('tests', [])} if group else {}
            for index, labeled in enumerate(source['tests']):
                test = tests.get(index)
                if not test or test['status'] != 'complete':
                    summary['counts']['error_or_unavailable'] += 1
                    continue
                text = json.dumps(labeled['data'], ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)
                need(test['serialized'] == text and test['expected'] == labeled['valid'], 'source_label_or_text')
                tokens = list(text.encode()) + [256]
                trajectory = [m for m in masks if m['case_id'] == source['case_id'] and m['test_index'] == index]
                need(len(trajectory) == test['steps'] and trajectory, 'trajectory_size')
                accepted = True
                for position, mask in enumerate(trajectory):
                    key = (source['case_id'], index, position)
                    need(key not in seen, 'duplicate_step')
                    seen.add(key)
                    need(mask['position'] == position and mask['token'] == tokens[position], 'token_position')
                    raw = bytes.fromhex(mask['raw_mask_hex'])
                    token = tokens[position]
                    allowed = bool(raw[token//8] & (1 << (token%8)))
                    need(allowed == mask['allowed'], 'bit_recompute')
                    if not allowed:
                        need(position == len(trajectory)-1 and mask['commit_result'] is None, 'commit_rejected_token')
                        accepted = False
                    else:
                        need(mask['commit_result'] is True, 'commit_bit_mismatch')
                if accepted:
                    need(len(trajectory) == len(tokens) and trajectory[-1]['token'] == 256, 'explicit_eos_missing')
                need(accepted == test['accepted'], 'accepted_recompute')
                match = accepted == labeled['valid']
                need(match == test['matches_label'], 'label_match_recompute')
                category = 'label_match' if match else 'valid_rejected' if labeled['valid'] else 'invalid_accepted'
                summary['counts'][category] += 1
        need(sum(summary['counts'].values()) == 45, 'all45_denominator')
        need(result['counters']['schema_specs'] <= 8 and result['counters']['matcher_constructions'] <= 45, 'construction_bound')
        need(result['counters']['mask_calls'] >= len(masks), 'mask_count')
        summary['finite_semantic_gate'] = (summary['counts']['label_match'] == 45 and controls_passed
                                            and result['status'] == 'complete' and not open_calls)
    need(all_masks <= 2430, 'total_mask_cap')
    report['archived_masks'] = all_masks
    report['finite_semantic_gate'] = all(r.get('finite_semantic_gate',False) for r in report['backends'].values())
    with (out / 'independent_verification.json').open('x') as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(report))


if __name__ == '__main__':
    verify(Path(sys.argv[1]).resolve())
