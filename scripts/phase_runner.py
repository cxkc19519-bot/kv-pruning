"""Registered phase-contract software acceptance and import-only startup."""
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
    with path.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')


def birth(pid):
    text=Path(f'/proc/{pid}/stat').read_text()
    return int(text[text.rindex(')')+2:].split()[19])


def config(args):
    path=ROOT/args.registration
    assert str(ROOT)=='/home/user/jhk/project/Directional Exploration/kv-pruning'
    assert path.parent==ROOT/'configs' and sha(path)==args.registration_sha256
    cfg=json.loads(path.read_text());assert cfg['execution_enabled']
    for name,h in {**cfg['source_sha256'],**cfg['input_sha256']}.items():assert sha(ROOT/name)==h,name
    if cfg['mode']=='startup_import_only':
        for field in ['runtime_pin','extra_runtime_pin']:
            for name,h in json.loads((ROOT/cfg[field]).read_text()).items():assert sha(ROOT/name)==h,name
        proof=json.loads((ROOT/cfg['phase_software_proof']).read_text());assert proof['phase_software_passed'] and proof['cases']==8
    return cfg,path


def worker(cfg,args):
    out=ROOT/cfg['run']
    for key,value in cfg['environment'].items():os.environ[key]=str(out/value[4:]) if value.startswith('RUN/') else value
    (out/'tmp').mkdir(exist_ok=True)
    import tempfile
    tempfile.tempdir=str(out/'tmp');os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    sys.path.insert(0,str(ROOT/'scripts'))
    events=(out/'events.jsonl').open('x');seq=0;owner=(os.getpid(),birth(os.getpid()))

    def emit(event,**fields):
        nonlocal seq
        seq+=1;row=dict(event=event,seq=seq,ns=time.monotonic_ns(),owner_pid=owner[0],owner_starttime=owner[1],tid=threading.get_native_id())
        row.update(fields);events.write(json.dumps(row,sort_keys=True)+'\n');events.flush()
    status=dict(status='running',pid=owner[0],starttime=owner[1],mode=cfg['mode'])
    begun=time.monotonic();phase=None;stack=None;guard=None
    try:
        if cfg['mode']=='software':
            counts=dict(import_denied=0,network_denied=0,process_denied=0,file_denied=0)
            def audit(event,data):
                category=None
                if event=='import' and data[0].split('.')[0] in ('torch','numpy','transformers','tokenizers','vllm','xgrammar','llguidance','tensorflow','jax'):category='import_denied'
                if event.startswith('socket.'):category='network_denied'
                if event in ('subprocess.Popen','os.system','os.posix_spawn','os.fork','os.forkpty'):category='process_denied'
                if event=='open' and isinstance(data[0],(str,bytes)):
                    p=Path(os.fsdecode(data[0])).resolve();mode,flags=data[1:3]
                    writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
                    if p.is_relative_to(ROOT/'models') or p.suffix in ('.safetensors','.bin','.pt','.pth') or writing and not p.is_relative_to(out):category='file_denied'
                if category:counts[category]+=1;emit('software_guard_denied',category=category);raise RuntimeError(category)
            sys.addaudithook(audit)
            from accept_phase_controller import run
            rows=run(out);assert len(rows)==8 and not any(counts.values())
            status.update(cases=8,guard=counts)
        else:
            from import_boundary_v2 import ImportBoundary
            from phase_controller import PhaseController
            guard=ImportBoundary(ROOT,out,json.loads((ROOT/cfg['boundary_pins']).read_text()),emit);guard.install()
            scope=dict(registration_sha256=args.registration_sha256,environment=cfg['environment'],source_sha256=cfg['source_sha256'],runtime_pin=cfg['input_sha256'][cfg['runtime_pin']])
            phase=PhaseController(scope,owner,args.spawn_ns,import_only=True,emit=lambda detail:emit('phase_event',detail=detail))
            stack=(out/'stacks.txt').open('x');faulthandler.dump_traceback_later(1,repeat=True,file=stack)
            phase.startup_stage('torch_import_begin');import torch;phase.startup_stage('torch_import_end')
            phase.startup_stage('thread_settings_begin');torch.set_num_threads(1);torch.set_num_interop_threads(1);phase.startup_stage('thread_settings_end')
            phase.startup_stage('xgrammar_import_begin');import xgrammar;phase.startup_stage('xgrammar_import_end')
            initialized=torch.cuda.is_initialized()
            assert not any(guard.counts[k] for k in ('file_denied','process_denied','forbidden_imports')),'unexpected_boundary_denial'
            phase.imports_ready(cuda_initialized=initialized,schema_work=0)
            status.update(library_import_ready_observed=True,backend_factory_ready=False,request_admission=False,
                          cuda_initialized=initialized,boundary_counts=dict(guard.counts))
        status['status']='complete'
    except BaseException as exc:
        status.update(status='failed',error=type(exc).__name__+':'+str(exc));(out/'worker-traceback.txt').write_text(traceback.format_exc())
    finally:
        if stack:faulthandler.cancel_dump_traceback_later();stack.close()
        if phase:
            phase.close('worker_exit');save(out/'phase-state.json',dict(trace=phase.trace,ledger=phase.ledger(),state=phase.state,scope_hash=phase.scope_hash,owner=list(owner)))
        status['worker_seconds']=time.monotonic()-begun
        emit('worker_complete',status=status['status']);save(out/'worker-status.json',status);events.close()
    return 0 if status['status']=='complete' else 1


