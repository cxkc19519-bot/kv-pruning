"""Original-input byte evidence and aggregate-five-second import diagnostics."""
import argparse
import faulthandler
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / 'configs/backend-diagnostic-execution-v1.json'
sys.dont_write_bytecode = True


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')


def birth(pid):
    text = Path(f'/proc/{pid}/stat').read_text()
    return int(text[text.rindex(')')+2:].split()[19])


def config(digest):
    need(str(ROOT) == '/home/user/jhk/project/Directional Exploration/kv-pruning', 'server_only')
    need(sha(REG) == digest, 'registration_pin')
    cfg = json.loads(REG.read_text())
    need(cfg['execution_enabled'], 'execution_disabled')
    for path, expected in {**cfg['source_sha256'], **cfg['input_sha256']}.items():
        need(sha(ROOT / path) == expected, 'source_input_changed:' + path)
    for path, expected in json.loads((ROOT / cfg['runtime_pin']).read_text()).items():
        need(sha(ROOT / path) == expected, 'runtime_changed:' + path)
    return cfg


def worker(backend, cfg):
    out = ROOT / cfg['run']
    for key, value in cfg['environment'].items():
        os.environ[key] = str(out / value[4:]) if value.startswith('RUN/') else value
    (out / 'tmp').mkdir(exist_ok=True)
    import tempfile
    tempfile.tempdir = str(out / 'tmp')
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
    events = (out / (backend + '-events.jsonl')).open('x')
    sequence = 0
    calls = 0
    guard = dict(network_denied=0, subprocess_denied=0, file_denied=0, forbidden_imports=0)

    def emit(event, **fields):
        nonlocal sequence
        sequence += 1
        row = dict(event=event, seq=sequence, ns=time.monotonic_ns(), pid=os.getpid(),
                   starttime=birth(os.getpid()), tid=threading.get_native_id(), backend=backend)
        row.update(fields)
        events.write(json.dumps(row, sort_keys=True) + '\n')
        events.flush()

    def audit(event, args):
        category = None
        if event == 'import' and args[0].split('.')[0] in ('vllm', 'tensorflow', 'jax'):
            category = 'forbidden_imports'
        if event in ('socket.__new__', 'socket.connect', 'socket.bind', 'socket.sendto', 'socket.getaddrinfo'):
            category = 'network_denied'
        if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork', 'os.forkpty'):
            category = 'subprocess_denied'
        if event == 'open' and isinstance(args[0], (str, bytes)):
            p = Path(os.fsdecode(args[0])).resolve()
            mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
            if p.is_relative_to(ROOT / 'models') or p.suffix in ('.safetensors', '.bin', '.pt', '.pth') or writing and not p.is_relative_to(out):
                category = 'file_denied'
        if category:
            guard[category] += 1
            emit('guard_block', category=category, audit_event=event, counts=dict(guard))
            if category == 'network_denied':
                raise OSError('offline_socket_denied')
            raise RuntimeError('scope_forbidden:' + category)

    sys.addaudithook(audit)
    emit('guard_installed', counts=dict(guard), affinity=sorted(os.sched_getaffinity(0)))

    def call(kind, fn):
        nonlocal calls
        calls += 1
        need(calls <= 520, 'public_call_cap')
        cid = calls
        emit('call_begin', call_id=cid, kind=kind)
        try:
            value = fn()
        except BaseException as exc:
            emit('call_end', call_id=cid, kind=kind, outcome='error', error=type(exc).__name__ + ':' + str(exc))
            return None, dict(error=type(exc).__name__ + ':' + str(exc))
        emit('call_end', call_id=cid, kind=kind, outcome='success')
        return value, None

    def byte_evidence(value, expected):
        row = dict(return_type=type(value).__module__ + '.' + type(value).__qualname__,
                   direct_equals_input=value == expected, input_hex=expected.hex())
        try:
            data = bytes(value)
            row.update(actual_hex=data.hex(), actual_length=len(data),
                       normalized_equals_input=data == expected)
        except Exception as exc:
            row.update(actual_hex=None, normalization_error=type(exc).__name__ + ':' + str(exc), repr=repr(value)[:1024])
        return row

    status = dict(backend=backend, pid=os.getpid(), starttime=birth(os.getpid()), status='running', guard=guard)
    started = time.monotonic()
    stack_stream = None
    try:
        if backend == 'llguidance':
            module, error = call('public_import', lambda: __import__('llguidance'))
            need(error is None, 'public_import_failed')
            vocab = [bytes([i]) for i in range(256)] + [b'<|eos|>']

            class ByteTokenizer:
                eos_token_id = 256
                bos_token_id = None
                tokens = vocab
                special_token_ids = [256]

                def __call__(self, text):
                    return list(text.encode() if isinstance(text, str) else text)

            wrapper, error = call('wrapper_construct', lambda: module.TokenizerWrapper(ByteTokenizer()))
            need(error is None, 'wrapper_failed')
            info, error = call('tokenizer_construct', lambda: module.LLTokenizer(wrapper, n_vocab=257, eos_token=256, slices=[]))
            need(error is None, 'tokenizer_failed')
            single = []
            for token in range(257):
                value, error = call('decode_single:' + str(token), lambda: info.decode_bytes([token]))
                row = dict(token=token, error=error)
                if error is None:
                    row.update(byte_evidence(value, vocab[token]))
                single.append(row)
                emit('single_byte_evidence', evidence=row)
            value, error = call('decode_full', lambda: info.decode_bytes(list(range(256))))
            full = dict(error=error)
            if error is None:
                full.update(byte_evidence(value, bytes(range(256))))
                if full['actual_hex'] is not None:
                    actual = bytes.fromhex(full['actual_hex'])
                    expected = bytes(range(256))
                    full['first_difference'] = next((i for i in range(max(len(actual), len(expected)))
                                                     if i >= len(actual) or i >= len(expected) or actual[i] != expected[i]), None)
            emit('full_byte_evidence', evidence=full)
            special = []
            for token in range(257):
                value, error = call('is_special:' + str(token), lambda: info.is_special_token(token))
                row = dict(token=token, actual=bool(value) if error is None else None, error=error)
                special.append(row)
                emit('special_evidence', evidence=row)
            draft = json.loads((ROOT / cfg['draft']).read_text())
            probes = []
            for text in draft['llguidance_diagnostic']['tokenize_byte_probes_hex']:
                data = bytes.fromhex(text)
                value, error = call('encode_probe', lambda: info.tokenize_bytes(data))
                row = dict(input_hex=text, returned_tokens=list(value) if error is None else None, error=error)
                probes.append(row)
                emit('encoder_evidence', evidence=row)
            need(calls == 520, 'exact_public_calls')
            save(out / 'llguidance-byte-evidence.json', dict(single=single, full=full, special=special, encoder_probes=probes,
                 constructor=dict(vocab_size=257, eos_id=256, special_ids=[256], slices=[]), public_calls=calls))
        else:
            stack_stream = (out / 'xgrammar-stacks.txt').open('x')
            faulthandler.dump_traceback_later(1, repeat=True, file=stack_stream)
            emit('aggregate_import_begin', deadline_ns=5_000_000_000)
            emit('torch_import_begin')
            import torch
            emit('torch_import_end')
            emit('torch_thread_settings_begin')
            torch.set_num_threads(1)
            torch.set_num_interop_threads(1)
            emit('torch_thread_settings_end')
            emit('xgrammar_import_begin')
            import xgrammar
            emit('xgrammar_import_end')
            emit('aggregate_import_end', cuda_initialized=torch.cuda.is_initialized())
        status['status'] = 'complete'
    except BaseException as exc:
        status.update(status='failed', error=type(exc).__name__ + ':' + str(exc))
        (out / (backend + '-traceback.txt')).write_text(traceback.format_exc())
    finally:
        if stack_stream is not None:
            faulthandler.cancel_dump_traceback_later()
            stack_stream.close()
        status.update(elapsed_seconds=time.monotonic() - started, public_calls=calls)
        emit('worker_complete', status=status['status'], counts=dict(guard), public_calls=calls)
        save(out / (backend + '-status.json'), status)
        events.close()
    return 0 if status['status'] == 'complete' else 1


