"""Fetch one approved public Mistral revision; all files require pinned hashes."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import threading
import time
from urllib.request import Request,urlopen

from fetch_pinned_model import verify,sha,save


REPO='mistralai/Mistral-7B-Instruct-v0.3'
REV='c170c708c41dac9275d15a8fff4eca08d52bab71'


def main():
    p=argparse.ArgumentParser()
    for name in ['spec','model-dir','metadata-from','out','preregistration']:p.add_argument('--'+name,required=True)
    p.add_argument('--workers',type=int,default=3);a=p.parse_args();assert 1<=a.workers<=3
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False)
    spec_path=Path(a.spec);spec=json.loads(spec_path.read_text())
    assert spec['repo_id']==REPO and spec['revision']==REV and spec['gated'] is False and spec['private'] is False
    assert len(spec['files'])==13 and len(spec['weight_files'])==3 and 'consolidated.safetensors' not in {e['rfilename'] for e in spec['files']}
    dest=Path(a.model_dir).resolve();dest.mkdir(parents=True,exist_ok=True);donor=Path(a.metadata_from).resolve()
    source={}
    for name in ['fetch_mistral_pinned.py','fetch_pinned_model.py']:
        data=Path(__file__).with_name(name).read_bytes();(root/('source_'+name)).write_bytes(data);source[name]=sha(data)
    (root/'official_spec.json').write_bytes(spec_path.read_bytes())
    (root/'preregistration.md').write_bytes(Path(a.preregistration).read_bytes())
    manifest=dict(args=vars(a),status='downloading',rows=0,start_unix=time.time(),source_sha256=source,
        official_spec_sha256=sha(spec_path.read_bytes()),preregistration_sha256=sha((root/'preregistration.md').read_bytes()),
        model_repo=REPO,revision=REV,model_dir=str(dest),
        transport_note='Public ModelScope asset or hf-mirror fixed revision; only official fixed HF hashes establish identity')
    save(root/'manifest.json',manifest);checks=[];lock=threading.Lock()
    def record(event):
        with lock:
            with (root/'attempts.jsonl').open('a') as f:f.write(json.dumps(dict(time_unix=time.time(),**event))+'\n')
    def fetch(entry):
        name=entry['rfilename'];assert '/' not in name
        path=dest/name;assert dest in path.resolve().parents and not path.is_symlink()
        if path.exists():
            check=verify(path,entry);assert check,'Existing file differs from fixed digest: '+name
            record(dict(file=name,event='already_verified'));return check
        if name in spec['metadata_files']:
            source_path=donor/name;assert source_path.is_file() and not source_path.is_symlink()
            assert verify(source_path,entry),'Reused metadata does not match fixed revision'
            path.write_bytes(source_path.read_bytes());check=verify(path,entry);assert check
            record(dict(file=name,event='copied_verified_metadata'));return check
        assert name in spec['weight_files']
        part=path.with_name(path.name+'.part');assert not part.is_symlink()
        urls=[f'https://www.modelscope.cn/models/{REPO}/resolve/master/{name}',
              f'https://hf-mirror.com/{REPO}/resolve/{REV}/{name}']
        failures=[]
        for attempt in range(4):
            offset=part.stat().st_size if part.exists() else 0
            assert offset<=entry['size'],'Oversized partial file'
            if offset==entry['size']:
                check=verify(part,entry);assert check,'Complete partial file has wrong pinned digest'
                part.rename(path);check['mtime_ns']=path.stat().st_mtime_ns;return check
            headers={'User-Agent':'kv-pruning-fixed-mistral'}
            if offset:headers['Range']=f'bytes={offset}-'
            url=urls[attempt%2];record(dict(file=name,event='attempt',attempt=attempt,url=url,offset=offset))
            try:
                with urlopen(Request(url,headers=headers),timeout=30) as response:
                    if response.status==206 and response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
                        mode='ab' if offset else 'wb'
                    elif response.status==200:mode='wb';offset=0
                    else:raise RuntimeError('Unexpected HTTP status/range')
                    received=offset;last=time.monotonic()
                    with part.open(mode) as f:
                        while True:
                            chunk=response.read(4*1024*1024)
                            if not chunk:break
                            f.write(chunk);received+=len(chunk)
                            assert received<=entry['size'],'Response exceeds fixed size'
                            if time.monotonic()-last>=15:
                                print('DOWNLOAD',name,received,'/',entry['size'],flush=True);last=time.monotonic()
                assert received==entry['size'],'Incomplete transfer'
                check=verify(part,entry);assert check,'Pinned file digest mismatch'
                part.rename(path);check['mtime_ns']=path.stat().st_mtime_ns
                record(dict(file=name,event='verified',digest=check['digest']));print('VERIFIED',name,flush=True);return check
            except Exception as error:
                failures.append(str(error));record(dict(file=name,event='failure',attempt=attempt,type=type(error).__name__,message=str(error)))
        raise RuntimeError('All transfer attempts failed for '+name+': '+'; '.join(failures))
    try:
        for entry in spec['files']:
            if entry['rfilename'] in spec['metadata_files']:checks.append(fetch(entry))
        save(root/'artifact_checks.json',dict(repo=REPO,revision=REV,model_dir=str(dest),complete=False,files=checks))
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            for future in as_completed([pool.submit(fetch,e) for e in spec['files'] if e['rfilename'] in spec['weight_files']]):
                checks.append(future.result());save(root/'artifact_checks.json',dict(repo=REPO,revision=REV,model_dir=str(dest),complete=False,files=checks))
        assert len(checks)==13
        save(root/'artifact_checks.json',dict(repo=REPO,revision=REV,model_dir=str(dest),complete=True,files=checks))
        manifest.update(status='complete',end_unix=time.time(),files=13,total_bytes=sum(e['size'] for e in spec['files']));save(root/'manifest.json',manifest)
        print('MODEL_COMPLETE',manifest['total_bytes'],flush=True)
    except Exception as error:
        manifest.update(status='failed_download',end_unix=time.time(),error_type=type(error).__name__,error_message=str(error));save(root/'manifest.json',manifest);raise


if __name__=='__main__':main()
