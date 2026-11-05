"""Registered finite UTF8 adapter and schema-free factory correctness probe."""
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
    if cfg['mode']=='utf8_domain_factory':
        for field in ['runtime_pin','extra_runtime_pin']:
            for name,h in json.loads((ROOT/cfg[field]).read_text()).items():assert sha(ROOT/name)==h,name
        proof=json.loads((ROOT/cfg['startup_proof']).read_text());assert proof['startup_import_gate'] and proof['library_import_ready_observed']
    return cfg,path


def worker(cfg,args):
    out=ROOT/cfg['run']
    for key,value in cfg['environment'].items():
        os.environ[key]=str(out/value[4:]) if value.startswith('RUN/') else value
    (out/'tmp').mkdir(exist_ok=True)
    import tempfile
    import resource
    tempfile.tempdir=str(out/'tmp')
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    sys.path.insert(0,str(ROOT/'scripts'))
    events=(out/'events.jsonl').open('x');seq=0;owner=(os.getpid(),birth(os.getpid()))
    def emit(event,**fields):
        nonlocal seq
        seq+=1
        row=dict(event=event,seq=seq,ns=time.monotonic_ns(),owner_pid=owner[0],
                 owner_starttime=owner[1],tid=threading.get_native_id())
        row.update(fields);events.write(json.dumps(row,sort_keys=True)+'\n');events.flush()
        return row
    status=dict(status='running',pid=owner[0],starttime=owner[1],mode=cfg['mode'],
                domain_verified=False,xgrammar_compiler_constructed=False,
                llguidance_tokenizer_constructed=False,backend_factory_ready=False,
                request_admission=False,finite_semantic_gate=False,live_ready=False)
    stack=None;guard=None;calls=0;setup_deadline=None
    try:
        from import_boundary_v2 import ImportBoundary
        guard=ImportBoundary(ROOT,out,json.loads((ROOT/cfg['boundary_pins']).read_text()),emit)
        guard.install()
        stack=(out/'stacks.txt').open('x');faulthandler.enable(file=stack,all_threads=True)
        emit('worker_bootstrap',parent_spawn_ns=args.spawn_ns,periodic_dump=False,
             affinity=sorted(os.sched_getaffinity(0)),fatal_enabled=faulthandler.is_enabled())
        emit('torch_import_begin');import torch;emit('torch_import_end')
        torch.set_num_threads(1);torch.set_num_interop_threads(1)
        emit('xgrammar_import_begin');import xgrammar as xgr;emit('xgrammar_import_end')
        emit('llguidance_import_begin');import llguidance as llg;emit('llguidance_import_end')
        assert not torch.cuda.is_initialized()
        assert time.monotonic_ns()-args.spawn_ns<30_000_000_000
        ready=emit('library_import_ready',cuda_initialized=False)
        setup_deadline=ready['ns']+5_000_000_000
        emit('adapter_setup_begin',origin_ns=ready['ns'],deadline_ns=setup_deadline)
        contract=json.loads((ROOT/cfg['domain']).read_text())
        from utf8_domain import encode,vocabulary,SyntheticTokenizer
        vocab=vocabulary(contract);size=contract['vocab_size'];eos=contract['eos_id']
        def budget():
            assert time.monotonic_ns()<min(setup_deadline,args.spawn_ns+30_000_000_000),'aggregate_setup_deadline'
        def call(kind,fn):
            nonlocal calls
            budget();calls+=1;assert calls<=600
            emit('native_call_begin',call_id=calls,kind=kind,deadline_ns=setup_deadline)
            try:value=fn()
            except BaseException as exc:
                emit('native_call_end',call_id=calls,kind=kind,outcome='error',error=repr(exc))
                raise
            emit('native_call_end',call_id=calls,kind=kind,outcome='success')
            budget()
            return value
        xi=call('xgrammar_tokenizer_construct',lambda:xgr.TokenizerInfo(vocab,xgr.VocabType.RAW,
                  vocab_size=size,stop_token_ids=[eos]))
        xmeta=call('xgrammar_tokenizer_metadata',lambda:dict(vocab_size=xi.vocab_size,
                  stop_ids=list(xi.stop_token_ids),special_ids=list(xi.special_token_ids),
                  decoded_hex=[bytes(v).hex() for v in xi.decoded_vocab]))
        save(out/'xgrammar-metadata.json',xmeta)
        assert xmeta['vocab_size']==size and xmeta['stop_ids']==[eos]
        assert [bytes.fromhex(h) for h in xmeta['decoded_hex'][:eos]]==vocab[:eos]
        assert set(xmeta['special_ids'])|set(xmeta['stop_ids'])=={eos}
        adapter=SyntheticTokenizer(contract)
        wrapper=call('llguidance_wrapper_construct',lambda:llg.TokenizerWrapper(adapter))
        li=call('llguidance_tokenizer_construct',lambda:llg.LLTokenizer(wrapper,n_vocab=size,eos_token=eos,slices=[]))
        lm=call('llguidance_tokenizer_metadata',lambda:dict(vocab_size=li.vocab_size,eos_id=li.eos_token,eos_ids=list(li.eos_tokens)))
        save(out/'llguidance-metadata.json',lm)
        assert lm['vocab_size']==size and lm['eos_id']==eos and lm['eos_ids']==[eos]
        singles=[]
        for token in range(size):
            special=call('llguidance_special:'+str(token),lambda:li.is_special_token(token))
            emit('special_evidence',token=token,special=bool(special))
            assert bool(special)==(token==eos)
            raw=call('llguidance_decode:'+str(token),lambda:li.decode_bytes([token]))
            emit('decode_evidence',token=token,return_type=type(raw).__name__,raw_hex=raw.hex() if isinstance(raw,bytes) else None)
            assert isinstance(raw,bytes)
            if token!=eos:assert raw==vocab[token]
            ids=None
            if token!=eos:
                ids=list(call('llguidance_encode:'+str(token),lambda:li.tokenize_bytes(vocab[token],parse_special=False)))
                emit('encode_evidence',token=token,ids=ids)
                assert ids==[token]
            singles.append(dict(token=token,special=bool(special),decoded_hex=raw.hex(),encoded_ids=ids))
        allbytes=b''.join(vocab[:eos])
        allids=list(call('llguidance_encode_all',lambda:li.tokenize_bytes(allbytes,parse_special=False)))
        allraw=call('llguidance_decode_all',lambda:li.decode_bytes(list(range(eos))))
        assert allids==list(range(eos)) and allraw==allbytes
        positives=[]
        for index,text in enumerate(contract['positive_probes']):
            expected=encode(text,contract)
            ids=list(call('llguidance_probe_encode:'+str(index),lambda:li.tokenize_bytes(text.encode('utf-8'),parse_special=False)))
            raw=call('llguidance_probe_decode:'+str(index),lambda:li.decode_bytes(ids))
            emit('positive_evidence',index=index,ids=ids,decoded_hex=raw.hex())
            assert ids==expected and raw==text.encode('utf-8') and eos not in ids
            positives.append(dict(index=index,utf8_hex=text.encode('utf-8').hex(),ids=ids,decoded_hex=raw.hex()))
        negatives=[]
        for item in contract['negative_probes']:
            before=calls;payload=bytes.fromhex(item['bytes_hex']) if 'bytes_hex' in item else item['text']
            try:
                encode(payload,contract)
            except (ValueError,UnicodeError,TypeError) as exc:
                negatives.append(dict(id=item['id'],rejected=True,error=type(exc).__name__,
                                      native_calls_before=before,native_calls_after=calls))
            else:raise AssertionError('negative_input_not_rejected:'+item['id'])
        selection=json.loads((ROOT/cfg['selection']).read_text())
        coverage=[]
        for case in selection['cases']:
            for index,test in enumerate(case['tests']):
                text=json.dumps(test['data'],ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False)
                ids=encode(text,contract)
                assert b''.join(vocab[t] for t in ids)==text.encode('ascii')
                coverage.append(dict(case_id=case['case_id'],index=index,utf8_hex=text.encode('ascii').hex(),ids=ids))
        assert len(coverage)==45
        compiler=call('xgrammar_compiler_construct',lambda:xgr.GrammarCompiler(xi,max_threads=1,
                      cache_enabled=False,cache_limit_bytes=8388608))
        assert isinstance(compiler,xgr.GrammarCompiler)
        assert not torch.cuda.is_initialized()
        assert not any(guard.counts[k] for k in ('file_denied','process_denied','forbidden_imports','network_denied'))
        evidence=dict(contract_sha256=sha(ROOT/cfg['domain']),owner=list(owner),xgrammar=xmeta,llguidance=lm,
                      singles=singles,all_hex=allraw.hex(),all_ids=allids,positives=positives,negatives=negatives,
                      selection_representability=coverage,selection_semantics_executed=False,
                      adapter_callback_calls=adapter.callback_calls,native_calls=calls,
                      xgrammar_factory=dict(constructed=True,max_threads=1,cache_enabled=False,cache_limit_bytes=8388608),
                      llguidance_factory=dict(tokenizer_constructed=True,schema_factory_constructed=False,
                                             deferred_work=['grammar_from_json_schema','LLMatcher','first_mask']))
        save(out/'domain-evidence.json',evidence)
        budget()
        completed=emit('adapter_setup_complete',deadline_ns=setup_deadline,domain_verified=True,
                       xgrammar_compiler_constructed=True,llguidance_tokenizer_constructed=True)
        status.update(status='complete',domain_verified=True,xgrammar_compiler_constructed=True,
                      llguidance_tokenizer_constructed=True,cuda_initialized=False,
                      startup_ns=ready['ns']-args.spawn_ns,adapter_setup_ns=completed['ns']-ready['ns'])
    except BaseException as exc:
        status.update(status='failed',error=type(exc).__name__+':'+str(exc))
        (out/'worker-traceback.txt').write_text(traceback.format_exc())
    finally:
        if stack:faulthandler.disable();stack.close()
        if guard:status['boundary_counts']=dict(guard.counts)
        status['native_calls']=calls
        emit('worker_closed',status=status['status'],readiness_live=False)
        save(out/'worker-status.json',status);events.close()
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
        snapshot_map={}
        for index,name in enumerate(cfg['input_sha256']):
            saved_name='input_'+str(index).zfill(2)+'_'+Path(name).name
            (out/saved_name).write_bytes((ROOT/name).read_bytes())
            snapshot_map[name]=saved_name
        save(out/'snapshot-map.json',snapshot_map)
        python=ROOT/('.venv/bin/python' if cfg['mode']=='software' else '.venv-controller-history/bin/python')
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        if cfg['mode']=='utf8_domain_factory':env['PYTHONPATH']=str(ROOT/'.venv-controller-history/lib/python3.11/site-packages')
        argv=[str(python),'-B','-S',str(Path(__file__).resolve()),'--worker','--registration',args.registration,'--registration-sha256',args.registration_sha256]
        with (out/'worker.log').open('x') as log,(out/'process-samples.jsonl').open('x') as samples:
            spawn=time.monotonic_ns();summary['spawn_ns']=spawn
            active=subprocess.Popen(argv+['--spawn-ns',str(spawn)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            identity=birth(active.pid);summary.update(worker_pid=active.pid,worker_starttime=identity)
            while active.poll() is None:
                now=time.monotonic_ns()
                samples.write(json.dumps(dict(ns=now,pid=active.pid,stat=Path(f'/proc/{active.pid}/stat').read_text()))+'\n')
                stack=out/'stacks.txt'
                adapter_expired=False
                event_path=out/'events.jsonl'
                if event_path.exists():
                    for line in event_path.read_bytes().splitlines():
                        try:row=json.loads(line)
                        except json.JSONDecodeError:continue
                        if row['event']=='adapter_setup_begin':
                            assert row['owner_pid']==summary['worker_pid'] and row['owner_starttime']==identity
                            adapter_expired=now>=row['deadline_ns']
                if now-spawn>=30_000_000_000 or adapter_expired or (stack.exists() and stack.stat().st_size>524288):
                    summary.update(watchdog=True,watchdog_ns=now,startup_timeout=now-spawn>=30_000_000_000,adapter_timeout=adapter_expired);kill(active,identity);break
                time.sleep(.01)
            summary['worker_exit_code']=active.wait();active=None
        save(out/'worker-process.json',{k:v for k,v in summary.items() if k.startswith('worker') or k in ('spawn_ns','watchdog','watchdog_ns','startup_timeout','adapter_timeout')})
        save(out/'worker_manifest.json',{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
        with (out/'verifier.log').open('x') as log:
            verifier=subprocess.Popen([sys.executable,'-I','-S','-B',str(ROOT/'scripts/verify_utf8_domain_factory.py'),str(out)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            summary.update(verifier_pid=verifier.pid,verifier_starttime=birth(verifier.pid))
            remaining=cfg['total_seconds']-(time.monotonic_ns()-main_begin)/1e9
            try:summary['verifier_exit_code']=verifier.wait(timeout=min(8,max(.01,remaining)))
            except subprocess.TimeoutExpired:
                assert birth(verifier.pid)==summary['verifier_starttime'];verifier.kill();verifier.wait(timeout=1);raise
        assert summary['verifier_exit_code']==0
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