def launch(cfg, digest):
    out = ROOT / cfg['run']
    out.mkdir(exist_ok=False)
    begin = time.monotonic()
    summary = dict(status='running', pid=os.getpid(), starttime=birth(os.getpid()), children=[], rows=0, model_outputs=0)
    active = None
    active_birth = None

    def kill_owned(child, identity):
        need(birth(child.pid) == identity, 'owned_process_identity')
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=1)

    try:
        save(out / 'execution_snapshot.json', dict(registration_sha256=digest, argv=sys.argv, python=sys.version,
             pid=os.getpid(), source_sha256=cfg['source_sha256'], input_sha256=cfg['input_sha256']))
        (out / 'registration_snapshot.json').write_bytes(REG.read_bytes())
        for rel in cfg['source_sha256']:
            (out / ('source_' + Path(rel).name)).write_bytes((ROOT / rel).read_bytes())
        for rel in cfg['input_sha256']:
            (out / ('input_' + Path(rel).name)).write_bytes((ROOT / rel).read_bytes())
        with (out / 'process-samples.jsonl').open('x') as samples:
            for backend in ('llguidance', 'xgrammar'):
                argv = [str(ROOT / '.venv-controller-history/bin/python'), '-B', '-S', str(Path(__file__).resolve()),
                        '--worker', backend, '--registration-sha256', digest]
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
                           PYTHONPATH=str(ROOT / '.venv-controller-history/lib/python3.11/site-packages'))
                with (out / (backend + '.log')).open('x') as log:
                    child = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    active, active_birth = child, birth(child.pid)
                    item = dict(backend=backend, pid=child.pid, starttime=active_birth)
                    summary['children'].append(item)
                    born = time.monotonic()
                    while child.poll() is None:
                        now = time.monotonic_ns()
                        path = out / (backend + '-events.jsonl')
                        rows = []
                        if path.exists():
                            for line in path.read_text().splitlines():
                                try:
                                    rows.append(json.loads(line))
                                except json.JSONDecodeError:
                                    pass
                        open_calls = {}
                        for r in rows:
                            if r['event'] == 'call_begin': open_calls[r['call_id']] = r
                            if r['event'] == 'call_end': open_calls.pop(r['call_id'], None)
                        starts = [r for r in rows if r['event'] == 'aggregate_import_begin']
                        ends = [r for r in rows if r['event'] == 'aggregate_import_end']
                        aggregate_expired = bool(starts and not ends and now-starts[0]['ns'] >= 5_000_000_000)
                        call_expired = any(now-r['ns'] >= 5_000_000_000 for r in open_calls.values())
                        stack = out / 'xgrammar-stacks.txt'
                        cap = stack.exists() and stack.stat().st_size > 524288
                        samples.write(json.dumps(dict(backend=backend, ns=now, pid=child.pid, stat=Path(f'/proc/{child.pid}/stat').read_text())) + '\n')
                        if aggregate_expired or call_expired or cap or time.monotonic()-born > 10 or time.monotonic()-begin > 19:
                            item.update(watchdog=True, aggregate_deadline=aggregate_expired, call_deadline=call_expired,
                                        stack_cap=cap, watchdog_ns=now)
                            kill_owned(child, active_birth)
                            break
                        time.sleep(.01)
                    item['exit_code'] = child.wait()
                    item['identity_present_after_wait'] = Path(f'/proc/{child.pid}').exists()
                    active = None
        save(out / 'processes.json', summary['children'])
        save(out / 'worker_manifest.json', {str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
        with (out / 'verifier.log').open('x') as log:
            verifier = subprocess.Popen([sys.executable, '-I', '-S', '-B', str(ROOT / 'scripts/verify_backend_diagnostic.py'), str(out)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            summary['verifier_pid'] = verifier.pid
            summary['verifier_starttime'] = birth(verifier.pid)
            try:
                summary['verifier_exit_code'] = verifier.wait(timeout=8)
            except subprocess.TimeoutExpired:
                need(birth(verifier.pid) == summary['verifier_starttime'], 'verifier_identity')
                verifier.kill()
                verifier.wait(timeout=1)
                raise
        need(summary['verifier_exit_code'] == 0, 'independent_verifier_failed')
        need(time.monotonic()-begin <= 30, 'total_wall_bound')
        summary['status'] = 'complete'
    except BaseException as exc:
        if active is not None and active.poll() is None:
            kill_owned(active, active_birth)
        summary.update(status='failed', error=type(exc).__name__ + ':' + str(exc))
        (out / 'launcher-traceback.txt').write_text(traceback.format_exc())
    finally:
        summary['elapsed_seconds'] = time.monotonic()-begin
        sys.path.insert(0, str(ROOT / 'scripts'))
        from checked_archive import finalize_archive
        closure = finalize_archive(out, summary, 64, 8388608)
        print(json.dumps(dict(summary, archive=closure)))
    return 0 if closure['status'] == 'complete' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--worker', choices=['llguidance', 'xgrammar'])
    args = parser.parse_args()
    cfg = config(args.registration_sha256)
    if args.worker:
        sys.exit(worker(args.worker, cfg))
    need(args.execute, 'explicit_execute')
    sys.exit(launch(cfg, args.registration_sha256))
