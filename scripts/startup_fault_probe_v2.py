"""Two registered, bounded GDB probes of Torch import; no semantic work."""
import argparse
import faulthandler
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    with p.open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write('\n')


def identity(pid):
    text = Path(f'/proc/{pid}/stat').read_text()
    return int(text[text.rindex(')') + 2:].split()[19])


def check(args):
    path = ROOT / args.registration
    assert path.parent == ROOT / 'configs' and sha(path) == args.sha256
    cfg = json.loads(path.read_text())
    assert cfg['execution_enabled'] and cfg['cases'] == ['periodic', 'fatal_only']
    assert cfg['case_seconds'] == 30 and cfg['total_seconds'] == 75
    for name, digest in {**cfg['source_sha256'], **cfg['input_sha256']}.items():
        assert sha(ROOT / name) == digest, name
    for field in ('runtime_pin', 'extra_runtime_pin'):
        for name, digest in json.loads((ROOT / cfg[field]).read_text()).items():
            assert sha(ROOT / name) == digest, name
    for name, pin in json.loads((ROOT / cfg['tools_pin']).read_text()).items():
        p = Path(name)
        st = p.stat()
        assert sha(p) == pin['sha256'] and st.st_dev == pin['dev'] and st.st_ino == pin['ino']
    return cfg, path


def worker(cfg, args):
    out = ROOT / cfg['run'] / args.case
    for key, value in cfg['environment'].items():
        os.environ[key] = str(out / value[4:]) if value.startswith('RUN/') else value
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    import tempfile
    tempfile.tempdir = str(out / 'tmp')
    sys.path.insert(0, str(ROOT / 'scripts'))
    events = (out / 'events.jsonl').open('x')
    owner = [os.getpid(), identity(os.getpid())]
    seq = 0

    def emit(event, **fields):
        nonlocal seq
        seq += 1
        row = dict(event=event, ns=time.monotonic_ns(), seq=seq,
                   pid=owner[0], starttime=owner[1], tid=threading.get_native_id())
        row.update(fields)
        events.write(json.dumps(row, sort_keys=True) + '\n')
        events.flush()

    stream = (out / 'stacks.txt').open('x')
    faulthandler.enable(file=stream, all_threads=True)
    emit('worker_bootstrap', case=args.case, owner=owner, parent_spawn_ns=args.spawn_ns,
         fatal_enabled=faulthandler.is_enabled(), core_limit=list(resource.getrlimit(resource.RLIMIT_CORE)),
         affinity=sorted(os.sched_getaffinity(0)), python=sys.version,
         executable=os.path.realpath(sys.executable), sys_path=sys.path)
    if args.case == 'launcher_smoke':
        save(out / 'worker-status.json', dict(status='complete', target_imports=0, case=args.case))
        emit('smoke_complete')
        faulthandler.disable()
        stream.close()
        events.close()
        return 0
    from import_boundary_v2 import ImportBoundary
    guard = ImportBoundary(ROOT, out, json.loads((ROOT / cfg['boundary_pins']).read_text()), emit)
    guard.install()
    status = dict(status='running', case=args.case, pid=owner[0], starttime=owner[1])
    try:
        if args.case == 'periodic':
            faulthandler.dump_traceback_later(1, repeat=True, file=stream)
        emit('diagnostic_mode', periodic=args.case == 'periodic', fatal_enabled=faulthandler.is_enabled())
        emit('torch_import_begin')
        import torch
        emit('torch_import_end')
        emit('thread_settings_begin')
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        emit('thread_settings_end')
        initialized = torch.cuda.is_initialized()
        assert not initialized
        assert not any(guard.counts[k] for k in ('file_denied', 'process_denied', 'forbidden_imports'))
        assert time.monotonic_ns() - args.spawn_ns < 30_000_000_000
        status.update(status='complete', torch_import_complete=True, cuda_initialized=initialized)
    except BaseException as exc:
        status.update(status='failed', error=repr(exc))
        (out / 'traceback.txt').write_text(traceback.format_exc())
    finally:
        if args.case == 'periodic':
            faulthandler.cancel_dump_traceback_later()
        faulthandler.disable()
        stream.close()
        status['boundary_counts'] = dict(guard.counts)
        emit('worker_complete', status=status['status'])
        save(out / 'worker-status.json', status)
        events.close()
    return 0 if status['status'] == 'complete' else 1


