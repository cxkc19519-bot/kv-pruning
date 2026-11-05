"""Fetch fixed public LFS text payloads; never execute the recorded agent actions."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

FETCH = '''import sys,urllib.request
with urllib.request.urlopen(urllib.request.Request(sys.argv[1],headers={'User-Agent':'kv-pruning-native-data-preflight'}),timeout=20) as r:b=r.read(int(sys.argv[2])+1)
assert len(b)<=int(sys.argv[2])
sys.stdout.buffer.write(b)
'''


def digest(b):
    return hashlib.sha256(b).hexdigest()


def save(p, o):
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding='utf-8')


def fetch(url, limit):
    return subprocess.run([sys.executable,'-c',FETCH,url,str(limit)],capture_output=True,check=True,timeout=90).stdout


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    root=Path(args.out);root.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).read_bytes();raw_config=Path(args.config).read_bytes();c=json.loads(raw_config)
    assert c['execution_enabled'] is False
    (root/'source.py').write_bytes(source);(root/'config.json').write_bytes(raw_config)
    m=dict(status='running',start_unix=time.time(),args=vars(args),rows=0,new_model_outputs=0,
           source_sha256=digest(source),config_sha256=digest(raw_config),files=[])
    save(root/'manifest.json',m)
    try:
        for name,(blob,expected,size) in c['files'].items():
            payload=json.loads(fetch(f'https://api.github.com/repos/{c["repo"]}/git/blobs/{blob}',10000))
            pointer=base64.b64decode(payload['content'])
            assert hashlib.sha1(b'blob '+str(len(pointer)).encode()+b'\0'+pointer).hexdigest()==blob
            text=pointer.decode()
            assert f'oid sha256:{expected}' in text and f'size {size}\n' in text
            pointer_path=root/'pointers'/name;pointer_path.parent.mkdir(parents=True,exist_ok=True);pointer_path.write_bytes(pointer)
            url=f'https://media.githubusercontent.com/media/{c["repo"]}/{c["revision"]}/{name}'
            raw=fetch(url,size)
            assert len(raw)==size and digest(raw)==expected
            path=root/'upstream'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            data=json.loads(raw);assert isinstance(data,list)
            m['files'].append(dict(path=name,sha256=expected,bytes=size,git_pointer_blob=blob,records=len(data),url=url))
            save(root/'manifest.json',m)
            print('VERIFIED',name,len(data),flush=True)
        m.update(status='complete',end_unix=time.time())
    except Exception as e:
        m.update(status='failed',end_unix=time.time(),error_type=type(e).__name__,error_message=str(e),traceback=traceback.format_exc())
        if isinstance(e,subprocess.CalledProcessError):m['network_stderr']=e.stderr.decode(errors='replace')[-2000:]
        raise
    finally:save(root/'manifest.json',m)


if __name__=='__main__':main()
