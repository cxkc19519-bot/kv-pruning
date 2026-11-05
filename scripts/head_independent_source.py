"""One unauthenticated HEAD of the original author's public bucket object."""
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
import urllib.error


def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    r=Path(__file__).resolve().parent.parent;assert a.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning'
    raw=(r/'configs/independent-source-public-head-v2.json').read_bytes();cfg=json.loads(raw);o=r/cfg['run'];o.mkdir(exist_ok=False)
    s=dict(status='running',pid=os.getpid(),requests=0,main_outputs=0,engineering_outputs=0);start=time.monotonic()
    def timeout(*a):raise TimeoutError('30secondcap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(30)
    try:
        (o/'proposal_snapshot.json').write_bytes(raw);(o/'source.py').write_bytes(Path(__file__).read_bytes())
        s['requests']=1
        with urllib.request.urlopen(urllib.request.Request(cfg['url'],method='HEAD'),timeout=15) as response:
            assert response.status==200 and response.geturl()==cfg['url'];headers={k.lower():v for k,v in response.headers.items()}
        save(o/'headers.json',headers)
        assert all(k in headers for k in cfg['required_headers'])
        hashes=dict(x.strip().split('=',1) for x in headers['x-goog-hash'].split(','));assert 'md5' in hashes
        s.update(status='complete',generation=headers['x-goog-generation'],data_bytes=int(headers['content-length']),content_md5_base64=hashes['md5'],etag=headers['etag'],data_body_downloaded=False)
    except BaseException as exc:
        s.update(status='failed',error=repr(exc));(o/'failure.txt').write_text(traceback.format_exc())
        if isinstance(exc,urllib.error.HTTPError):save(o/'error_headers.json',dict(exc.headers))
    finally:
        signal.alarm(0);s['elapsed_seconds']=time.monotonic()-start;save(o/'summary.json',s)
        save(o/'manifest.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in o.iterdir() if p.is_file()});print(json.dumps(s),flush=True)
    return 0 if s['status']=='complete' else 1
if __name__=='__main__':raise SystemExit(main())
