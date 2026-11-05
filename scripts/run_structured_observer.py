"""Registered Linux stdlib-only lifecycle fixtures; no real grammar backend."""
import argparse
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import threading
import time
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / 'configs/structured-observer-execution-v1.json'


def need(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def proc(pid):
    try:
        text = Path(f'/proc/{pid}/stat').read_text()
        fields = text[text.rindex(')') + 2:].split()
        return dict(pid=pid, starttime=int(fields[19]), state=fields[0],
                    ppid=int(fields[1]), cpu_ticks=int(fields[11]) + int(fields[12]),
                    rss_pages=int(fields[21]))
    except (FileNotFoundError, ProcessLookupError):
        return None


def same(pid, starttime):
    row = proc(pid)
    return row is not None and row['starttime'] == starttime


def registration(digest):
    need(str(ROOT) == '/home/user/jhk/project/Directional Exploration/kv-pruning', 'server_only')
    need(sha(REG) == digest, 'registration_sha256')
    cfg = json.loads(REG.read_text())
    need(cfg['execution_enabled'] and cfg['mode'] == 'stdlib_lifecycle_observer_engineering', 'scope')
    for rel, expected in {**cfg['source_sha256'], **cfg['input_sha256']}.items():
        need(sha(ROOT / rel) == expected, 'input_or_source_changed:' + rel)
    return cfg


def guard(out, allow_task):
    counts = dict(forbidden_imports=0, network_attempts=0,
                  file_attempts=0, unexpected_subprocess=0, allowed_task_spawns=0)

    def audit(event, args):
        if event == 'import' and args[0].split('.')[0] in (
                'torch', 'numpy', 'transformers', 'tokenizers', 'vllm',
                'xgrammar', 'llguidance', 'grid', 'tensorflow', 'jax'):
            counts['forbidden_imports'] += 1
            raise RuntimeError('backend_import_forbidden')
        if event.startswith('socket.'):
            counts['network_attempts'] += 1
            raise RuntimeError('network_forbidden')
        if event in ('os.system', 'os.fork', 'os.forkpty', 'os.posix_spawn'):
            counts['unexpected_subprocess'] += 1
            raise RuntimeError('unregistered_process_operation')
        if event == 'subprocess.Popen':
            argv = args[1]
            prefix = [sys.executable, '-I', '-S', '-B', str(Path(__file__).resolve()), '--task']
            if not allow_task or not isinstance(argv, list) or argv[:6] != prefix or argv[6] not in ('hold', 'abrupt'):
                counts['unexpected_subprocess'] += 1
                raise RuntimeError('unexpected_subprocess')
            counts['allowed_task_spawns'] += 1
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = Path(os.fsdecode(args[0])).resolve()
            mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if path.is_relative_to(ROOT / 'models') or path.suffix in ('.safetensors', '.bin', '.pt', '.pth') or writing and not path.is_relative_to(out):
                counts['file_attempts'] += 1
                raise RuntimeError('file_scope_forbidden')
    sys.addaudithook(audit)
    return counts


class Events:
    def __init__(self, cfg, case):
        self.run = cfg['run']
        self.case = case
        self.seq = 0
        self.lock = threading.Lock()
        self.starttime = proc(os.getpid())['starttime']

    def __call__(self, event, request='A', shared='job', **fields):
        with self.lock:
            self.seq += 1
            row = dict(event=event, run_id=self.run, case_id=self.case,
                       request_id=request, shared_work_id=shared,
                       worker_slot_id='slot0', pool_id=self.case + '-pool0',
                       pid=os.getpid(), pid_starttime=self.starttime,
                       native_thread_id=threading.get_native_id(),
                       sequence_number=self.seq, monotonic_ns=time.monotonic_ns())
            row.update(fields)
            payload = (json.dumps(row, sort_keys=True, allow_nan=False) + '\n').encode()
            need(len(payload) < 4096, 'atomic_event_size')
            need(os.write(1, payload) == len(payload), 'short_event_write')


def task(args, cfg):
    out = ROOT / cfg['run']
    counts = guard(out, False)
    event = Events(cfg, args.case)
    event('worker_ready')
    event('work_started')
    os.write(args.ready_fd, b'R')
    os.close(args.ready_fd)
    command = os.read(0, 1)
    if args.task == 'abrupt':
        os._exit(7)
    event('work_finished', outcome='released' if command else 'parent_pipe_closed')
    event('task_guard', counts=counts)
    return 0


def fixture(args, cfg):
    out = ROOT / cfg['run']
    counts = guard(out, True)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    event = Events(cfg, args.case)
    event('fixture_started', affinity=sorted(os.sched_getaffinity(0)))
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='owned-slot0')
    releases = []
    children = []
    started = time.monotonic()
    status = 'failed'

    def submit(request='A', shared='job', mode='normal', released=False):
        gate, ready = threading.Event(), threading.Event()
        if released:
            gate.set()
        releases.append(gate)
        event('submitted', request, shared)

        def work():
            event('worker_ready', request, shared)
            event('same_slot_probe_started' if request == 'probe' else 'work_started', request, shared)
            ready.set()
            result = 'success'
            try:
                need(gate.wait(1.5), 'fixture_gate_timeout')
                if mode == 'error':
                    result = 'error'
                    raise RuntimeError('expected_worker_exception')
                if mode == 'cooperative':
                    result = 'cancelled'
                return result
            finally:
                event('same_slot_probe_finished' if request == 'probe' else 'work_finished', request, shared, outcome=result)
        return pool.submit(work), gate, ready

    def wait_ready(ready):
        need(ready.wait(1), 'start_barrier')

    def state(future, request='A', shared='job'):
        event('state_observed', request, shared, running=future.running(), done=future.done(), cancelled=future.cancelled())

    def spawn(mode):
        rfd, wfd = os.pipe()
        event('submitted')
        argv = [sys.executable, '-I', '-S', '-B', str(Path(__file__).resolve()),
                '--task', mode, '--ready-fd', str(wfd), '--case', args.case,
                '--registration-sha256', args.registration_sha256]
        try:
            child = subprocess.Popen(argv, stdin=subprocess.PIPE, pass_fds=(wfd,), cwd=ROOT)
            identity = proc(child.pid)
            need(identity is not None, 'child_identity')
            children.append((child, identity['starttime']))
            event('child_owned', child_pid=child.pid, child_starttime=identity['starttime'])
        finally:
            os.close(wfd)
        try:
            need(bool(select.select([rfd], [], [], 1)[0]), 'child_ready_deadline')
            need(os.read(rfd, 1) == b'R', 'child_ready_barrier')
        finally:
            os.close(rfd)
        return child, identity['starttime']

    def reap(child, birth, kill=False):
        if kill:
            need(same(child.pid, birth), 'kill_identity')
            os.kill(child.pid, signal.SIGKILL)
        code = child.wait(timeout=1)
        event('process_reaped', child_pid=child.pid, child_starttime=birth, exit_code=code)
        if child.stdin:
            child.stdin.close()
        return code

    def alarm(*unused):
        raise TimeoutError('fixture_wall_deadline')

    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, 2.7)
    try:
        name = args.case
        if name in ('queued_cancel', 'duplicate_cancel'):
            first, release, ready = submit()
            wait_ready(ready)
            queued, _, _ = submit('B', 'queued-job')
            for _ in range(2 if name == 'duplicate_cancel' else 1):
                event('cancel_requested', 'B', 'queued-job', kind='future_cancel')
                result = queued.cancel()
                event('cancel_result', 'B', 'queued-job', result=result)
                need(result, 'queued_cancel_failed')
            event('caller_returned', 'B', 'queued-job', outcome='cancelled')
            release.set()
            need(first.result(timeout=1) == 'success', 'occupier_failed')
            need(queued.cancelled(), 'queued_not_cancelled')
        elif name in ('running_future_not_cancelled', 'caller_deadline_work_continues', 'normal_probe_reuses_same_slot'):
            future, release, ready = submit()
            wait_ready(ready)
            if name == 'caller_deadline_work_continues':
                event('cancel_requested', kind='caller_deadline')
                try:
                    future.result(timeout=.01)
                    raise AssertionError('deadline_not_observed')
                except FutureTimeout:
                    event('caller_returned', outcome='TimeoutError')
            else:
                event('cancel_requested', kind='future_cancel')
                result = future.cancel()
                event('cancel_result', result=result)
                need(result is False, 'running_cancel_wrong')
                event('caller_returned', outcome='cancel_false')
            state(future)
            need(future.running() and not future.done(), 'work_did_not_continue')
            if name == 'normal_probe_reuses_same_slot':
                probe, _, probe_ready = submit('probe', 'probe-job', released=True)
                need(not probe_ready.is_set() and not probe.done(), 'probe_bypassed_occupied_slot')
                state(probe, 'probe', 'probe-job')
            event('release_requested')
            release.set()
            need(future.result(timeout=1) == 'success', 'work_failed')
            if name == 'normal_probe_reuses_same_slot':
                need(probe.result(timeout=1) == 'success', 'probe_failed')
        elif name == 'cooperative_stop':
            future, release, ready = submit(mode='cooperative')
            wait_ready(ready)
            event('cancel_requested', kind='cooperative_event')
            release.set()
            need(future.result(timeout=1) == 'cancelled', 'cooperative_stop_failed')
            event('caller_returned', outcome='cancelled')
        elif name in ('process_kill_reap', 'worker_exit_without_end_marker', 'cleanup_timeout_is_failure'):
            child, birth = spawn('abrupt' if name == 'worker_exit_without_end_marker' else 'hold')
            event('cancel_requested', kind='owned_process')
            if name == 'worker_exit_without_end_marker':
                child.stdin.write(b'X')
                child.stdin.flush()
                need(reap(child, birth) == 7, 'wrong_abrupt_exit')
                event('caller_returned', outcome='work_end_unknown', work_end_right_censored=True)
            elif name == 'cleanup_timeout_is_failure':
                try:
                    child.wait(timeout=.01)
                    raise AssertionError('cleanup_not_blocked')
                except subprocess.TimeoutExpired:
                    event('cleanup_status', outcome='failed', reason='owned_work_still_alive',
                          child_pid=child.pid, child_starttime=birth)
                    event('caller_returned', outcome='cleanup_failed')
                need(reap(child, birth, kill=True) == -signal.SIGKILL, 'kill_exit_code')
            else:
                need(reap(child, birth, kill=True) == -signal.SIGKILL, 'kill_exit_code')
                event('caller_returned', outcome='killed_and_reaped')
        elif name == 'worker_exception':
            future, release, ready = submit(mode='error')
            wait_ready(ready)
            release.set()
            try:
                future.result(timeout=1)
                raise AssertionError('worker_exception_not_propagated')
            except RuntimeError as exc:
                need(str(exc) == 'expected_worker_exception', 'wrong_worker_exception')
                event('caller_returned', outcome='RuntimeError')
        elif name == 'completion_wins_cancel_race':
            future, _, ready = submit(released=True)
            wait_ready(ready)
            need(future.result(timeout=1) == 'success', 'completion_failed')
            event('cancel_requested', kind='after_completion')
            result = future.cancel()
            event('cancel_result', result=result)
            need(result is False, 'completed_future_cancelled')
            state(future)
            event('caller_returned', outcome='already_completed')
        elif name == 'shared_work_has_other_waiter':
            waiters = {'A', 'B'}
            event('waiter_attached', 'A', 'shared-job', waiters=sorted(waiters))
            event('waiter_attached', 'B', 'shared-job', waiters=sorted(waiters))
            future, release, ready = submit(shared='shared-job')
            wait_ready(ready)
            event('cancel_requested', shared='shared-job', kind='detach_waiter')
            waiters.remove('A')
            event('waiter_detached', shared='shared-job', waiters=sorted(waiters))
            event('caller_returned', shared='shared-job', outcome='waiter_cancelled')
            state(future, shared='shared-job')
            need(waiters == {'B'} and future.running(), 'shared_work_wrongly_stopped')
            release.set()
            need(future.result(timeout=1) == 'success', 'remaining_waiter_failed')
            event('caller_returned', 'B', 'shared-job', outcome='success')
        else:
            raise ValueError('unknown_case')
        status = 'complete'
    except BaseException as error:
        event('fixture_error', error=type(error).__name__ + ':' + str(error))
        traceback.print_exc(file=sys.stderr)
    finally:
        for release in releases:
            release.set()
        for child, birth in children:
            if child.poll() is None:
                reap(child, birth, kill=True)
        pool.shutdown(wait=True, cancel_futures=True)
        signal.setitimer(signal.ITIMER_REAL, 0)
        need(not any(counts[k] for k in ('forbidden_imports', 'network_attempts', 'file_attempts', 'unexpected_subprocess')), 'guard_violation')
        event('cleanup_complete', children=[dict(pid=c.pid, starttime=b, exit_code=c.returncode,
              identity_still_present=same(c.pid, b)) for c, b in children], counts=counts)
        event('fixture_complete', status=status, elapsed_seconds=time.monotonic() - started)
    return 0 if status == 'complete' else 1


