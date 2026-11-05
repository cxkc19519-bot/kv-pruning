"""Download only registered public payloads, with hash verification and wall limits."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import threading
import time
import traceback

from fetch_pinned_model import verify


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    p=argparse.ArgumentParser()
    for key in ['spec','dest','out']:p.add_argument('--'+key,required=True)
    args=p.parse_args();spec_raw=Path(args.spec).read_bytes();spec=json.loads(spec_raw)
    assert spec['download_enabled'] is True and spec['model_execution_enabled'] is False
    assert spec['gated'] is False and spec['private'] is False
    assert sum(f['size'] for f in spec['files'])<=spec['max_total_bytes']
    root=Path(args.out);root.mkdir(parents=True,exist_ok=False)
    dest=Path(args.dest).resolve();dest.mkdir(parents=True,exist_ok=True)
    source=Path(__file__).read_bytes();helper=Path(__file__).with_name('fetch_pinned_model.py').read_bytes()
    (root/'source_fetch.py').write_bytes(source);(root/'source_verify.py').write_bytes(helper);(root/'spec.json').write_bytes(spec_raw)
    m=dict(status='downloading',start_unix=time.time(),args=vars(args),rows=0,new_model_outputs=0,
           model_executed=False,source_sha256=sha(source),verify_source_sha256=sha(helper),
           spec_sha256=sha(spec_raw),files=[],repo_id=spec['repo_id'],revision=spec['revision'])
    save(root/'manifest.json',m);lock=threading.Lock()
    def log(obj):
        with lock:
            with (root/'attempts.jsonl').open('a') as f:f.write(json.dumps(dict(time_unix=time.time(),**obj))+'\n')
    def one(entry):
        name=entry['rfilename'];path=dest/name
        assert not Path(name).is_absolute() and dest in path.resolve().parents and not path.is_symlink()
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            check=verify(path,entry);assert check,'Existing artifact hash differs: '+name
            log(dict(file=name,event='already_verified'));return check
        donor=spec.get('donors',{}).get(name)
        if donor:
            source_path=Path(donor);assert source_path.is_file() and not source_path.is_symlink()
            assert verify(source_path,entry),'Donor hash differs: '+name
            shutil.copyfile(source_path,path)
            check=verify(path,entry);assert check
            log(dict(file=name,event='copied_verified_donor',donor=donor));return check
        part=path.with_name(path.name+'.part');assert not part.is_symlink()
        prefix='datasets/' if spec['repo_type']=='dataset' else ''
        url=f'https://hf-mirror.com/{prefix}{spec["repo_id"]}/resolve/{spec["revision"]}/{name}'
        for attempt in range(spec['max_attempts_per_file']):
            assert not part.exists() or part.stat().st_size<=entry['size']
            if part.exists() and part.stat().st_size==entry['size']:
                check=verify(part,entry);assert check,'Completed partial hash differs: '+name
                part.rename(path);check['mtime_ns']=path.stat().st_mtime_ns;return check
            log(dict(file=name,event='attempt',attempt=attempt,url=url,offset=part.stat().st_size if part.exists() else 0))
            cmd=['curl','--fail','--location','--silent','--show-error','--connect-timeout','20',
                 '--max-time',str(spec['per_attempt_wall_seconds']),'--continue-at','-',
                 '--output',str(part),url]
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=spec['per_attempt_wall_seconds']+15)
            log(dict(file=name,event='curl_exit',attempt=attempt,exit_code=result.returncode,stderr=result.stderr[-1500:]))
            if result.returncode==0:
                check=verify(part,entry);assert check,'Downloaded hash differs: '+name
                part.rename(path);check['mtime_ns']=path.stat().st_mtime_ns
                log(dict(file=name,event='verified',digest=check['digest']));print('VERIFIED',name,entry['size'],flush=True);return check
        raise RuntimeError('Registered attempts exhausted: '+name)
    try:
        with ThreadPoolExecutor(max_workers=spec['workers']) as pool:
            for future in as_completed([pool.submit(one,e) for e in sorted(spec['files'],key=lambda e:e['size'])]):
                check=future.result();m['files'].append(check);save(root/'manifest.json',m)
        m.update(status='complete',end_unix=time.time(),total_bytes=sum(e['size'] for e in spec['files']))
    except Exception as error:
        m.update(status='failed_download',end_unix=time.time(),error_type=type(error).__name__,error_message=str(error),traceback=traceback.format_exc());raise
    finally:save(root/'manifest.json',m)


if __name__=='__main__':main()
