"""Registered prospective typed-object3-schema/21-instance semantic correctness probe."""
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
    if cfg['mode']=='typed_object_semantic':
        for field in ['runtime_pin','extra_runtime_pin']:
            for name,h in json.loads((ROOT/cfg[field]).read_text()).items():assert sha(ROOT/name)==h,name
        proof=json.loads((ROOT/cfg['domain_proof']).read_text());assert proof['domain_factory_gate']
    return cfg,path


def worker(cfg,args):
    import struct
    import resource
    import tempfile
    out=ROOT/cfg['run']
    for key,value in cfg['environment'].items():
        os.environ[key]=str(out/value[4:]) if value.startswith('RUN/') else value
    (out/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(out/'tmp')
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    resource.setrlimit(resource.RLIMIT_FSIZE,(8388608,8388608));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    sys.path.insert(0,str(ROOT/'scripts'))
    events=(out/'events.jsonl').open('x');masks=(out/'masks.jsonl').open('x');instances=(out/'instances.jsonl').open('x')
    seq=0;owner=(os.getpid(),birth(os.getpid()));calls=0;deadline=None;context={'phase':'setup'}
    counters=dict(schema_specs=0,matcher_constructions=0,mask_positions=0,mask_api_calls=0,commit_calls=0)
    def emit(event,**fields):
        nonlocal seq
        seq+=1;row=dict(event=event,seq=seq,ns=time.monotonic_ns(),owner_pid=owner[0],
                       owner_starttime=owner[1],tid=threading.get_native_id())
        row.update(fields);events.write(json.dumps(row,sort_keys=True)+'\n');events.flush();return row
    def budget():
        limit=min(deadline,args.spawn_ns+30_000_000_000) if context['phase']=='setup' else deadline
        assert time.monotonic_ns()<limit,'shared_phase_deadline'
    def call(kind,fn):
        nonlocal calls
        budget();calls+=1;assert calls<=7516,'call_cap'
        if kind in ('x_mask','ll_mask','ll_bias'):
            counters['mask_api_calls']+=1;assert counters['mask_api_calls']<=1779,'mask_api_cap'
        if kind=='commit':
            counters['commit_calls']+=1;assert counters['commit_calls']<=1186,'commit_cap'
        emit('call_begin',call_id=calls,kind=kind,deadline_ns=deadline,context=dict(context))
        try:value=fn()
        except BaseException as exc:
            emit('call_end',call_id=calls,kind=kind,outcome='error',error=repr(exc),context=dict(context));raise
        emit('call_end',call_id=calls,kind=kind,outcome='success',context=dict(context))
        budget();return value
    status=dict(status='running',pid=owner[0],starttime=owner[1],rows=0,model_outputs=0,counters=counters,
                request_SLO_claim=False,readiness_live=False)
    stack=None;guard=None
    try:
        from import_boundary_v2 import ImportBoundary
        from utf8_domain import encode,vocabulary,SyntheticTokenizer
        guard=ImportBoundary(ROOT,out,json.loads((ROOT/cfg['boundary_pins']).read_text()),emit);guard.install()
        stack=(out/'stacks.txt').open('x');faulthandler.enable(file=stack,all_threads=True)
        emit('worker_bootstrap',parent_spawn_ns=args.spawn_ns,affinity=sorted(os.sched_getaffinity(0)),periodic_dump=False)
        emit('imports_begin');import torch;torch.set_num_threads(1);torch.set_num_interop_threads(1)
        import xgrammar as xgr
        import llguidance as llg
        assert not torch.cuda.is_initialized() and sys.byteorder=='little'
        ready=emit('library_import_ready',cuda_initialized=False);deadline=ready['ns']+5_000_000_000
        emit('adapter_setup_begin',deadline_ns=deadline)
        contract=json.loads((ROOT/cfg['domain']).read_text());vocab=vocabulary(contract);eos=133
        xi=call('x_tokenizer',lambda:xgr.TokenizerInfo(vocab,xgr.VocabType.RAW,vocab_size=134,stop_token_ids=[eos]))
        xm=call('x_metadata',lambda:dict(size=xi.vocab_size,stop=list(xi.stop_token_ids),ordinary=[bytes(t).hex() for t in xi.decoded_vocab[:133]]))
        assert xm==dict(size=134,stop=[133],ordinary=[v.hex() for v in vocab[:133]])
        adapter=SyntheticTokenizer(contract)
        li=call('ll_tokenizer',lambda:llg.LLTokenizer(llg.TokenizerWrapper(adapter),n_vocab=134,eos_token=133,slices=[]))
        lm=call('ll_metadata',lambda:dict(size=li.vocab_size,eos=li.eos_token,ordinary=li.decode_bytes(list(range(133))).hex()))
        assert lm==dict(size=134,eos=133,ordinary=b''.join(vocab[:133]).hex())
        compiler=call('x_compiler',lambda:xgr.GrammarCompiler(xi,max_threads=1,cache_enabled=False,cache_limit_bytes=8388608))
        mask_tensor=torch.full((1,5),-1,dtype=torch.int32,device='cpu')
        budget();emit('adapter_setup_complete',deadline_ns=deadline,x_metadata=xm,ll_metadata=lm)
        raw_groups=json.loads((ROOT/cfg['raw_groups']).read_text())
        plan=json.loads((ROOT/cfg['inventory']).read_text())
        assert len(raw_groups)==3 and len(plan)==42
        completed=0
        for backend in ['xgrammar','llguidance']:
            for group_index,raw_payload in enumerate(raw_groups):
                context={'phase':'schema_group','backend':backend,'group_index':group_index}
                submitted=emit('group_submitted',backend=backend,group_index=group_index,
                               payload_sha256=hashlib.sha256(raw_payload.encode('utf-8')).hexdigest())
                deadline=submitted['ns']+5_000_000_000
                emit('group_deadline',backend=backend,group_index=group_index,origin_ns=submitted['ns'],deadline_ns=deadline)
                group=json.loads(raw_payload);cid=group['case_id'];schema=group['schema']
                emit('group_payload_validated',backend=backend,group_index=group_index,case_id=cid,tests=len(group['tests']))
                counters['schema_specs']+=1
                group_error=None;grammar=None
                try:
                    grammar=call('schema_compile' if backend=='xgrammar' else 'schema_convert',
                        lambda:compiler.compile_json_schema(schema,strict_mode=False,any_whitespace=True)
                        if backend=='xgrammar' else llg.LLMatcher.grammar_from_json_schema(schema))
                except Exception as exc:group_error=type(exc).__name__+':'+str(exc)
                for test_index,test in enumerate(group['tests']):
                    context.update(test_index=test_index)
                    entry=dict(backend=backend,group_index=group_index,case_id=cid,test_index=test_index,
                               expected=test['valid'],status='running',accepted=None,steps=0)
                    if group_error is not None:
                        entry.update(status='schema_error',error=group_error)
                    else:
                        try:
                            budget()
                            text=json.dumps(test['data'],ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False)
                            token_ids=encode(text,contract)+[eos]
                            entry.update(serialized=text,tokens=token_ids)
                            counters['matcher_constructions']+=1;assert counters['matcher_constructions']<=42
                            matcher=call('matcher_init',lambda:xgr.GrammarMatcher(grammar,terminate_without_stop_token=False)
                                if backend=='xgrammar' else llg.LLMatcher(li,grammar,log_level=0))
                            if backend=='llguidance':
                                assert not call('ll_is_error',matcher.is_error),call('ll_error',matcher.get_error)
                                entry['warnings']=list(call('ll_warnings',matcher.get_grammar_warnings))
                            accepted=True
                            for position,token in enumerate(token_ids):
                                context['position']=position
                                counters['mask_positions']+=1;assert counters['mask_positions']<=1186
                                trace=dict(backend=backend,group_index=group_index,test_index=test_index,position=position,
                                           token=token,raw_hex=None,allowed=None,commit_result=None)
                                try:
                                    if backend=='xgrammar':
                                        mask_tensor.fill_(-1)
                                        applied=call('x_mask',lambda:matcher.fill_next_token_bitmask(mask_tensor))
                                        words=mask_tensor[0].tolist()
                                        raw=b''.join(struct.pack('<I',v&0xffffffff) for v in words)
                                        trace.update(words=words,need_apply=bool(applied),raw_hex=raw.hex(),mask_call_id=calls)
                                        assert len(raw)==20
                                    else:
                                        raw=call('ll_mask',matcher.compute_bitmask)
                                        trace.update(raw_hex=bytes(raw).hex(),mask_call_id=calls)
                                        bias=call('ll_bias',matcher.compute_logit_bias)
                                        trace.update(bias_hex=bytes(bias).hex(),bias_call_id=calls)
                                        assert isinstance(raw,bytes) and 17<=len(raw)<=64
                                        assert isinstance(bias,bytes) and 134<=len(bias)<=256
                                        assert all(v in (0,200) for v in bias[:134])
                                        assert all(bool(raw[t//8]&(1<<(t%8)))==(bias[t]==200) for t in range(134)),'mask_bias_disagreement'
                                        assert not call('ll_is_error',matcher.is_error),call('ll_error',matcher.get_error)
                                    allowed=bool(raw[token//8]&(1<<(token%8)));trace['allowed']=allowed
                                    if allowed:
                                        committed=call('commit',lambda:matcher.accept_token(token)
                                                       if backend=='xgrammar' else matcher.consume_token(token))
                                        trace.update(commit_result=bool(committed),commit_call_id=calls)
                                        assert committed,'mask_commit_disagreement'
                                        if backend=='llguidance':
                                            assert not call('ll_is_error',matcher.is_error),call('ll_error',matcher.get_error)
                                finally:
                                    if trace['raw_hex'] is not None:
                                        masks.write(json.dumps(trace,sort_keys=True)+'\n');masks.flush();entry['steps']+=1
                                if not allowed:accepted=False;break
                            if accepted:
                                if backend=='xgrammar':
                                    terminal=dict(stopped=bool(call('x_terminated',matcher.is_terminated)),
                                                  completed=bool(call('x_completed',matcher.is_completed)))
                                    assert terminal['stopped'],'eos_not_terminated'
                                else:
                                    terminal=dict(stopped=bool(call('ll_stopped',matcher.is_stopped)),
                                                  error=bool(call('ll_is_error',matcher.is_error)),
                                                  accepting=bool(call('ll_accepting',matcher.is_accepting)),
                                                  stop_reason=str(call('ll_stop_reason',matcher.stop_reason)))
                                    assert terminal['stopped'] and not terminal['error'],'eos_not_stopped'
                                entry['terminal']=terminal
                            entry.update(status='complete',accepted=accepted,matches_label=accepted==test['valid'])
                        except Exception as exc:
                            entry.update(status='error',error=type(exc).__name__+':'+str(exc),accepted=None)
                    instances.write(json.dumps(entry,sort_keys=True)+'\n');instances.flush();completed+=1
                budget()
                emit('group_complete',backend=backend,group_index=group_index,deadline_ns=deadline)
        assert completed==42 and counters['schema_specs']==6
        assert not torch.cuda.is_initialized()
        assert not any(guard.counts[k] for k in ('file_denied','process_denied','network_denied','forbidden_imports'))
        status.update(status='complete',rows_completed=completed,cuda_initialized=False)
    except BaseException as exc:
        status.update(status='failed',error=type(exc).__name__+':'+str(exc))
        (out/'worker-traceback.txt').write_text(traceback.format_exc())
    finally:
        if stack:faulthandler.disable();stack.close()
        if guard:status['boundary_counts']=dict(guard.counts)
        status['calls']=calls
        emit('worker_closed',status=status['status'],readiness_live=False)
        save(out/'worker-status.json',status);events.close();masks.close();instances.close()
    return 0 if status['status']=='complete' else 1


def launch(cfg,path,args,main_begin,checks_end):
    out=ROOT/cfg['run'];out.mkdir(exist_ok=False)
    summary=dict(status='running',mode=cfg['mode'],pid=os.getpid(),starttime=birth(os.getpid()),rows=0,model_outputs=0,
                 prechecks_ns=checks_end-main_begin,old_cold5_gate=False,old_257_semantic_gate=False)
    active=None;identity=None

    def kill(child,stamp):
        assert birth(child.pid)==stamp
        os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=1)
    try:
        save(out/'execution_snapshot.json',dict(registration_sha256=args.registration_sha256,argv=sys.argv,python=sys.version,
             launcher_begin_ns=main_begin,prechecks_end_ns=checks_end,source_sha256=cfg['source_sha256'],input_sha256=cfg['input_sha256']))
        (out/'registration_snapshot.json').write_bytes(path.read_bytes())
        for name in cfg['source_sha256']:(out/('source_'+Path(name).name)).write_bytes((ROOT/name).read_bytes())
        snapshot_map={}
        for index,name in enumerate(cfg['input_sha256']):
            saved_name='input_'+str(index).zfill(2)+'_'+Path(name).name
            (out/saved_name).write_bytes((ROOT/name).read_bytes())
            snapshot_map[name]=saved_name
        save(out/'snapshot-map.json',snapshot_map)
        python=ROOT/('.venv/bin/python' if cfg['mode']=='software' else '.venv-controller-history/bin/python')
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        if cfg['mode']=='typed_object_semantic':env['PYTHONPATH']=str(ROOT/'.venv-controller-history/lib/python3.11/site-packages')
        argv=[str(python),'-B','-S',str(Path(__file__).resolve()),'--worker','--registration',args.registration,'--registration-sha256',args.registration_sha256]
        with (out/'worker.log').open('x') as log,(out/'process-samples.jsonl').open('x') as samples:
            spawn=time.monotonic_ns();summary['spawn_ns']=spawn
            active=subprocess.Popen(argv+['--spawn-ns',str(spawn)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            identity=birth(active.pid);summary.update(worker_pid=active.pid,worker_starttime=identity)
            while active.poll() is None:
                now=time.monotonic_ns()
                samples.write(json.dumps(dict(ns=now,pid=active.pid,stat=Path(f'/proc/{active.pid}/stat').read_text()))+'\n')
                stack=out/'stacks.txt'
                active_deadline=None;startup_done=False
                event_path=out/'events.jsonl'
                if event_path.exists():
                    for line in event_path.read_bytes().splitlines():
                        try:row=json.loads(line)
                        except json.JSONDecodeError:continue
                        if row['event'] in ('adapter_setup_begin','group_deadline'):
                            assert row['owner_pid']==summary['worker_pid'] and row['owner_starttime']==identity
                            active_deadline=row['deadline_ns']
                        if row['event']=='adapter_setup_complete':startup_done=True;active_deadline=None
                        if row['event']=='group_complete':active_deadline=None
                phase_timeout=active_deadline is not None and now>=active_deadline
                startup_timeout=not startup_done and now-spawn>=30_000_000_000
                if startup_timeout or phase_timeout or now-spawn>=120_000_000_000 or (stack.exists() and stack.stat().st_size>524288):
                    summary.update(watchdog=True,watchdog_ns=now,startup_timeout=startup_timeout,phase_timeout=phase_timeout)
                    kill(active,identity);break
                time.sleep(.01)
            summary['worker_exit_code']=active.wait();active=None
        save(out/'worker-process.json',{k:v for k,v in summary.items() if k.startswith('worker') or k in ('spawn_ns','watchdog','watchdog_ns','startup_timeout','phase_timeout')})
        save(out/'worker_manifest.json',{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
        with (out/'verifier.log').open('x') as log:
            verifier=subprocess.Popen([sys.executable,'-I','-S','-B',str(ROOT/'scripts/verify_typed_object_probe.py'),str(out)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            summary.update(verifier_pid=verifier.pid,verifier_starttime=birth(verifier.pid))
            remaining=cfg['total_seconds']-(time.monotonic_ns()-main_begin)/1e9
            try:summary['verifier_exit_code']=verifier.wait(timeout=min(8,max(.01,remaining)))
            except subprocess.TimeoutExpired:
                assert birth(verifier.pid)==summary['verifier_starttime'];verifier.kill();verifier.wait(timeout=1);raise
        assert summary['verifier_exit_code']==0
        verification=json.loads((out/'independent_verification.json').read_text())
        summary.update(typed_object_semantic_gate=verification['typed_object_semantic_gate'],
                       semantic_summaries=verification['summaries'])
        assert summary['worker_exit_code']==0
        assert (time.monotonic_ns()-main_begin)/1e9<=cfg['total_seconds']
        summary['status']='complete'
    except BaseException as exc:
        if active and active.poll() is None:kill(active,identity)
        summary.update(status='failed',error=type(exc).__name__+':'+str(exc));(out/'launcher-traceback.txt').write_text(traceback.format_exc())
    finally:
        summary['launcher_seconds']=(time.monotonic_ns()-main_begin)/1e9
        sys.path.insert(0,str(ROOT/'scripts'))
        from checked_archive import finalize_archive
        closure=finalize_archive(out,summary,64,16777216)
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