def descendants(pid):
    found = []
    todo = [pid]
    while todo:
        current = todo.pop()
        row = proc(current)
        if row is None:
            continue
        found.append(row)
        try:
            children = Path(f'/proc/{current}/task/{current}/children').read_text()
            todo.extend(int(n) for n in children.split())
        except (FileNotFoundError, ProcessLookupError):
            pass
    return found


def launch(args, cfg):
    out = (ROOT / cfg['run']).resolve()
    need(out.parent == ROOT / 'results', 'run_path')
    out.mkdir(exist_ok=False)
    start = time.monotonic()
    record = dict(status='running', pid=os.getpid(), children=[], rows=0, model_outputs=0,
                  new_CPU_runs=1, real_backend_calls=0)
    active = None
    active_birth = None
    try:
        save(out / 'execution_snapshot.json', dict(registration_sha256=args.registration_sha256,
             python=sys.version, executable=sys.executable, argv=sys.argv, pid=os.getpid(),
             pid_starttime=proc(os.getpid())['starttime'], monotonic_ns=time.monotonic_ns(),
             source_sha256=cfg['source_sha256'], input_sha256=cfg['input_sha256']))
        (out / 'registration_snapshot.json').write_bytes(REG.read_bytes())
        for rel in cfg['source_sha256']:
            (out / ('source_' + Path(rel).name)).write_bytes((ROOT / rel).read_bytes())
        for rel in cfg['input_sha256']:
            (out / ('input_' + Path(rel).name)).write_bytes((ROOT / rel).read_bytes())
        with (out / 'process_samples.jsonl').open('x') as samples:
            for case in cfg['case_ids']:
                need(time.monotonic() - start < 115, 'total_wall_limit')
                argv = [sys.executable, '-I', '-S', '-B', str(Path(__file__).resolve()),
                        '--fixture', '--case', case, '--registration-sha256', args.registration_sha256]
                with (out / (case + '.jsonl')).open('x') as events, (out / (case + '.stderr')).open('x') as errors:
                    child = subprocess.Popen(argv, cwd=ROOT, stdout=events, stderr=errors, start_new_session=True)
                    birth = proc(child.pid)['starttime']
                    active, active_birth = child, birth
                    item = dict(case_id=case, pid=child.pid, starttime=birth)
                    record['children'].append(item)
                    deadline = time.monotonic() + 3
                    while child.poll() is None:
                        now = time.monotonic_ns()
                        rows = descendants(child.pid)
                        need(len(rows) <= 2, 'work_process_cap')
                        samples.write(json.dumps(dict(case_id=case, observer_ns=now, processes=rows)) + '\n')
                        if time.monotonic() > deadline:
                            need(same(child.pid, birth), 'watchdog_identity')
                            os.killpg(child.pid, signal.SIGKILL)
                            child.wait(timeout=1)
                            item.update(exit_code=child.returncode, timeout=True)
                            raise TimeoutError('case_watchdog:' + case)
                        time.sleep(.01)
                    item['exit_code'] = child.wait()
                    active = None
                    item['identity_still_present'] = same(child.pid, birth)
                    need(item['exit_code'] == 0, 'case_failed:' + case)
        save(out / 'case_processes.json', record['children'])
        save(out / 'worker_manifest.json', {str(p.relative_to(out)): sha(p) for p in out.iterdir() if p.is_file()})
        argv = [sys.executable, '-I', '-S', '-B', str(ROOT / 'scripts/verify_structured_observer.py'), str(out)]
        with (out / 'verifier.log').open('x') as log:
            verifier = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT, start_new_session=True)
            record['verifier_pid'] = verifier.pid
            try:
                record['verifier_exit_code'] = verifier.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(verifier.pid, signal.SIGKILL)
                verifier.wait(timeout=1)
                raise
        need(record['verifier_exit_code'] == 0, 'independent_verifier_failed')
        record.update(status='complete', cases=12)
    except BaseException as error:
        if active is not None and active.poll() is None:
            if same(active.pid, active_birth):
                os.killpg(active.pid, signal.SIGKILL)
            active.wait(timeout=1)
        record.update(status='failed', error=type(error).__name__ + ':' + str(error))
        (out / 'launcher_traceback.txt').write_text(traceback.format_exc())
    finally:
        record['elapsed_seconds'] = time.monotonic() - start
        sys.path.insert(0, str(ROOT / 'scripts'))
        from checked_archive import finalize_archive
        closure = finalize_archive(out, record, 64, 8 * 1024 * 1024)
        print(json.dumps(dict(record, archive_closure=closure)), flush=True)
    return 0 if closure['status'] == 'complete' else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--fixture', action='store_true')
    parser.add_argument('--task', choices=['hold', 'abrupt'])
    parser.add_argument('--case')
    parser.add_argument('--ready-fd', type=int)
    args = parser.parse_args()
    cfg = registration(args.registration_sha256)
    if args.task:
        return task(args, cfg)
    if args.fixture:
        need(args.case in cfg['case_ids'], 'registered_case')
        return fixture(args, cfg)
    need(args.execute, 'explicit_execute_required')
    return launch(args, cfg)


if __name__ == '__main__':
    sys.exit(main())
