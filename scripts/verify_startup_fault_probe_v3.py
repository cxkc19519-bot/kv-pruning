"""Independent artifact/clock/signal verifier; imports no backend or probe."""
import hashlib
import json
from pathlib import Path
import re
import sys


def need(value, reason):
    if not value:
        raise AssertionError(reason)


def verify(out, destination):
    final = json.loads((out / 'manifest.json').read_text())
    for name, digest in final.items():
        path = (out / name).resolve()
        need(path.is_relative_to(out) and hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'sealed_manifest')
    mapping = json.loads((out / 'pre_verification_manifest.json').read_text())
    for name, digest in mapping.items():
        p = (out / name).resolve()
        need(p.is_relative_to(out), 'manifest_path')
        need(hashlib.sha256(p.read_bytes()).hexdigest() == digest, 'manifest_hash:' + name)
    cfg = json.loads((out / 'registration_snapshot.json').read_text())
    need(cfg['cases'] == ['periodic', 'fatal_only'], 'frozen_pair')
    smoke_dir = out / 'launcher_smoke'
    smoke = json.loads((smoke_dir / 'worker-status.json').read_text())
    smoke_process = json.loads((smoke_dir / 'process-record.json').read_text())
    need(smoke['status'] == 'complete' and smoke['target_imports'] == 0, 'stdlib_smoke')
    need(smoke_process['debugger_exit_code'] == 0 and not smoke_process['timed_out'], 'smoke_gdb')
    need('PROBE_DEBUGGER_END' in (smoke_dir / 'gdb.log').read_text(), 'smoke_batch_end')
    need(smoke_process['debugger_end_ns'] - smoke_process['spawn_ns'] < 5_000_000_000, 'smoke5')
    results = []
    prior_end = smoke_process['debugger_end_ns']
    for case in cfg['cases']:
        directory = out / case
        process = json.loads((directory / 'process-record.json').read_text())
        rows = [json.loads(line) for line in (directory / 'events.jsonl').read_text().splitlines()]
        need(rows and rows[0]['event'] == 'worker_bootstrap', 'bootstrap_record')
        owner = [rows[0]['pid'], rows[0]['starttime']]
        need(owner in process['owned_processes'], 'worker_external_identity')
        for i, row in enumerate(rows):
            need(row['seq'] == i + 1 and row['tid'] == owner[0], 'event_owner_tid_sequence')
            if row['event'] in ('lookup_started', 'lookup_finished'):
                query = json.loads((directory / f"lookup-{row['number']}.json").read_text())
                need([row['pid'], row['starttime']] == [query['pid'], query['starttime']], 'query_subject_identity')
                need(row['argv'] == ['/sbin/ldconfig', '-p'], 'query_subject_argv')
            else:
                need([row['pid'], row['starttime']] == owner, 'worker_subject_identity')
            if i:
                need(row['ns'] >= rows[i - 1]['ns'], 'event_clock')
        need(rows[0]['parent_spawn_ns'] == process['spawn_ns'] and rows[0]['fatal_enabled'], 'origin_fatal')
        need(rows[0]['core_limit'] == [0, 0] and len(rows[0]['affinity']) <= 2, 'resource_scope')
        modes = [r for r in rows if r['event'] == 'diagnostic_mode']
        need(len(modes) == 1 and modes[0]['periodic'] == (case == 'periodic'), 'timer_assignment')
        need(not any(r['event'] == 'boundary_denied' for r in rows), 'observed_boundary_denial')
        need(not any('xgrammar' in r['event'] or 'factory' in r['event'] or 'schema' in r['event'] for r in rows), 'torch_only')
        log = (directory / 'gdb.log').read_text()
        need('PROBE_DEBUGGER_END' in log or process['timed_out'], 'debugger_finished_or_timeout')
        need((directory / 'gdb.log').stat().st_size <= 524288, 'debugger_output_cap')
        need((directory / 'stacks.txt').stat().st_size <= 524288, 'stack_cap')
        if prior_end is not None:
            need(process['spawn_ns'] >= prior_end, 'pair_sequential')
        prior_end = process['debugger_end_ns']
        samples = [json.loads(line) for line in (directory / 'process-samples.jsonl').read_text().splitlines()]
        need(samples and samples[0]['ns'] >= process['spawn_ns'], 'external_clock')
        if not process['timed_out']:
            need(process['debugger_end_ns'] - process['spawn_ns'] < 30_000_000_000, 'case30')
        else:
            need(process['debugger_end_ns'] - process['spawn_ns'] >= 30_000_000_000, 'timeout_not_early')
        signal_match = re.search(r'(?:Thread[^\n]*|Program) received signal (SIG[A-Z]+)', log)
        selected = log.split('PROBE_SELECTED_BACKTRACE', 1)[-1].split('PROBE_ALL_THREADS', 1)[0]
        fault_in_dump = bool(signal_match and signal_match.group(1) == 'SIGSEGV'
                             and re.search(r'#0\s+.*(?:dump_frame|_Py_DumpASCII|dump_traceback|PyCode_Addr2Line)', selected)
                             and 'faulthandler_thread' in selected)
        status_path = directory / 'worker-status.json'
        status = json.loads(status_path.read_text()) if status_path.exists() else None
        complete = status is not None and status['status'] == 'complete'
        if complete:
            need(not signal_match and not process['timed_out'], 'complete_with_fault')
            names = [r['event'] for r in rows]
            for event in ['torch_import_begin', 'torch_import_end', 'thread_settings_begin', 'thread_settings_end', 'worker_complete']:
                need(names.count(event) == 1, 'complete_checkpoint:' + event)
            need(status['cuda_initialized'] is False and status['torch_import_complete'], 'cuda_postcheck')
            need(not any(status['boundary_counts'][k] for k in ('file_denied', 'process_denied', 'forbidden_imports')), 'final_boundary')
        queries = []
        for p in sorted(directory.glob('lookup-*.json')):
            q = json.loads(p.read_text())
            need(q['argv'] == ['/sbin/ldconfig', '-p'] and q['exit_code'] == 0, 'query_contract')
            for stream, cap in [('stdout', 262144), ('stderr', 65536)]:
                raw = (directory / f"lookup-{q['number']}-{stream}.binlog").read_bytes()
                need(len(raw) == q[stream + '_bytes'] and len(raw) <= cap, 'query_bytes')
                need(hashlib.sha256(raw).hexdigest() == q[stream + '_sha256'], 'query_hash')
            queries.append(q)
        need(len(queries) <= 4, 'query_count')
        results.append(dict(case=case, worker_owner=owner, torch_import_complete=complete,
                            debugger_exit_code=process['debugger_exit_code'], timed_out=process['timed_out'],
                            signal=signal_match.group(1) if signal_match else None,
                            fault_in_periodic_dump=fault_in_dump,
                            last_event=rows[-1]['event'], queries=queries,
                            boundary_counts=status['boundary_counts'] if status else None))
    report = dict(status='complete', launcher_smoke_passed=True, cases=results, old_cold5_gate=False, full_startup_gate=False,
                  finite_semantic_gate=False, request_admission=False, semantic_instances=0,
                  causal_claim='Single pair under GDB; no general failure rate or retrospective proof.')
    report['original_validator_failed_preserved'] = True
    report['source_manifest_sha256'] = hashlib.sha256((out / 'manifest.json').read_bytes()).hexdigest()
    (destination / 'independent_verification.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    registration = root / sys.argv[1]
    need(hashlib.sha256(registration.read_bytes()).hexdigest() == sys.argv[2], 'registration_sha256')
    cfg = json.loads(registration.read_text())
    for name, digest in {**cfg['source_sha256'], **cfg['input_sha256']}.items():
        need(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name)
    destination = root / cfg['output']
    destination.mkdir(exist_ok=False)
    (destination / 'registration_snapshot.json').write_bytes(registration.read_bytes())
    (destination / 'source_verifier.py').write_bytes(Path(__file__).read_bytes())
    verify((root / cfg['input_run']).resolve(), destination)
    mapping = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.iterdir()}
    (destination / 'manifest.json').write_text(json.dumps(mapping, sort_keys=True, indent=2) + '\n')
    print('ANALYSIS_MANIFEST_SHA256', hashlib.sha256((destination / 'manifest.json').read_bytes()).hexdigest())
