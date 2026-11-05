"""Independent event/ownership checker; does not import fixture implementation."""
import hashlib
import json
from pathlib import Path
import sys
import time


def require(value, reason):
    if not value:
        raise AssertionError(reason)


def verify(out):
    started = time.monotonic()
    for name, digest in json.loads((out / 'worker_manifest.json').read_text()).items():
        path = (out / name).resolve()
        require(path.is_relative_to(out), 'manifest_boundary')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'artifact_hash:' + name)
    cfg = json.loads((out / 'registration_snapshot.json').read_text())
    processes = json.loads((out / 'case_processes.json').read_text())
    require(len(processes) == 12, 'case_process_count')
    require([x['case_id'] for x in processes] == cfg['case_ids'], 'case_order')
    checks = []
    all_identities = set()
    for case, process in zip(cfg['case_ids'], processes):
        require(process['exit_code'] == 0 and not process['identity_still_present'], 'fixture_exit')
        require((out / (case + '.stderr')).read_text() == '', 'fixture_stderr')
        rows = [json.loads(line) for line in (out / (case + '.jsonl')).read_text().splitlines()]
        require(rows and rows[0]['event'] == 'fixture_started', 'first_event')
        require(rows[-1]['event'] == 'fixture_complete' and rows[-1]['status'] == 'complete', 'last_event')
        require(rows[-1]['elapsed_seconds'] < 3, 'case_wall_cap')
        require(len(rows[0]['affinity']) <= 2, 'affinity_cap')
        identities = {(process['pid'], process['starttime'])}
        identities.update((r['child_pid'], r['child_starttime']) for r in rows if r['event'] == 'child_owned')
        require(len(identities) <= 2, 'case_process_cap')
        sequences = {}
        for r in rows:
            require(r['run_id'] == cfg['run'] and r['case_id'] == case, 'event_scope')
            identity = (r['pid'], r['pid_starttime'])
            require(identity in identities, 'event_unowned_pid')
            require(r['native_thread_id'] > 0 and r['worker_slot_id'] == 'slot0', 'event_thread_or_slot')
            require(r['pool_id'] == case + '-pool0', 'pool_identity')
            seq, stamp = sequences.get(identity, (0, 0))
            require(r['sequence_number'] == seq + 1 and r['monotonic_ns'] >= stamp, 'sequence_clock')
            sequences[identity] = (r['sequence_number'], r['monotonic_ns'])
        all_identities.update(identities)

        def events(name, request=None):
            return [r for r in rows if r['event'] == name and (request is None or r['request_id'] == request)]

        def one(name, request=None):
            found = events(name, request)
            require(len(found) == 1, 'event_cardinality:' + case + ':' + name)
            return found[0]

        def before(a, b):
            require(a['monotonic_ns'] <= b['monotonic_ns'], 'causal_order:' + case)

        cleanup = one('cleanup_complete')
        require(all(not cleanup['counts'][k] for k in ('forbidden_imports', 'network_attempts', 'file_attempts', 'unexpected_subprocess')), 'guard')
        require(cleanup['counts']['allowed_task_spawns'] == len(identities) - 1, 'task_spawn_count')
        require(all(c['exit_code'] is not None and not c['identity_still_present'] for c in cleanup['children']), 'owned_child_cleanup')
        require(not events('fixture_error'), 'fixture_reported_error')
        before(cleanup, one('fixture_complete'))
        if case in ('queued_cancel', 'duplicate_cancel'):
            require(not events('work_started', 'B'), 'queued_work_ran')
            result = events('cancel_result', 'B')
            require(len(result) == (2 if case == 'duplicate_cancel' else 1) and all(r['result'] is True for r in result), 'queued_cancel_results')
            before(one('work_started', 'A'), events('cancel_requested', 'B')[0])
            before(one('caller_returned', 'B'), one('work_finished', 'A'))
        elif case in ('running_future_not_cancelled', 'caller_deadline_work_continues', 'normal_probe_reuses_same_slot'):
            before(one('work_started', 'A'), one('cancel_requested', 'A'))
            before(one('cancel_requested', 'A'), one('caller_returned', 'A'))
            before(one('caller_returned', 'A'), one('state_observed', 'A'))
            state = one('state_observed', 'A')
            require(state['running'] and not state['done'] and not state['cancelled'], 'running_witness')
            before(state, one('release_requested'))
            before(one('release_requested'), one('work_finished', 'A'))
            if case == 'caller_deadline_work_continues':
                require(one('caller_returned')['outcome'] == 'TimeoutError', 'deadline_outcome')
            else:
                require(one('cancel_result')['result'] is False, 'running_cancel_outcome')
            if case == 'normal_probe_reuses_same_slot':
                require(not one('state_observed', 'probe')['done'], 'probe_not_queued')
                begin, end = one('same_slot_probe_started'), one('same_slot_probe_finished')
                before(one('work_finished', 'A'), begin)
                before(begin, end)
                a = one('work_started', 'A')
                require(all(a[k] == begin[k] == end[k] for k in ('pid', 'pid_starttime', 'native_thread_id', 'pool_id', 'worker_slot_id')), 'probe_replaced_worker')
        elif case == 'cooperative_stop':
            before(one('cancel_requested'), one('work_finished'))
            before(one('work_finished'), one('caller_returned'))
            require(one('work_finished')['outcome'] == 'cancelled', 'cooperative_outcome')
        elif case in ('process_kill_reap', 'worker_exit_without_end_marker', 'cleanup_timeout_is_failure'):
            owned, reaped = one('child_owned'), one('process_reaped')
            require((owned['child_pid'], owned['child_starttime']) == (reaped['child_pid'], reaped['child_starttime']), 'reaped_identity')
            require(one('work_started')['pid'] == owned['child_pid'], 'process_work_pid')
            require(not events('work_finished'), 'unexpected_end_marker')
            before(one('work_started'), one('cancel_requested'))
            before(one('cancel_requested'), reaped)
            require(reaped['exit_code'] == (7 if case == 'worker_exit_without_end_marker' else -9), 'process_exit_code')
            if case == 'worker_exit_without_end_marker':
                require(one('caller_returned')['work_end_right_censored'] is True, 'unobserved_end_not_censored')
            elif case == 'cleanup_timeout_is_failure':
                failed = one('cleanup_status')
                require(failed['outcome'] == 'failed' and one('caller_returned')['outcome'] == 'cleanup_failed', 'cleanup_false_success')
                before(failed, reaped)
            else:
                before(reaped, one('caller_returned'))
        elif case == 'worker_exception':
            require(one('work_finished')['outcome'] == 'error', 'exception_end')
            require(one('caller_returned')['outcome'] == 'RuntimeError', 'exception_return')
            before(one('work_finished'), one('caller_returned'))
        elif case == 'completion_wins_cancel_race':
            before(one('work_finished'), one('cancel_requested'))
            require(one('cancel_result')['result'] is False and one('state_observed')['done'], 'completion_race')
            require(one('caller_returned')['outcome'] == 'already_completed', 'completed_not_cancelled')
        elif case == 'shared_work_has_other_waiter':
            require({r['request_id'] for r in events('waiter_attached')} == {'A', 'B'}, 'shared_initial_waiters')
            require(one('waiter_detached')['waiters'] == ['B'], 'shared_remaining_waiter')
            require(one('state_observed')['running'], 'shared_work_stopped')
            require(one('caller_returned', 'A')['outcome'] == 'waiter_cancelled', 'A_not_detached')
            require(one('caller_returned', 'B')['outcome'] == 'success', 'B_not_served')
            require(all(r['shared_work_id'] == 'shared-job' for r in rows if r['event'] in ('work_started', 'work_finished', 'caller_returned')), 'shared_identity')
            before(one('caller_returned', 'A'), one('work_finished'))
            before(one('work_finished'), one('caller_returned', 'B'))
        else:
            raise AssertionError('unhandled_case')
        cancellations = events('cancel_requested')
        metrics = dict(caller_cancel_latency_ns=None, work_stop_latency_ns=None,
                       probe_wait_ns=None, work_end_source=None,
                       exact_work_end_right_censored=False,
                       qualification='synthetic event ordering, not backend performance')
        if cancellations:
            cancel = cancellations[0]
            returned = next((r for r in events('caller_returned')
                             if r['request_id'] == cancel['request_id']), None)
            ends = [r for r in events('work_finished') if r['shared_work_id'] == cancel['shared_work_id']]
            if returned:
                metrics['caller_cancel_latency_ns'] = returned['monotonic_ns'] - cancel['monotonic_ns']
            if ends:
                metrics['work_stop_latency_ns'] = ends[0]['monotonic_ns'] - cancel['monotonic_ns']
                metrics['work_end_source'] = 'work_finished_event'
            elif events('process_reaped'):
                metrics['work_stop_latency_ns'] = one('process_reaped')['monotonic_ns'] - cancel['monotonic_ns']
                metrics['work_end_source'] = 'process_reaped_upper_bound_not_exact_work_end'
                metrics['exact_work_end_right_censored'] = True
            elif case in ('queued_cancel', 'duplicate_cancel'):
                metrics['work_end_source'] = 'never_started_cancelled_in_queue'
            if case == 'normal_probe_reuses_same_slot':
                metrics['probe_wait_ns'] = one('same_slot_probe_started')['monotonic_ns'] - one('submitted', 'probe')['monotonic_ns']
        checks.append(dict(case_id=case, independently_verified=True, events=len(rows), metrics=metrics,
                           identities=[list(x) for x in sorted(identities)]))

    sample_count = 0
    case_samples = {case: [] for case in cfg['case_ids']}
    for line in (out / 'process_samples.jsonl').read_text().splitlines():
        sample = json.loads(line)
        require(sample['case_id'] in cfg['case_ids'] and len(sample['processes']) <= 2, 'sample_scope')
        for p in sample['processes']:
            require((p['pid'], p['starttime']) in all_identities, 'sample_unowned_identity')
            require(p['cpu_ticks'] >= 0 and p['rss_pages'] >= 0, 'sample_value')
        sample_count += 1
        case_samples[sample['case_id']].append(sample)
    require(sample_count >= 12, 'missing_external_sampling')
    for check in checks:
        case = check['case_id']
        samples = case_samples[case]
        require(samples, 'case_missing_samples')
        check['sample_count'] = len(samples)
        stamps = [s['observer_ns'] for s in samples]
        require(stamps == sorted(stamps), 'sample_clock_order')
        check['observed_max_poll_gap_ns'] = max((b-a for a, b in zip(stamps, stamps[1:])), default=None)
        check['sampled_peak_sum_RSS_pages'] = max(sum(p['rss_pages'] for p in s['processes']) for s in samples)
        # A short fixture can end between two 10ms polls. Do not fabricate CPU zero.
        rows = [json.loads(line) for line in (out / (case + '.jsonl')).read_text().splitlines()]
        cancels = [r['monotonic_ns'] for r in rows if r['event'] == 'cancel_requested']
        ticks = {}
        if cancels:
            for sample in samples:
                if sample['observer_ns'] >= cancels[0]:
                    for p in sample['processes']:
                        ticks.setdefault((p['pid'], p['starttime']), []).append(p['cpu_ticks'])
        values = [v[-1]-v[0] for v in ticks.values() if len(v) >= 2]
        check['post_cancel_sampled_CPU_tick_delta'] = sum(values) if values else None
        check['CPU_tick_qualification'] = 'sampled_lower_coverage; null means insufficient post-cancel samples; synthetic jobs mostly wait'
    require(not any(n in sys.modules for n in ('torch', 'vllm', 'xgrammar', 'llguidance', 'numpy', 'transformers', 'tokenizers')), 'verifier_backend_import')
    result = dict(status='complete', cases=len(checks), checks=checks, external_samples=sample_count,
                  real_backend_calls=0, elapsed_seconds=time.monotonic() - started)
    with (out / 'independent_verification.json').open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status='complete', cases=len(checks), external_samples=sample_count)))


if __name__ == '__main__':
    verify(Path(sys.argv[1]).resolve())
