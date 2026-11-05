"""Separate registered software acceptance and unchanged-five-second import."""
import argparse
import faulthandler
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path,value):
    with path.open('x') as f:
        json.dump(value,f,sort_keys=True,indent=2);f.write('\n')


def birth(pid):
    text=Path(f'/proc/{pid}/stat').read_text()
    return int(text[text.rindex(')')+2:].split()[19])


def config(args):
    path=ROOT/args.registration
    assert path.parent==ROOT/'configs' and sha(path)==args.registration_sha256
    cfg=json.loads(path.read_text());assert cfg['execution_enabled']
    assert str(ROOT)=='/home/user/jhk/project/Directional Exploration/kv-pruning'
    for name,h in {**cfg['source_sha256'],**cfg['input_sha256']}.items():assert sha(ROOT/name)==h,name
    for name,h in json.loads((ROOT/cfg['runtime_pin']).read_text()).items():assert sha(ROOT/name)==h,name
    for name,h in json.loads((ROOT/cfg['extra_runtime_pin']).read_text()).items():assert sha(ROOT/name)==h,name
    return cfg,path


def worker(cfg):
    out=ROOT/cfg['run']
    for key,value in cfg['environment'].items():os.environ[key]=str(out/value[4:]) if value.startswith('RUN/') else value
    (out/'tmp').mkdir(exist_ok=True)
    import tempfile
    tempfile.tempdir=str(out/'tmp')
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    events=(out/'events.jsonl').open('x');seq=0;identity=birth(os.getpid())

    def emit(event,**fields):
        nonlocal seq
        seq+=1
        row=dict(event=event,seq=seq,ns=time.monotonic_ns(),owner_pid=os.getpid(),owner_starttime=identity,tid=threading.get_native_id())
        row.update(fields);events.write(json.dumps(row,sort_keys=True)+'\n');events.flush()
    pins=json.loads((ROOT/cfg['boundary_pins']).read_text())
    sys.path.insert(0,str(ROOT/'scripts'))
    status=dict(status='running',pid=os.getpid(),starttime=identity,mode=cfg['mode'])
    start=time.monotonic();stack=None
    try:
        if cfg['mode']=='software':
            from accept_import_boundary_v2 import run
            result=run(ROOT,out,pins,emit)
            assert result['passed']==23
        else:
            from import_boundary_v2 import ImportBoundary
            boundary=ImportBoundary(ROOT,out,pins,emit);boundary.install()
            stack=(out/'stacks.txt').open('x');faulthandler.dump_traceback_later(1,repeat=True,file=stack)
            emit('aggregate_import_begin',deadline_ns=5_000_000_000)
            emit('torch_import_begin');import torch;emit('torch_import_end')
            emit('torch_thread_settings_begin');torch.set_num_threads(1);torch.set_num_interop_threads(1);emit('torch_thread_settings_end')
            emit('xgrammar_import_begin');import xgrammar;emit('xgrammar_import_end')
            emit('aggregate_import_end',cuda_initialized=torch.cuda.is_initialized())
            assert not torch.cuda.is_initialized()
            status['boundary_counts']=boundary.counts
        status['status']='complete'
    except BaseException as exc:
        status.update(status='failed',error=type(exc).__name__+':'+str(exc));(out/'worker-traceback.txt').write_text(traceback.format_exc())
    finally:
        if stack:
            faulthandler.cancel_dump_traceback_later();stack.close()
        status['seconds']=time.monotonic()-start
        emit('worker_complete',status=status['status']);save(out/'worker-status.json',status);events.close()
    return 0 if status['status']=='complete' else 1


