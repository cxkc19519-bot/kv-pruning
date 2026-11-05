"""Read-only official GCS metadata; server-only bounded source audit."""
import sys
sys.dont_write_bytecode=True
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback
import urllib.request


def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')


def main():
    a=argparse.ArgumentParser();a.add_argument('--execute',action='store_true');args=a.parse_args()
    r=Path(__file__).resolve().parent.parent;assert args.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning'
    raw=(r/'configs/independent-source-discovery-v1.json').read_bytes();cfg=json.loads(raw)
    o=r/cfg['run'];assert o.resolve().parent==(r/'results').resolve();o.mkdir(exist_ok=False)
    start=time.monotonic();state=dict(status='running',pid=os.getpid(),main_outputs=0,engineering_outputs=0,requests=0)
    def timeout(*a):raise TimeoutError('30secondcap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(30)
    try:
        (o/'proposal_snapshot.json').write_bytes(raw);(o/'source.py').write_bytes(Path(__file__).read_bytes())
        state['requests']=1
        with urllib.request.urlopen(cfg['url'],timeout=15) as response:
            assert response.status==200 and response.geturl()==cfg['url']
            b=response.read(65537);assert len(b)<=65536
            (o/'metadata.json').write_bytes(b)
        j=json.loads(b)
        assert j['bucket']==cfg['expected_bucket'] and j['name']==cfg['expected_name']
        assert j['generation'].isdigit() and int(j['size'])>0 and j['md5Hash']
        state.update(status='complete',metadata_sha256=sha(b),generation=j['generation'],data_bytes=int(j['size']),content_md5_base64=j['md5Hash'],etag=j['etag'],network_requests=1,data_body_downloaded=False)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc));(o/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0);state['elapsed_seconds']=time.monotonic()-start;save(o/'summary.json',state)
        save(o/'manifest.json',{p.name:sha(p.read_bytes()) for p in o.iterdir() if p.is_file()});print(json.dumps(state),flush=True)
    return 0 if state['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
