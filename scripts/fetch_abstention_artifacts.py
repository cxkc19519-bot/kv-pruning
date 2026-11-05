"""Read-only retrieval of four pinned public evaluation artifacts; no model code."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import time
import traceback
from urllib.request import Request, urlopen

REPO = 'mali-kh/compression-aware-abstention'
REVISION = '1426730aaf29edf48e91930d14d3b47b73f8e584'
FILES = {
    'artifacts/eval/block4_judge_log.jsonl': ('36e28965df78f5cf8fc781a6fdcf344d30a2e94d', 234941),
    'artifacts/eval/block4_sample.jsonl': ('1fc4a3b1203e7fbeef57a5d120ff4d79a9bfd259', 10865241),
    'artifacts/eval/v1_eval_base_compressed_kvzip.jsonl': ('c2a232bb29f308741036936f9c2524c7dfdf81d0', 242150),
    'artifacts/eval/v1_eval_mixture_cc_kvzip.jsonl': ('5944b7a4494d829a7163403fa3d97bd924ded578', 135304),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (root / 'fetch_source.py').write_bytes(source)
    manifest = dict(status='running', start_unix=time.time(), repo=REPO,
                    revision=REVISION, source_sha256=sha(source), new_model_outputs=0,
                    scope='Pinned released text only; neither upstream execution nor human reannotation', files=[])
    save(root / 'manifest.json', manifest)
    try:
        for name, (expected, size) in FILES.items():
            url = f'https://api.github.com/repos/{REPO}/git/blobs/{expected}'
            with urlopen(Request(url, headers={'User-Agent': 'kv-pruning-read-only-artifact-audit'}), timeout=30) as response:
                payload_raw = response.read(16_000_001)
            assert len(payload_raw) <= 16_000_000
            payload = json.loads(payload_raw)
            assert payload['encoding'] == 'base64' and payload['sha'] == expected
            raw = base64.b64decode(payload['content'])
            assert len(raw) == size
            assert hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest() == expected
            path = root / 'upstream' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
            keys = sorted(set().union(*(row.keys() for row in rows)))
            manifest['files'].append(dict(path=name, git_blob=expected, bytes=size,
                                          sha256=sha(raw), rows=len(rows), keys=keys))
            save(root / 'manifest.json', manifest)
            print(name, len(rows), keys, flush=True)
        manifest.update(status='complete', end_unix=time.time())
    except Exception as error:
        manifest.update(status='failed', end_unix=time.time(), error_type=type(error).__name__,
                        error_message=str(error), traceback=traceback.format_exc())
        raise
    finally:
        save(root / 'manifest.json', manifest)


if __name__ == '__main__':
    main()