def launch(cfg,path,args,main_begin,checks_end):
    out=ROOT/cfg['run'];out.mkdir(exist_ok=False)
    summary=dict(status='running',mode=cfg['mode'],pid=os.getpid(),starttime=birth(os.getpid()),rows=0,model_outputs=0,
                 prechecks_ns=checks_end-main_begin,old_cold5_gate=False,finite_semantic_gate=False)
    active=None;identity=None

    def kill(child,stamp):
        assert birth(child.pid)==stamp
        os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=1)
    try:
        save(out/'execution_snapshot.json',dict(registration_sha256=args.registration_sha256,argv=sys.argv,python=sys.version,
             launcher_begin_ns=main_begin,prechecks_end_ns=checks_end,source_sha256=cfg['source_sha256'],input_sha256=cfg['input_sha256']))
        (out/'registration_snapshot.json').write_bytes(path.read_bytes())
        for name in cfg['source_sha256']:(out/('source_'+Path(name).name)).write_bytes((ROOT/name).read_bytes())
        for name in cfg['input_sha256']:(out/('input_'+Path(name).name)).write_bytes((ROOT/name).read_bytes())
        python=ROOT/('.venv/bin/python' if cfg['mode']=='software' else '.venv-controller-history/bin/python')
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        if cfg['mode']=='startup_import_only':env['PYTHONPATH']=str(ROOT/'.venv-controller-history/lib/python3.11/site-packages')
        argv=[str(python),'-B','-S',str(Path(__file__).resolve()),'--worker','--registration',args.registration,'--registration-sha256',args.registration_sha256]
        with (out/'worker.log').open('x') as log,(out/'process-samples.jsonl').open('x') as samples:
            spawn=time.monotonic_ns();summary['spawn_ns']=spawn
            active=subprocess.Popen(argv+['--spawn-ns',str(spawn)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            identity=birth(active.pid);summary.update(worker_pid=active.pid,worker_starttime=identity)
            while active.poll() is None:
                now=time.monotonic_ns()
                samples.write(json.dumps(dict(ns=now,pid=active.pid,stat=Path(f'/proc/{active.pid}/stat').read_text()))+'\n')
                stack=out/'stacks.txt'
                if now-spawn>=30_000_000_000 or (stack.exists() and stack.stat().st_size>524288):
                    summary.update(watchdog=True,watchdog_ns=now,startup_timeout=now-spawn>=30_000_000_000);kill(active,identity);break
                time.sleep(.01)
            summary['worker_exit_code']=active.wait();active=None
        save(out/'worker-process.json',{k:v for k,v in summary.items() if k.startswith('worker') or k in ('spawn_ns','watchdog','watchdog_ns','startup_timeout')})
        save(out/'worker_manifest.json',{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
        with (out/'verifier.log').open('x') as log:
            verifier=subprocess.Popen([sys.executable,'-I','-S','-B',str(ROOT/'scripts/verify_phase_runner.py'),str(out)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            summary.update(verifier_pid=verifier.pid,verifier_starttime=birth(verifier.pid))
            remaining=cfg['total_seconds']-(time.monotonic_ns()-main_begin)/1e9
            try:summary['verifier_exit_code']=verifier.wait(timeout=min(8,max(.01,remaining)))
            except subprocess.TimeoutExpired:
                assert birth(verifier.pid)==summary['verifier_starttime'];verifier.kill();verifier.wait(timeout=1);raise
        assert summary['verifier_exit_code']==0
        if cfg['mode']=='software':assert summary['worker_exit_code']==0
        assert (time.monotonic_ns()-main_begin)/1e9<=cfg['total_seconds']
        summary['status']='complete'
    except BaseException as exc:
        if active and active.poll() is None:kill(active,identity)
        summary.update(status='failed',error=type(exc).__name__+':'+str(exc));(out/'launcher-traceback.txt').write_text(traceback.format_exc())
    finally:
        summary['launcher_seconds']=(time.monotonic_ns()-main_begin)/1e9
        sys.path.insert(0,str(ROOT/'scripts'))
        from checked_archive import finalize_archive
        closure=finalize_archive(out,summary,64,8388608)
        print(json.dumps(dict(summary,archive=closure)))
    return 0 if closure['status']=='complete' else 1


if __name__=='__main__':
    main_begin=time.monotonic_ns()
    parser=argparse.ArgumentParser();parser.add_argument('--registration',required=True);parser.add_argument('--registration-sha256',required=True)
    parser.add_argument('--worker',action='store_true');parser.add_argument('--execute',action='store_true');parser.add_argument('--spawn-ns',type=int)
    args=parser.parse_args();cfg,path=config(args);checks_end=time.monotonic_ns()
    if args.worker:sys.exit(worker(cfg,args))
    assert args.execute
    sys.exit(launch(cfg,path,args,main_begin,checks_end))
