"""Download public model artifacts on server and verify the official HF commit.

Alternative transport endpoints are not trusted for version identity: every file
must match the official fixed-revision blob or LFS digest before local loading.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
import threading
import time
from urllib.request import Request,urlopen


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,indent=2),encoding='utf-8')


def verify(path,entry):
    if path.stat().st_size!=entry['size']:return None
    algorithm='sha256' if entry.get('lfs') else 'git_blob_sha1'
    digest=hashlib.sha256() if algorithm=='sha256' else hashlib.sha1()
    if algorithm=='git_blob_sha1':digest.update(b'blob '+str(entry['size']).encode()+b'\0')
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):digest.update(chunk)
    expected=entry['lfs']['sha256'] if entry.get('lfs') else entry['blobId']
    if digest.hexdigest()!=expected:return None
    return dict(path=entry['rfilename'],size=entry['size'],algorithm=algorithm,digest=digest.hexdigest(),
                mtime_ns=path.stat().st_mtime_ns,verified=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',required=True);p.add_argument('--model-dir',required=True);p.add_argument('--out',required=True);p.add_argument('--workers',type=int,default=5);a=p.parse_args()
    assert 1<=a.workers<=5
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False);dest=Path(a.model_dir).resolve();dest.mkdir(parents=True,exist_ok=True)
    spec_path=Path(a.spec);spec=json.loads(spec_path.read_text());assert spec['repo_id']=='Qwen/Qwen3-8B' and spec['gated'] is False
    assert spec['revision']=='b968826d9c46dd6066d109eabc6255188de91218'
    source=Path(__file__).read_bytes();(root/'source_fetch_pinned_model.py').write_bytes(source);(root/'official_spec.json').write_bytes(spec_path.read_bytes())
    manifest=dict(args=vars(a),status='downloading',rows=0,start_unix=time.time(),source_sha256={'fetch_pinned_model.py':sha(source)},
        official_spec_sha256=sha(spec_path.read_bytes()),model_repo=spec['repo_id'],revision=spec['revision'],model_dir=str(dest),
        transport_note='ModelScope public assets or hf-mirror fixed revision; version identity only from official HF commit digests')
    save(root/'manifest.json',manifest);lock=threading.Lock();checks=[]
    log=(root/'attempts.jsonl').open('w')
    def record(obj):
        with lock:log.write(json.dumps(obj)+'\n');log.flush()
    def fetch(entry):
        name=entry['rfilename'];path=dest/name;assert dest in path.resolve().parents and not path.is_symlink()
        if path.exists():
            check=verify(path,entry);assert check,'Existing full artifact differs from pinned commit: '+name
            record(dict(file=name,event='already_verified'));return check
        part=path.with_name(path.name+'.part');assert not part.is_symlink()
        urls=[f'https://www.modelscope.cn/models/{spec["repo_id"]}/resolve/master/{name}',
              f'https://hf-mirror.com/{spec["repo_id"]}/resolve/{spec["revision"]}/{name}']
        failures=[]
        for attempt in range(4):
            url=urls[attempt%2];offset=part.stat().st_size if part.exists() else 0
            if offset>entry['size']:raise RuntimeError('Partial file exceeds pinned size: '+name)
            if offset==entry['size']:
                check=verify(part,entry)
                if check:part.rename(path);check['mtime_ns']=path.stat().st_mtime_ns;return check
                raise RuntimeError('Completed partial artifact hash mismatch: '+name)
            headers={'User-Agent':'kv-pruning-pinned-model'}
            if offset:headers['Range']=f'bytes={offset}-'
            record(dict(file=name,event='attempt',attempt=attempt,offset=offset,transport='modelscope' if attempt%2==0 else 'hf-mirror'))
            try:
                with urlopen(Request(url,headers=headers),timeout=30) as response:
                    if offset and response.status==206:
                        assert response.headers.get('Content-Range','').startswith(f'bytes {offset}-')
                        mode='ab'
                    elif response.status==200:mode='wb';offset=0
                    else:raise RuntimeError('Unexpected HTTP status/range: '+str(response.status))
                    received=offset;last=time.monotonic()
                    with part.open(mode) as f:
                        while True:
                            chunk=response.read(4*1024*1024)
                            if not chunk:break
                            f.write(chunk);received+=len(chunk)
                            if received>entry['size']:raise RuntimeError('Response exceeds pinned size')
                            if time.monotonic()-last>=10:
                                print('DOWNLOAD',name,received,'/',entry['size'],flush=True);last=time.monotonic()
                assert received==entry['size'],'Incomplete file: '+name
                check=verify(part,entry);assert check,'Pinned digest mismatch: '+name
                part.rename(path);check['mtime_ns']=path.stat().st_mtime_ns
                record(dict(file=name,event='verified',**check));print('VERIFIED',name,entry['size'],flush=True);return check
            except Exception as error:
                failures.append(str(error));record(dict(file=name,event='failure',attempt=attempt,type=type(error).__name__,message=str(error)))
        raise RuntimeError('All transfers failed for '+name+': '+'; '.join(failures))
    try:
        # Keep small metadata ahead of weights so architecture/tokenizer can be
        # inspected while separate large files transfer concurrently.
        entries=sorted(spec['files'],key=lambda e:e['size'])
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            futures={pool.submit(fetch,e):e for e in entries}
            for future in as_completed(futures):
                checks.append(future.result());save(root/'artifact_checks.json',dict(repo=spec['repo_id'],revision=spec['revision'],model_dir=str(dest),complete=False,files=checks))
        assert len(checks)==len(entries)
        save(root/'artifact_checks.json',dict(repo=spec['repo_id'],revision=spec['revision'],model_dir=str(dest),complete=True,files=checks))
        manifest.update(status='complete',end_unix=time.time(),total_bytes=sum(e['size'] for e in entries),files=len(checks));save(root/'manifest.json',manifest)
        print('MODEL_COMPLETE',len(checks),manifest['total_bytes'],flush=True)
    except Exception as error:
        manifest.update(status='failed_download',end_unix=time.time(),error_type=type(error).__name__,error_message=str(error));save(root/'manifest.json',manifest);raise
    finally:log.close()


if __name__=='__main__':main()
