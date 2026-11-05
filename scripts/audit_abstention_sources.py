"""Fetch and parse pinned author sources only; never import or execute them."""
import argparse
import ast
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import time
import traceback
from urllib.request import Request, urlopen


REPO = 'mali-kh/compression-aware-abstention'
REVISION = '1426730aaf29edf48e91930d14d3b47b73f8e584'
FILES = ['README.md', 'LICENSE', 'docs/CLAIMS.md', 'pyproject.toml',
         'src/compressors/base.py', 'src/compressors/kvpress_wrapper.py',
         'src/compressors/kvzip.py', 'src/data/label_construction.py',
         'src/data/musique.py', 'src/eval/honest_accuracy.py',
         'scripts/eval_compressed_cache.py', 'scripts/block10_eval.py',
         'scripts/block10_pivot.py', 'scripts/verify_paper_claims.py']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def fetch(url, limit):
    with urlopen(Request(url, headers={'User-Agent': 'kv-pruning-read-only-source-audit'}), timeout=20) as response:
        data = response.read(limit+1)
    if len(data) > limit:
        raise ValueError('Source exceeded the frozen byte ceiling')
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--transport', choices=['raw', 'api'], default='raw')
    args = parser.parse_args()
    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (root / 'source_audit_abstention_sources.py').write_bytes(source)
    manifest = dict(status='running', start_unix=time.time(), args=vars(args),
                    source_sha256=sha(source), rows=0, new_model_outputs=0,
                    repo=REPO, revision=REVISION, selected_files=FILES,
                    scope='Read-only pinned text and AST; not a reproduction or model run')
    save(root / 'manifest.json', manifest)
    entries = []
    try:
        tree_url = f'https://api.github.com/repos/{REPO}/git/trees/{REVISION}?recursive=1'
        raw = fetch(tree_url, 3_000_000)
        (root / 'tree.json').write_bytes(raw)
        tree = json.loads(raw)
        assert not tree.get('truncated')
        blobs = {item['path']: item for item in tree['tree'] if item['type'] == 'blob'}
        assert all(name in blobs for name in FILES)
        def one(name):
            entry = dict(path=name, expected_git_blob=blobs[name]['sha'])
            try:
                if args.transport == 'raw':
                    url = f'https://raw.githubusercontent.com/{REPO}/{REVISION}/{name}'
                    data = fetch(url, 300_000)
                else:
                    url = f'https://api.github.com/repos/{REPO}/git/blobs/{blobs[name]["sha"]}'
                    payload = json.loads(fetch(url, 450_000))
                    assert payload['encoding'] == 'base64' and payload['sha'] == blobs[name]['sha']
                    data = base64.b64decode(payload['content'])
                    assert len(data) <= 300_000
                actual = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
                assert actual == blobs[name]['sha'], name
                destination = root / 'upstream' / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
                entry.update(status='fetched_verified', bytes=len(data), sha256=sha(data), url=url)
                if name.endswith('.py'):
                    parsed = ast.parse(data.decode('utf-8-sig'))
                    entry.update(python_ast='ok',
                                 top_level_definitions=[n.name for n in parsed.body
                                                        if isinstance(n, (ast.FunctionDef, ast.ClassDef))])
            except Exception as error:
                entry.update(status='failed', error_type=type(error).__name__, error_message=str(error))
            return entry
        with ThreadPoolExecutor(max_workers=4) as pool:
            pending = [pool.submit(one, name) for name in FILES]
            for future in as_completed(pending):
                entry = future.result()
                entries.append(entry)
                save(root / 'source_checks.json', sorted(entries, key=lambda x: x['path']))
                print(entry['status'], entry['path'], flush=True)
        assert len(entries) == len(FILES) and all(e['status'] == 'fetched_verified' for e in entries)
        manifest.update(status='complete', end_unix=time.time(), fetch_failures=0,
                        verified_files=len(entries), python_ast_checks=sum('python_ast' in e for e in entries),
                        artifact_sha256={str(p.relative_to(root)): sha(p.read_bytes())
                                         for p in root.rglob('*') if p.is_file() and p.name != 'manifest.json'})
    except Exception as error:
        manifest.update(status='failed', end_unix=time.time(),
                        fetch_failures=sum(e['status'] == 'failed' for e in entries),
                        error_type=type(error).__name__, error_message=str(error), traceback=traceback.format_exc())
        raise
    finally:
        save(root / 'manifest.json', manifest)
    print('COMPLETE', manifest['verified_files'], 'files', manifest['python_ast_checks'], 'AST checks')


if __name__ == '__main__':
    main()
