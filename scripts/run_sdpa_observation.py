"""Registered same-prefix KV GPU engineering and independent binary verifier watchdog."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import time
import traceback

ROOT = Path(__file__).resolve().parent.parent
REG = 'configs/sdpa-observation-v1.json'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    p.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def registration(digest):
    need(str(ROOT) == '/home/user/jhk/project/Directional Exploration/kv-pruning', 'registered_server_only')
    need(sha(ROOT / REG) == digest, 'registration_pin')
    cfg = json.loads((ROOT / REG).read_text())
    need(cfg['execution_enabled'] is True and cfg['mode'] == 'GPU_SDPA_observation_only', 'execution_scope')
    need(all(cfg[k] is False for k in ('network_enabled', 'next_GPU_execution_enabled')), 'no_model_scope')
    for rel, digest in {**cfg['source_sha256'], **cfg['input_sha256']}.items():
        need(sha(ROOT / rel) == digest, 'source_or_input_pin:' + rel)
    need(cfg['tokenizer_enabled'] is True, 'native_tokenizer_scope')
    need(cfg['model_inference_enabled'] is True and cfg['GPU_enabled'] is True, 'registered_GPU_scope')
    need(sha(Path(cfg['blocked_probe_source']['path'])) == cfg['blocked_probe_source']['sha256'], 'probe_source_pin')
    directory = Path(cfg['model']['path'])
    need(directory.name == cfg['model']['revision'], 'model_revision')
    for name, digest in cfg['model']['metadata_sha256'].items():
        need(sha(directory / name) == digest, 'metadata_pin:' + name)
    return cfg


def child(stage, cfg):
    out = ROOT / cfg['run']
    import tempfile
    tempfile.tempdir = str(out / 'runtime-tmp')
    start = time.monotonic()
    guard = dict(forbidden_imports=0, file_attempts=0, network_attempts=0, subprocess_attempts=0)
    directory = Path(cfg['model']['path'])
    blobroot = (directory.parent.parent / 'blobs').resolve()
    metadata_paths = {(directory / name).resolve() for name in cfg['model']['metadata_sha256']}
    weight_paths = {(directory / name).resolve() for name in cfg['weights']}
    guard['blocked_loopback_capability_probes'] = 0
    status = dict(stage=stage, pid=os.getpid(), status='running', model_answers=0, tokenizer_encodes=None if stage == 'worker' else 0,
                  GPU_queries=0, weight_bytes_read=None, network_requests=0)

    def audit(event, args):
        forbidden = ('vllm', 'tensorflow', 'jax') + (('torch', 'transformers', 'tokenizers', 'jinja2', 'numpy') if stage == 'verifier' else ())
        if event == 'import' and args[0].split('.')[0] in forbidden:
            guard['forbidden_imports'] += 1
            raise RuntimeError('model_tokenizer_import_forbidden')
        if event.startswith('socket.') and event != 'socket.__new__':
            caller = sys._getframe(1)
            probe = cfg['blocked_probe_source']
            if (event == 'socket.bind' and args[1] == ('::1', 0) and caller.f_code.co_name == '_has_ipv6'
                    and caller.f_code.co_filename == probe['path']):
                guard['blocked_loopback_capability_probes'] += 1
                raise OSError('deny_pinned_optional_loopback_probe')
            guard['network_attempts'] += 1
            raise RuntimeError('socket_operation_forbidden')
        if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork', 'os.forkpty'):
            guard['subprocess_attempts'] += 1
            raise RuntimeError('subprocess_forbidden')
        if event == 'open' and isinstance(args[0], (str, bytes)):
            p = Path(os.fsdecode(args[0])).resolve()
            mode, flags = args[1], args[2]
            writing = isinstance(mode, str) and any(x in mode for x in 'wax+') or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
            original = Path(os.fsdecode(args[0])).absolute()
            is_model_path = original.is_relative_to(directory) or p.is_relative_to(blobroot) or p.is_relative_to(directory.resolve())
            if (p.is_relative_to(ROOT / 'models') or p.suffix in ('.safetensors', '.bin', '.pt', '.pth') and p not in weight_paths
                    or is_model_path and p not in metadata_paths | weight_paths or writing and not p.is_relative_to(out)):
                guard['file_attempts'] += 1
                raise RuntimeError('file_scope_forbidden')

    def timeout(*unused):
        raise TimeoutError(stage + '_CPU_wall_cap')

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(cfg['bounds']['worker_seconds' if stage == 'worker' else 'verifier_seconds'])
    sys.addaudithook(audit)
    try:
        if stage == 'verifier':
            for rel, digest in json.loads((out / 'worker_manifest.json').read_text()).items():
                need(sha(out / rel) == digest, 'worker_artifact_pin:' + rel)
        script = 'observe_sdpa_gpu.py' if stage == 'worker' else 'verify_sdpa_gpu.py'
        sys.path.insert(0, str(ROOT / 'scripts'))
        sys.argv = [str(ROOT / 'scripts' / script), str(out)]
        runpy.run_path(sys.argv[0], run_name='__main__')
        if stage == 'worker':
            status['tokenizer_encodes'] = json.loads((out / 'observation_summary.json').read_text())['tokenizer_encodes']
        status['weight_bytes_rehashed'] = sum((directory / name).stat().st_size for name in cfg['weights'])
        need(not any(v for k, v in guard.items() if k != 'blocked_loopback_capability_probes'), 'guard_observation')
        status['status'] = 'complete'
    except BaseException as error:
        status.update(status='failed', error=type(error).__name__ + ':' + str(error))
        (out / (stage + '_traceback.txt')).write_text(traceback.format_exc())
        raise
    finally:
        signal.alarm(0)
        status['elapsed_seconds'] = time.monotonic() - start
        save(out / (stage + '_guard.json'), guard)
        save(out / (stage + '_status.json'), status)
        print(json.dumps(status), flush=True)


def launch(cfg, digest):
    out = (ROOT / cfg['run']).resolve()
    need(out.parent == (ROOT / 'results').resolve(), 'run_boundary')
    out.mkdir(exist_ok=False)
    (out / 'runtime-tmp').mkdir(exist_ok=False)
    start = time.monotonic()
    record = dict(status='running', pid=os.getpid(), children=[], main_outputs=0, engineering_outputs=0,
                  real_model_logits=0, real_KV_signal_observed=False)
    try:
        gpu_query = subprocess.run(['nvidia-smi', '-i', cfg['gpu_uuid'], '--query-gpu=memory.used,utilization.gpu',
                                  '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True, timeout=15)
        used, util = [int(x.strip()) for x in gpu_query.stdout.strip().split(',')]
        save(out / 'gpu_preflight.json', dict(uuid=cfg['gpu_uuid'], memory_used_mib=used, utilization=util))
        need(used <= 128 and util == 0, 'registered_GPU_not_idle')
        save(out / 'execution_snapshot.json', dict(registration_sha256=digest, argv=sys.argv, python=sys.version,
             executable=sys.executable, pid=os.getpid(), source_sha256=cfg['source_sha256'], input_sha256=cfg['input_sha256']))
        (out / 'registration_snapshot.json').write_bytes((ROOT / REG).read_bytes())
        for rel in cfg['source_sha256']:
            (out / ('source_' + Path(rel).name)).write_bytes((ROOT / rel).read_bytes())
        for rel in cfg['input_sha256']:
            (out / ('snapshot_input_' + Path(rel).name)).write_bytes((ROOT / rel).read_bytes())
        save(out / 'input_manifest.json', cfg['input_sha256'])
        for stage in ('worker', 'verifier'):
            remaining = cfg['bounds']['outer_seconds'] - (time.monotonic() - start)
            need(remaining > 0, 'outer_deadline')
            with (out / (stage + '.log')).open('w') as log:
                environment = dict(os.environ, TOKENIZERS_PARALLELISM='false', HF_HUB_OFFLINE='1', USE_TORCH='1', USE_TF='0', USE_FLAX='0',
                                   TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1',
                                   TMPDIR=str(out / 'runtime-tmp'),
                                   CUDA_VISIBLE_DEVICES=cfg['gpu_uuid'] if stage == 'worker' else '')
                p = subprocess.Popen([sys.executable, '-B', str(Path(__file__)), '--child', stage,
                    '--registration-sha256', digest], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True, env=environment)
                item = dict(stage=stage, pid=p.pid)
                record['children'].append(item)
                try:
                    item['exit_code'] = p.wait(timeout=min(remaining, cfg['bounds']['worker_seconds' if stage == 'worker' else 'verifier_seconds'] + 5))
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGTERM)
                    try:
                        p.wait(timeout=cfg['bounds']['term_grace_seconds'])
                    except subprocess.TimeoutExpired:
                        os.killpg(p.pid, signal.SIGKILL)
                        p.wait()
                    item.update(exit_code=p.returncode, timeout=True)
                    raise TimeoutError(stage + '_watchdog_timeout')
            need(item['exit_code'] == 0, stage + '_failed')
            if stage == 'worker':
                save(out / 'worker_manifest.json', {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()})
        record.update(status='complete', cases=2, new_GPU_runs=1, real_model_logits=14, engineering_logit_vectors=14)
    except BaseException as error:
        record.update(status='failed', error=type(error).__name__ + ':' + str(error))
        (out / 'launcher_traceback.txt').write_text(traceback.format_exc())
    finally:
        record['elapsed_seconds'] = time.monotonic() - start
        from checked_archive import finalize_archive
        closure = finalize_archive(out, record, cfg['bounds']['max_archive_files'], cfg['bounds']['max_archive_bytes'])
        record['status'] = closure['status']
        print(json.dumps(dict(record, archive_closure=closure)), flush=True)
    return 0 if record['status'] == 'complete' else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--child', choices=['worker', 'verifier'])
    args = parser.parse_args()
    cfg = registration(args.registration_sha256)
    if args.child:
        child(args.child, cfg)
        return 0
    need(args.execute, 'explicit_execution_required')
    return launch(cfg, args.registration_sha256)


if __name__ == '__main__':
    sys.exit(main())