def debugger(cfg, args):
    # Apply output/core bounds before exec; GDB and its inferior inherit them.
    resource.setrlimit(resource.RLIMIT_FSIZE, (524288, 524288))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONFAULTHANDLER', None)
    env.update(DEBUGINFOD_URLS='', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    commands = [
        'set auto-load off', 'set debuginfod enabled off', 'set pagination off',
        'set confirm off', 'set disable-randomization off', 'set startup-with-shell off',
        'set print thread-events off', 'set print elements 16',
        'set environment PYTHONPATH=' + str(ROOT / '.venv-controller-history/lib/python3.11/site-packages'),
        'handle SIGSEGV stop print nopass', 'handle SIGBUS stop print nopass',
        'run', 'echo PROBE_SELECTED_BACKTRACE\\n',
        'if $_isvoid($_exitcode) && $_isvoid($_exitsignal)\nbt 20\nend',
        'echo PROBE_ALL_THREADS\\n', 'thread apply all bt 12',
        'info program', 'echo PROBE_DEBUGGER_END\\n', 'quit']
    command_path = ROOT / cfg['run'] / args.case / 'commands.gdb'
    command_path.write_text('\n'.join(commands) + '\n')
    # GDB reconstructs inferior argv; avoid its shell-disabled space escaping.
    # The resolved interpreter is the same pinned executable as the venv link.
    argv = ['/usr/bin/gdb', '-nx', '-nh', '--batch', '-iex', 'set auto-load off', '-x', str(command_path)]
    argv += ['--args', str((ROOT / '.venv-controller-history/bin/python').resolve()), '-B', '-S',
             str(Path(__file__).relative_to(ROOT)), '--worker', '--registration', args.registration,
             '--sha256', args.sha256, '--case', args.case, '--spawn-ns', str(args.spawn_ns)]
    save(ROOT / cfg['run'] / args.case / 'debugger-argv.json', argv)
    os.execve(argv[0], argv, env)


def descendants(pid):
    found = []
    pending = [pid]
    while pending:
        parent = pending.pop()
        try:
            children = Path(f'/proc/{parent}/task/{parent}/children').read_text().split()
        except FileNotFoundError:
            continue
        for child in map(int, children):
            try:
                found.append((child, identity(child)))
                pending.append(child)
            except FileNotFoundError:
                pass
    return found


def stop_owned(owners):
    for pid, stamp in reversed(owners):
        try:
            if identity(pid) == stamp:
                os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except FileNotFoundError:
            pass


def launch(cfg, path, args, started):
    out = ROOT / cfg['run']
    out.mkdir(exist_ok=False)
    summary = dict(status='running', pid=os.getpid(), starttime=identity(os.getpid()),
                   rows=0, model_outputs=0, cases=[])
    active = None
    owners = []
    try:
        (out / 'registration_snapshot.json').write_bytes(path.read_bytes())
        for i, (name, digest) in enumerate({**cfg['source_sha256'], **cfg['input_sha256']}.items()):
            (out / f'snapshot-{i:02d}-{Path(name).name}').write_bytes((ROOT / name).read_bytes())
        for case in ['launcher_smoke'] + cfg['cases']:
            case_out = out / case
            case_out.mkdir()
            (case_out / 'tmp').mkdir()
            begun = time.monotonic_ns()
            case_limit = 5 if case == 'launcher_smoke' else 30
            record = dict(case=case, spawn_ns=begun, timed_out=False)
            with (case_out / 'gdb.log').open('x') as log, (case_out / 'process-samples.jsonl').open('x') as samples:
                argv = [sys.executable, '-I', '-S', '-B', str(Path(__file__).resolve()), '--debugger',
                        '--registration', args.registration, '--sha256', args.sha256,
                        '--case', case, '--spawn-ns', str(begun)]
                active = subprocess.Popen(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                owners = [(active.pid, identity(active.pid))]
                record.update(debugger_pid=owners[0][0], debugger_starttime=owners[0][1])
                while active.poll() is None:
                    for item in descendants(active.pid):
                        if item not in owners:
                            owners.append(item)
                    samples.write(json.dumps(dict(ns=time.monotonic_ns(), owners=owners)) + '\n')
                    if time.monotonic_ns() - begun >= case_limit * 1_000_000_000 or time.monotonic() - started >= 70:
                        record['timed_out'] = True
                        stop_owned(owners)
                        break
                    time.sleep(.02)
                record['debugger_exit_code'] = active.wait(timeout=2)
                record['debugger_end_ns'] = time.monotonic_ns()
                active = None
            stop_owned(owners)
            record['owned_processes'] = owners
            save(case_out / 'process-record.json', record)
            summary['cases'].append(record)
            if case == 'launcher_smoke':
                smoke = json.loads((case_out / 'worker-status.json').read_text())
                assert smoke['status'] == 'complete' and smoke['target_imports'] == 0
                assert record['debugger_exit_code'] == 0 and not record['timed_out']
                assert 'PROBE_DEBUGGER_END' in (case_out / 'gdb.log').read_text()
            assert time.monotonic() - started < 70
        save(out / 'pre_verification_manifest.json', {
            str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()})
        with (out / 'verifier.log').open('x') as log:
            verifier = subprocess.Popen([sys.executable, '-I', '-S', '-B', str(ROOT / 'scripts/verify_startup_fault_probe_v2.py'), str(out)],
                                        cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            stamp = identity(verifier.pid)
            summary.update(verifier_pid=verifier.pid, verifier_starttime=stamp)
            try:
                summary['verifier_exit_code'] = verifier.wait(timeout=min(4, max(.01, 74 - (time.monotonic() - started))))
            except subprocess.TimeoutExpired:
                stop_owned([(verifier.pid, stamp)])
                verifier.wait(timeout=1)
                raise
        assert summary['verifier_exit_code'] == 0
        assert time.monotonic() - started < 75
        summary['status'] = 'complete'
    except BaseException as exc:
        stop_owned(owners)
        if active is not None:
            active.wait(timeout=2)
        summary.update(status='failed', error=repr(exc))
        (out / 'launcher-traceback.txt').write_text(traceback.format_exc())
    finally:
        summary['launcher_seconds'] = time.monotonic() - started
        sys.path.insert(0, str(ROOT / 'scripts'))
        from checked_archive import finalize_archive
        archive = finalize_archive(out, summary, 64, 8388608)
        print(json.dumps(dict(summary, archive=archive)))
    return 0 if archive['status'] == 'complete' else 1


if __name__ == '__main__':
    started = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--debugger', action='store_true')
    parser.add_argument('--case', choices=['launcher_smoke', 'periodic', 'fatal_only'])
    parser.add_argument('--spawn-ns', type=int)
    args = parser.parse_args()
    cfg, path = check(args)
    if args.worker:
        sys.exit(worker(cfg, args))
    if args.debugger:
        debugger(cfg, args)
    assert args.execute
    sys.exit(launch(cfg, path, args, started))
