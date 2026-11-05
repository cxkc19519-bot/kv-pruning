"""Finalize new archives without writing a false 'complete' before cap checks."""
import hashlib
import json
from pathlib import Path


def encoded(value):
    return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def finalize_archive(directory,record,max_files,max_bytes):
    directory=Path(directory).resolve()
    summary=directory/'launcher_summary.json';manifest=directory/'manifest.json'
    if summary.exists() or manifest.exists():
        raise ValueError('new_archive_only_no_overwrite')
    files=[p for p in directory.rglob('*') if p.is_file()]
    if any(not p.resolve().is_relative_to(directory) for p in files):
        raise ValueError('archive_file_outside_root')
    hashes={str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    base_bytes=sum(p.stat().st_size for p in files)
    state=dict(record)
    state['archive_files_including_closure']=len(files)+2
    state['archive_caps_checked_before_success']=True
    def prepare():
        body=encoded(state)
        mapping=dict(hashes)
        mapping['launcher_summary.json']=hashlib.sha256(body).hexdigest()
        mf=encoded(mapping)
        return body,mf,base_bytes+len(body)+len(mf)
    body,mf,total_bytes=prepare()
    if len(files)+2>max_files or total_bytes>max_bytes:
        state['status']='failed'
        state['archive_error']='file_count_cap' if len(files)+2>max_files else 'byte_count_cap'
        body,mf,total_bytes=prepare()
    with summary.open('xb') as f:f.write(body)
    with manifest.open('xb') as f:f.write(mf)
    return dict(status=state['status'],files=len(files)+2,bytes=total_bytes,
                archive_error=state.get('archive_error'),manifest_sha256=hashlib.sha256(mf).hexdigest())
