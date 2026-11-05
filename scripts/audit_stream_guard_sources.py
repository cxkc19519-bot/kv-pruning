"""Fetch pinned guard sources and released data with whole-file wall timeouts."""
import argparse
import ast
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback


FETCH_PROGRAM = '''import sys,urllib.request
u=sys.argv[1];limit=int(sys.argv[2])
with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'kv-pruning-source-feasibility'}),timeout=20) as r:
 b=r.read(limit+1)
assert len(b)<=limit
sys.stdout.buffer.write(b)
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=False)
    source, raw_config = Path(__file__).read_bytes(), Path(args.config).read_bytes()
    config = json.loads(raw_config)
    assert config['execution_enabled'] is False and config['model_outputs_authorized_by_this_config'] == 0
    (root/'source.py').write_bytes(source)
    (root/'config.json').write_bytes(raw_config)
    manifest = dict(status='running', args=vars(args), start_unix=time.time(), rows=0,
                    new_model_outputs=0, source_sha256=sha(source), config_sha256=sha(raw_config),
                    model_executed=False, upstream_executed=False, files=[])
    save(root/'manifest.json', manifest)
    jobs = []
    for name, blob in config['github_files'].items():
        jobs.append(('github/'+name, f'https://api.github.com/repos/{config["github_repo"]}/git/blobs/{blob}', blob, None, True))
    for extra in config.get('github_extra_repos', []):
        for name, blob in extra['files'].items():
            jobs.append(('github_extra/'+extra['name']+'/'+name,
                         f'https://api.github.com/repos/{extra["repo"]}/git/blobs/{blob}', blob, None, True))
    for group in ['model', 'dataset']:
        kind = '' if group == 'model' else 'datasets/'
        repo, rev = config['hf_'+group], config['hf_'+group+'_revision']
        for name, (blob, size) in config['hf_'+group+'_files'].items():
            jobs.append((group+'/'+name, f'https://hf-mirror.com/{kind}{repo}/resolve/{rev}/{name}', blob, size, False))
    try:
        def one(job):
            name, url, blob, size, is_api = job
            row = dict(path=name, url=url, expected_git_blob=blob)
            try:
                raw = subprocess.run([sys.executable, '-c', FETCH_PROGRAM, url, str(config['network']['max_response_bytes'])],
                                     capture_output=True, check=True, timeout=config['network']['per_file_wall_seconds']).stdout
                if is_api:
                    payload = json.loads(raw)
                    assert payload['sha'] == blob and payload['encoding'] == 'base64'
                    raw = base64.b64decode(payload['content'])
                if size is not None:
                    assert len(raw) == size
                assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == blob
                path = root/'upstream'/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                row.update(status='verified', bytes=len(raw), sha256=sha(raw))
                if name.endswith('.py'):
                    ast.parse(raw.decode('utf-8-sig'))
                    row['ast_parse'] = True
                if name.endswith('.jsonl'):
                    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
                    row.update(released_rows=len(rows), fields=sorted(set().union(*(r.keys() for r in rows))))
            except Exception as error:
                row.update(status='failed', error_type=type(error).__name__, error_message=str(error))
                if isinstance(error, subprocess.CalledProcessError):
                    row['network_stderr'] = error.stderr.decode(errors='replace')[-2000:]
            return row
        with ThreadPoolExecutor(max_workers=4) as pool:
            for future in as_completed([pool.submit(one, job) for job in jobs]):
                row = future.result()
                manifest['files'].append(row)
                save(root/'manifest.json', manifest)
                print(row['status'], row['path'], flush=True)
        assert all(r['status'] == 'verified' for r in manifest['files'])
        manifest.update(status='complete', end_unix=time.time(), files_verified=len(jobs))
    except Exception as error:
        manifest.update(status='failed', end_unix=time.time(), error_type=type(error).__name__,
                        error_message=str(error), traceback=traceback.format_exc())
        raise
    finally:
        save(root/'manifest.json', manifest)


if __name__ == '__main__':
    main()
