"""Pinned CPU-only finite semantic checks; no model/tokenizer files or service."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / 'configs/legacy-backend-cpu-execution-v1.json'
sys.dont_write_bytecode = True


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    with path.open('x') as f:
        json.dump(data, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')


def config(digest):
    need(str(ROOT) == '/home/user/jhk/project/Directional Exploration/kv-pruning', 'server_only')
    need(sha(REG) == digest, 'registration_pin')
    cfg = json.loads(REG.read_text())
    need(cfg['execution_enabled'], 'disabled')
    for rel, expected in {**cfg['source_sha256'], **cfg['input_sha256']}.items():
        need(sha(ROOT / rel) == expected, 'changed:' + rel)
    for rel, expected in json.loads((ROOT / cfg['runtime_pin']).read_text()).items():
        need(sha(ROOT / rel) == expected, 'runtime_changed:' + rel)
    return cfg


def worker(backend, cfg):
    out = ROOT / cfg['run']
    for key, value in cfg['environment'].items():
        os.environ[key] = str(out / value[4:]) if value.startswith('RUN/') else value
    (out / 'tmp').mkdir(exist_ok=True)
    import tempfile
    tempfile.tempdir = str(out / 'tmp')
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
    guard = dict(network_denied=0, subprocess_denied=0, file_denied=0, forbidden_imports=0)

    def audit(event, args):
        if event == 'import' and args[0].split('.')[0] in ('vllm', 'tensorflow', 'jax'):
            guard['forbidden_imports'] += 1
            raise RuntimeError('forbidden_import')
        if event in ('socket.__new__', 'socket.connect', 'socket.bind', 'socket.sendto', 'socket.getaddrinfo'):
            guard['network_denied'] += 1
            raise OSError('offline_socket_denied')
        if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork', 'os.forkpty'):
            guard['subprocess_denied'] += 1
            raise RuntimeError('compilation_or_subprocess_forbidden')
        if event == 'open' and isinstance(args[0], (str, bytes)):
            p = Path(os.fsdecode(args[0])).resolve()
            mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
            if p.is_relative_to(ROOT / 'models') or p.suffix in ('.safetensors', '.bin', '.pt', '.pth') or writing and not p.is_relative_to(out):
                guard['file_denied'] += 1
                raise RuntimeError('file_scope_forbidden:' + str(p))
    sys.addaudithook(audit)
    events = (out / (backend + '-events.jsonl')).open('x')
    lock = threading.Lock()
    seq = 0
    active = None
    heartbeat_counts = {}
    stopped = threading.Event()
    ready = threading.Event()

    def emit(event, **fields):
        nonlocal seq
        with lock:
            seq += 1
            row = dict(event=event, seq=seq, ns=time.monotonic_ns(), pid=os.getpid(),
                       tid=threading.get_native_id(), backend=backend)
            row.update(fields)
            events.write(json.dumps(row, sort_keys=True) + '\n')
            events.flush()

    def heartbeat():
        ready.set()
        while not stopped.wait(.001):
            current = active
            if current is not None:
                heartbeat_counts[current] = heartbeat_counts.get(current, 0) + 1
                emit('heartbeat', call_id=current)

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    need(ready.wait(1), 'heartbeat_start')
    calls = 0
    counters = dict(schema_specs=0, matcher_constructions=0, mask_calls=0, commit_calls=0)

    def call(kind, fn):
        nonlocal calls, active
        calls += 1
        cid = calls
        emit('call_begin', call_id=cid, kind=kind)
        active = cid
        try:
            result = fn()
        except BaseException as e:
            active = None
            emit('call_end', call_id=cid, kind=kind, outcome='error', error=type(e).__name__ + ':' + str(e))
            raise
        active = None
        emit('call_end', call_id=cid, kind=kind, outcome='success')
        return result

    started = time.monotonic()
    result = dict(backend=backend, pid=os.getpid(), status='running', counters=counters,
                  cases=[], guard=guard, real_model_calls=0)
    try:
        interval = sys.getswitchinterval()
        sys.setswitchinterval(.1)

        def hold():
            deadline = time.perf_counter() + .025
            while time.perf_counter() < deadline:
                pass
        try:
            call('control_python_holds_GIL', hold)
            call('control_sleep_releases_GIL', lambda: time.sleep(.025))
        finally:
            sys.setswitchinterval(interval)
        need(heartbeat_counts.get(1, 0) == 0 and heartbeat_counts.get(2, 0) > 0,
             'GIL_observer_controls_failed_before_backend_import')
        if backend == 'xgrammar':
            def imports():
                global torch, xgr
                import torch
                torch.set_num_threads(1)
                torch.set_num_interop_threads(1)
                import xgrammar as xgr
            call('import', imports)
            need(not torch.cuda.is_initialized(), 'CUDA_initialized')
        else:
            def imports():
                global llg
                import llguidance as llg
            call('import', imports)
        vocab = [bytes([i]) for i in range(256)] + [b'<|eos|>']

        class ByteTokenizer:
            eos_token_id = 256
            bos_token_id = None
            tokens = vocab
            special_token_ids = [256]

            def __call__(self, text):
                return list(text.encode() if isinstance(text, str) else text)

        if backend == 'xgrammar':
            info = call('tokenizer_info', lambda: xgr.TokenizerInfo(vocab, xgr.VocabType.RAW, vocab_size=257, stop_token_ids=[256]))
            compiler = call('compiler_init', lambda: xgr.GrammarCompiler(info, max_threads=1, cache_enabled=False, cache_limit_bytes=8388608))
            mask_tensor = torch.empty((1, 9), dtype=torch.int32, device='cpu')
            need(info.vocab_size == 257, 'vocab_size')
            need(list(info.decoded_vocab[:256]) == vocab[:256], 'decode_byte_roundtrip')
        else:
            info = call('tokenizer_info', lambda: llg.LLTokenizer(llg.TokenizerWrapper(ByteTokenizer()), n_vocab=257, eos_token=256, slices=[]))
            need(info.vocab_size == 257 and info.eos_token == 256, 'vocab_eos')
            need(info.decode_bytes(list(range(256))) == bytes(range(256)), 'decode_byte_roundtrip')
            need(info.tokenize_bytes(b'test') == list(b'test'), 'encode_byte_roundtrip')
        emit('vocab_verified', size=257, eos=256, raw_bytes_sha256=hashlib.sha256(b''.join(vocab)).hexdigest())
        selection = json.loads((ROOT / cfg['selection']).read_text())
        with (out / (backend + '-masks.jsonl')).open('x') as masks:
            for case in selection['cases']:
                counters['schema_specs'] += 1
                cid = case['case_id']
                schema = case['schema']
                try:
                    if backend == 'xgrammar':
                        grammar = call('schema_compile:' + cid, lambda: compiler.compile_json_schema(schema, strict_mode=False, any_whitespace=True))
                    else:
                        grammar = call('schema_conversion:' + cid, lambda: llg.LLMatcher.grammar_from_json_schema(schema))
                except Exception as exc:
                    result['cases'].append(dict(case_id=cid, status='schema_error', error=type(exc).__name__ + ':' + str(exc), tests=[]))
                    continue
                group = dict(case_id=cid, status='complete', tests=[])
                result['cases'].append(group)
                for index, test in enumerate(case['tests']):
                    text = json.dumps(test['data'], ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)
                    tokens = list(text.encode()) + [256]
                    counters['matcher_constructions'] += 1
                    entry = dict(index=index, expected=test['valid'], serialized=text,
                                 status='running', accepted=None, steps=0)
                    group['tests'].append(entry)
                    try:
                        matcher = call('matcher_init', lambda: xgr.GrammarMatcher(grammar) if backend == 'xgrammar' else llg.LLMatcher(info, grammar, log_level=0))
                        if backend == 'llguidance' and matcher.is_error():
                            raise ValueError('native_grammar_error:' + matcher.get_error())
                        accepted = True
                        for position, token in enumerate(tokens):
                            counters['mask_calls'] += 1
                            need(counters['mask_calls'] <= 1215, 'mask_cap')
                            if backend == 'xgrammar':
                                call('mask', lambda: matcher.fill_next_token_bitmask(mask_tensor))
                                raw = b''.join(struct.pack('<I', n & 0xffffffff) for n in mask_tensor[0].tolist())
                            else:
                                raw = call('mask', matcher.compute_bitmask)
                                need(not matcher.is_error(), 'native_mask_error:' + matcher.get_error())
                            need(len(raw) >= 33, 'short_mask')
                            allowed = bool(raw[token // 8] & (1 << (token % 8)))
                            record = dict(case_id=cid, test_index=index, position=position, token=token,
                                          raw_mask_hex=raw.hex(), allowed=allowed, commit_result=None)
                            entry['steps'] += 1
                            if not allowed:
                                accepted = False
                                masks.write(json.dumps(record) + '\n')
                                break
                            counters['commit_calls'] += 1
                            committed = call('commit', lambda: matcher.accept_token(token) if backend == 'xgrammar' else matcher.consume_token(token))
                            record['commit_result'] = bool(committed)
                            masks.write(json.dumps(record) + '\n')
                            need(committed, 'mask_commit_disagreement')
                        entry.update(status='complete', accepted=accepted, matches_label=accepted == test['valid'])
                    except Exception as exc:
                        entry.update(status='error', error=type(exc).__name__ + ':' + str(exc))
        need(counters['schema_specs'] == 8 and counters['matcher_constructions'] <= 45, 'construction_cap')
        result['cuda_initialized'] = torch.cuda.is_initialized() if backend == 'xgrammar' else None
        need(not result['cuda_initialized'], 'CUDA_initialized_at_end')
        result['status'] = 'complete'
    except BaseException as exc:
        result.update(status='failed', error=type(exc).__name__ + ':' + str(exc))
        (out / (backend + '-traceback.txt')).write_text(traceback.format_exc())
    finally:
        stopped.set()
        thread.join(timeout=1)
        result['elapsed_seconds'] = time.monotonic() - started
        result['native_counters_scope'] = '8 unique schema specs; llguidance native preparation also occurs in each of up to45 matcher constructors'
        emit('worker_complete', status=result['status'], counters=counters, guard=guard)
        events.close()
        save(out / (backend + '-result.json'), result)
    return 0 if result['status'] == 'complete' else 1


def launch(cfg, digest):
    out = ROOT / cfg['run']
    out.mkdir(exist_ok=False)
    start = time.monotonic()
    summary = dict(status='running', pid=os.getpid(), children=[], rows=0, model_outputs=0)
    active_child = None
    active_birth = None

    def birth(pid):
        text = Path('/proc/' + str(pid) + '/stat').read_text()
        return int(text[text.rindex(')')+2:].split()[19])

    def kill_owned(child, expected):
        need(birth(child.pid) == expected, 'owned_PID_starttime')
        os.killpg(child.pid, 9)
        child.wait(timeout=1)
    try:
        save(out / 'execution_snapshot.json', dict(registration_sha256=digest, argv=sys.argv,
             python=sys.version, pid=os.getpid(), source_sha256=cfg['source_sha256'], input_sha256=cfg['input_sha256']))
        (out / 'registration_snapshot.json').write_bytes(REG.read_bytes())
        for rel in cfg['source_sha256']:
            (out / ('source_' + Path(rel).name)).write_bytes((ROOT / rel).read_bytes())
        for rel in cfg['input_sha256']:
            (out / ('input_' + Path(rel).name)).write_bytes((ROOT / rel).read_bytes())
        with (out / 'external-samples.jsonl').open('x') as samples:
            for backend in ('xgrammar', 'llguidance'):
                argv = [str(ROOT / '.venv-controller-history/bin/python'), '-B', '-S',
                        str(Path(__file__).resolve()), '--worker', backend, '--registration-sha256', digest]
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
                # -S avoids .pth/site startup. Add precisely the pinned existing site.
                env['PYTHONPATH'] = str(ROOT / '.venv-controller-history/lib/python3.11/site-packages')
                with (out / (backend + '.log')).open('x') as log:
                    child = subprocess.Popen(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
                    active_child, active_birth = child, birth(child.pid)
                    summary['children'].append(dict(backend=backend, pid=child.pid, starttime=active_birth))
                    phase_file = out / (backend + '-events.jsonl')
                    born = time.monotonic()
                    timed_out = False
                    while child.poll() is None:
                        now = time.monotonic_ns()
                        outstanding = {}
                        if phase_file.exists():
                            for line in phase_file.read_text().splitlines():
                                try:
                                    row = json.loads(line)
                                except json.JSONDecodeError:
                                    continue
                                if row['event'] == 'call_begin': outstanding[row['call_id']] = row
                                if row['event'] == 'call_end': outstanding.pop(row['call_id'], None)
                        stat = Path('/proc/' + str(child.pid) + '/stat')
                        if stat.exists():
                            samples.write(json.dumps(dict(backend=backend, ns=now, pid=child.pid, stat=stat.read_text())) + '\n')
                        if time.monotonic() - start > 175 or time.monotonic() - born > 80 or any(now-r['ns'] > 5_000_000_000 for r in outstanding.values()):
                            kill_owned(child, active_birth)
                            timed_out = True
                            break
                        time.sleep(.01)
                    summary['children'][-1].update(exit_code=child.wait(), watchdog_timeout=timed_out)
                    active_child = None
        # Failures do not erase the other backend's independent diagnostic.
        save(out / 'worker_manifest.json', {str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
        with (out / 'verifier.log').open('x') as log:
            verifier = subprocess.run([sys.executable, '-I', '-S', '-B', str(ROOT / 'scripts/verify_legacy_backend_cpu.py'), str(out)], stdout=log, stderr=subprocess.STDOUT, timeout=10)
        summary['verifier_exit_code'] = verifier.returncode
        need(verifier.returncode == 0, 'independent_verifier_failed')
        need(all(c['exit_code'] == 0 for c in summary['children']), 'backend_worker_failed')
        summary['status'] = 'complete'
    except BaseException as exc:
        if active_child is not None and active_child.poll() is None:
            kill_owned(active_child, active_birth)
        summary.update(status='failed', error=type(exc).__name__ + ':' + str(exc))
        (out / 'launcher-traceback.txt').write_text(traceback.format_exc())
    finally:
        summary['elapsed_seconds'] = time.monotonic() - start
        sys.path.insert(0, str(ROOT / 'scripts'))
        from checked_archive import finalize_archive
        closure = finalize_archive(out, summary, 64, 8388608)
        print(json.dumps(dict(summary, archive=closure)))
    return 0 if closure['status'] == 'complete' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--worker', choices=['xgrammar', 'llguidance'])
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    cfg = config(args.registration_sha256)
    if args.worker:
        sys.exit(worker(args.worker, cfg))
    need(args.execute, 'explicit_execute')
    sys.exit(launch(cfg, args.registration_sha256))