def launch(args,cfg,registration):
    out=ROOT/cfg['run'];out.mkdir(exist_ok=False)
    start=time.monotonic();active=None;identity=None
    summary=dict(status='running',mode=cfg['mode'],pid=os.getpid(),starttime=birth(os.getpid()),rows=0,model_outputs=0)

    def kill(child,stamp):
        assert birth(child.pid)==stamp
        os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=1)
    try:
        save(out/'execution_snapshot.json',dict(registration_sha256=args.registration_sha256,argv=sys.argv,
             python=sys.version,pid=os.getpid(),source_sha256=cfg['source_sha256'],input_sha256=cfg['input_sha256']))
        (out/'registration_snapshot.json').write_bytes(registration.read_bytes())
        for name in cfg['source_sha256']:(out/('source_'+Path(name).name)).write_bytes((ROOT/name).read_bytes())
        for name in cfg['input_sha256']:(out/('input_'+Path(name).name)).write_bytes((ROOT/name).read_bytes())
        python=ROOT/('.venv/bin/python' if cfg['mode']=='software' else '.venv-controller-history/bin/python')
        argv=[str(python),'-B','-S',str(Path(__file__).resolve()),'--worker','--registration',args.registration,'--registration-sha256',args.registration_sha256]
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        if cfg['mode']=='native':env['PYTHONPATH']=str(ROOT/'.venv-controller-history/lib/python3.11/site-packages')
        with (out/'worker.log').open('x') as log,(out/'process-samples.jsonl').open('x') as samples:
            active=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            identity=birth(active.pid);summary.update(worker_pid=active.pid,worker_starttime=identity)
            born=time.monotonic()
            while active.poll() is None:
                rows=[];path=out/'events.jsonl'
                if path.exists():
                    for line in path.read_text().splitlines():
                        try:rows.append(json.loads(line))
                        except json.JSONDecodeError:pass
                now=time.monotonic_ns()
                begins=[r for r in rows if r['event']=='aggregate_import_begin'];ends=[r for r in rows if r['event']=='aggregate_import_end']
                expired=bool(begins and not ends and now-begins[0]['ns']>=5_000_000_000)
                samples.write(json.dumps(dict(ns=now,pid=active.pid,stat=Path(f'/proc/{active.pid}/stat').read_text()))+'\n')
                stack=out/'stacks.txt'
                if expired or time.monotonic()-born>12 or (stack.exists() and stack.stat().st_size>524288):
                    summary.update(watchdog=True,watchdog_ns=now,aggregate_expired=expired);kill(active,identity);break
                time.sleep(.01)
            summary['worker_exit_code']=active.wait();active=None
        save(out/'worker-process.json',{k:v for k,v in summary.items() if k.startswith('worker') or k in ['watchdog','watchdog_ns','aggregate_expired']})
        save(out/'worker_manifest.json',{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
        with (out/'verifier.log').open('x') as log:
            verifier=subprocess.Popen([sys.executable,'-I','-S','-B',str(ROOT/'scripts/verify_import_boundary_v2.py'),str(out)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            summary.update(verifier_pid=verifier.pid,verifier_starttime=birth(verifier.pid))
            try:summary['verifier_exit_code']=verifier.wait(timeout=8)
            except subprocess.TimeoutExpired:
                assert birth(verifier.pid)==summary['verifier_starttime'];verifier.kill();verifier.wait(timeout=1);raise
        assert summary['verifier_exit_code']==0
        if cfg['mode']=='software':assert summary['worker_exit_code']==0
        assert time.monotonic()-start<=30
        summary['status']='complete'
    except BaseException as exc:
        if active and active.poll() is None:kill(active,identity)
        summary.update(status='failed',error=type(exc).__name__+':'+str(exc));(out/'launcher-traceback.txt').write_text(traceback.format_exc())
    finally:
        summary['seconds']=time.monotonic()-start
        sys.path.insert(0,str(ROOT/'scripts'))
        from checked_archive import finalize_archive
        closure=finalize_archive(out,summary,64,8388608)
        print(json.dumps(dict(summary,archive=closure)))
    return 0 if closure['status']=='complete' else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--registration',required=True);parser.add_argument('--registration-sha256',required=True)
    parser.add_argument('--worker',action='store_true');parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    cfg,registration=config(args)
    if args.worker:sys.exit(worker(cfg))
    assert args.execute
    sys.exit(launch(args,cfg,registration))
