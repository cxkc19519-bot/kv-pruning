"""Server-only, isolated vLLM dependency resolution and hash-locked install.

No model loads or GPU kernels. Every subprocess is logged and time bounded.
Run once per new result directory; failed attempts are never overwritten.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-dir', required=True)
    ap.add_argument('--install', action='store_true')
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    assert sys.platform == 'linux', 'Experiments belong on the Linux server'
    run = Path(args.run_dir).resolve()
    assert run.parent == root / 'results'
    run.mkdir(exist_ok=False)
    env_dir = root / '.venv-controller-history'
    assert not env_dir.exists(), 'Never overwrite an existing environment'
    started = time.monotonic()
    state = {'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
             'pid': os.getpid(), 'status': 'running', 'model_outputs': 0,
             'gpu_kernels_launched': False, 'environment': str(env_dir),
             'commands': [], 'install_requested': args.install}
    (run / 'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    env = dict(os.environ)
    for k in list(env):
        if k.startswith('PIP_'):
            del env[k]
    env.update(PIP_CONFIG_FILE='/dev/null', PIP_NO_INPUT='1',
               PIP_CACHE_DIR=str(run / 'pip-cache'),
               CUDA_VISIBLE_DEVICES='', VLLM_NO_USAGE_STATS='1',
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')

    def save():
        (run / 'summary.json').write_text(json.dumps(state, indent=2) + '\n')

    def command(label, argv, timeout):
        remaining = 1800 - (time.monotonic() - started)
        assert remaining > 0, 'Total bootstrap bound exceeded'
        entry = {'label': label, 'argv': list(map(str, argv))}
        state['commands'].append(entry)
        save()
        with (run / (label + '.log')).open('wb') as log:
            try:
                cp = subprocess.run(argv, cwd=root, env=env, stdout=log,
                                    stderr=subprocess.STDOUT,
                                    timeout=min(timeout, remaining))
                entry['returncode'] = cp.returncode
            except subprocess.TimeoutExpired:
                entry['timed_out'] = True
                save()
                raise
        save()
        assert cp.returncode == 0, label + ' failed; see preserved log'

    try:
        assert shutil.disk_usage(root).free > 60 * 1024**3
        command('create_env', [sys.executable, '-m', 'venv', str(env_dir)], 90)
        py = str(env_dir / 'bin/python')
        command('python_version', [py, '-VV'], 20)
        pip = [py, '-m', 'pip', '--disable-pip-version-check']
        common = ['--index-url', 'https://pypi.org/simple',
                  '--only-binary=:all:', '--timeout', '25', '--retries', '0']
        command('resolve', pip + ['install', '--dry-run', '--ignore-installed',
                '--report', str(run / 'resolution.json')] + common +
                ['vllm==0.32.0'], 600)
        report = json.loads((run / 'resolution.json').read_text())
        locked = []
        seen = set()
        for item in report['install']:
            meta = item['metadata']
            name, version = meta['name'], meta['version']
            assert name.lower() not in seen
            seen.add(name.lower())
            info = item['download_info']
            assert info['url'].startswith('https://files.pythonhosted.org/')
            assert info['url'].endswith('.whl'), 'No source builds'
            sha = info['archive_info']['hashes']['sha256']
            assert len(sha) == 64
            if name.lower() == 'vllm':
                assert version == '0.32.0'
                assert sha == '5e2ecdc5b0baf72921c288486417ca82778456a448e4fe60b62ee43c0dfc8611'
            locked.append(f'{name}=={version} --hash=sha256:{sha}')
        assert 'vllm' in seen and 'torch' in seen
        lock = run / 'requirements.lock'
        lock.write_text('\n'.join(sorted(locked, key=str.lower)) + '\n')
        state['resolved_packages'] = len(locked)
        state['lock_sha256'] = hashlib.sha256(lock.read_bytes()).hexdigest()
        state['status'] = 'resolved_not_installed'
        save()
        if args.install:
            command('install', pip + ['install', '--require-hashes', '-r', str(lock)]
                    + common, 1100)
            command('pip_check', pip + ['check'], 45)
            command('freeze', pip + ['freeze', '--all'], 30)
            # Import only: CUDA hidden; no is_available, kernel, model or worker.
            command('imports', [py, '-c',
                'import torch,transformers,vllm; '
                'print("torch",torch.__version__,"cuda",torch.version.cuda); '
                'print("transformers",transformers.__version__); '
                'print("vllm",vllm.__version__)'], 90)
            state['status'] = 'installed_imports_passed_gpu_unverified'
    except Exception as exc:
        state['status'] = 'failed'
        state['error'] = repr(exc)
        (run / 'failure.txt').write_text(traceback.format_exc())
    finally:
        state['elapsed_seconds'] = time.monotonic() - started
        state['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        save()
        files = [p for p in run.iterdir() if p.is_file()]
        (run / 'manifest.json').write_text(json.dumps({p.name: {
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
            'bytes': p.stat().st_size} for p in files}, indent=2) + '\n')
        print(json.dumps(state, indent=2), flush=True)
    return 0 if state['status'] != 'failed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
