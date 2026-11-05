"""Recompute finite-domain evidence with stdlib only; no adapter/backend import."""
import hashlib
import json
from pathlib import Path
import sys


def need(value, reason):
    if not value:
        raise AssertionError(reason)


def verify(out):
    for name, digest in json.loads((out/'worker_manifest.json').read_text()).items():
        p=(out/name).resolve()
        need(p.is_relative_to(out) and hashlib.sha256(p.read_bytes()).hexdigest()==digest,'manifest:'+name)
    cfg=json.loads((out/'registration_snapshot.json').read_text())
    snapshots=json.loads((out/'snapshot-map.json').read_text())
    need(set(snapshots)==set(cfg['input_sha256']) and len(set(snapshots.values()))==len(snapshots),'unique_input_snapshots')
    for name,saved_name in snapshots.items():
        need(hashlib.sha256((out/saved_name).read_bytes()).hexdigest()==cfg['input_sha256'][name],'input_binding:'+name)
    contract=json.loads((out/snapshots[cfg['domain']]).read_text())
    points=list(range(128))+[162,233,8364,20013,128512]
    need(contract['codepoints']==points and contract['eos_id']==133 and contract['vocab_size']==134,'fixed_domain')
    vocab=[chr(c).encode('utf-8') for c in points]
    index={c:i for i,c in enumerate(points)}
    def tokens(text):
        return [index[ord(c)] for c in text]
    process=json.loads((out/'worker-process.json').read_text())
    rows=[json.loads(line) for line in (out/'events.jsonl').read_text().splitlines()]
    owner=[process['worker_pid'],process['worker_starttime']]
    for i,row in enumerate(rows):
        need(row['seq']==i+1 and [row['owner_pid'],row['owner_starttime']]==owner,'owner_sequence')
        need(row['ns']>=process['spawn_ns'],'event_before_spawn')
        if i:need(row['ns']>=rows[i-1]['ns'],'event_clock')
    report=dict(status='complete',domain_factory_gate=False,finite_semantic_gate=False,
                old_cold5_gate=False,old_ff_identity_gate=False,request_admission=False,readiness_live=False)
    status_path=out/'worker-status.json'
    status=json.loads(status_path.read_text()) if status_path.exists() else None
    if not status or status['status']!='complete':
        need(process['worker_exit_code']!=0,'missing_success_evidence')
        report.update(failure_or_censoring=True,worker_error=status.get('error') if status else None)
    else:
        need(process['worker_exit_code']==0,'worker_exit')
        by_event={}
        for row in rows:by_event.setdefault(row['event'],[]).append(row)
        def one(name):
            found=by_event.get(name,[]);need(len(found)==1,'checkpoint:'+name);return found[0]
        boot=one('worker_bootstrap')
        need(boot['parent_spawn_ns']==process['spawn_ns'] and not boot['periodic_dump'] and boot['fatal_enabled'],'bootstrap')
        need(len(boot['affinity'])<=2,'cpu_affinity')
        checkpoint_names=['torch_import_begin','torch_import_end','xgrammar_import_begin','xgrammar_import_end',
                          'llguidance_import_begin','llguidance_import_end','library_import_ready','adapter_setup_begin',
                          'adapter_setup_complete','worker_closed']
        times=[one(name)['ns'] for name in checkpoint_names]
        need(times==sorted(times),'stage_order')
        ready=one('library_import_ready');begin=one('adapter_setup_begin');end=one('adapter_setup_complete')
        need(not ready['cuda_initialized'] and ready['ns']-process['spawn_ns']<30_000_000_000,'imports30')
        need(begin['origin_ns']==ready['ns'] and begin['deadline_ns']==ready['ns']+5_000_000_000,'one_setup_origin5')
        need(end['deadline_ns']==begin['deadline_ns'] and end['ns']<begin['deadline_ns'],'setup5')
        need(end['ns']-process['spawn_ns']<30_000_000_000,'aggregate30')
        starts=by_event.get('native_call_begin',[]);ends=by_event.get('native_call_end',[])
        need(len(starts)==len(ends)==425,'exact425_native_calls')
        for i,(a,b) in enumerate(zip(starts,ends)):
            need(a['call_id']==b['call_id']==i+1 and a['kind']==b['kind'] and b['outcome']=='success','call_pair')
            need(a['deadline_ns']==begin['deadline_ns'] and begin['ns']<=a['ns']<=b['ns']<end['ns'],'call_deadline')
            if i:need(a['ns']>=ends[i-1]['ns'],'serial_calls')
        evidence=json.loads((out/'domain-evidence.json').read_text())
        need(evidence['owner']==owner and evidence['contract_sha256']==cfg['input_sha256'][cfg['domain']],'evidence_scope')
        xm=evidence['xgrammar'];lm=evidence['llguidance']
        need(xm['vocab_size']==134 and xm['stop_ids']==[133],'x_vocab_eos')
        need(len(xm['decoded_hex'])==134 and [bytes.fromhex(h) for h in xm['decoded_hex'][:133]]==vocab,'x_raw_vocab')
        need(set(xm['special_ids'])|set(xm['stop_ids'])=={133},'x_no_ordinary_special')
        need(lm==dict(vocab_size=134,eos_id=133,eos_ids=[133]),'ll_vocab_eos')
        single=evidence['singles'];need(len(single)==134,'single_count')
        for i,row in enumerate(single):
            need(row['token']==i and row['special']==(i==133),'ll_special')
            if i<133:need(bytes.fromhex(row['decoded_hex'])==vocab[i] and row['encoded_ids']==[i],'ll_single_roundtrip')
        need(evidence['all_ids']==list(range(133)) and bytes.fromhex(evidence['all_hex'])==b''.join(vocab),'all_ordinary_roundtrip')
        need(len(evidence['positives'])==len(contract['positive_probes'])==8,'positive_count')
        for i,(text,row) in enumerate(zip(contract['positive_probes'],evidence['positives'])):
            need(row==dict(index=i,utf8_hex=text.encode('utf-8').hex(),ids=tokens(text),decoded_hex=text.encode('utf-8').hex()),'positive_evidence')
            need(133 not in row['ids'],'text_not_eos')
        negatives=evidence['negatives'];need(len(negatives)==len(contract['negative_probes'])==7,'negative_count')
        for original,row in zip(contract['negative_probes'],negatives):
            rejected=False
            try:
                text=bytes.fromhex(original['bytes_hex']).decode('utf-8') if 'bytes_hex' in original else original['text']
                text.encode('utf-8');tokens(text)
            except (UnicodeError,KeyError):rejected=True
            need(rejected and row['id']==original['id'] and row['rejected'],'negative_recomputed')
            need(row['native_calls_before']==row['native_calls_after'],'no_native_for_bad_input')
        selection=json.loads((out/snapshots[cfg['selection']]).read_text());expected=[]
        for case in selection['cases']:
            for i,test in enumerate(case['tests']):
                text=json.dumps(test['data'],ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False)
                expected.append(dict(case_id=case['case_id'],index=i,utf8_hex=text.encode('ascii').hex(),ids=tokens(text)))
        need(len(expected)==45 and evidence['selection_representability']==expected,'all45_representable_not_semantics')
        need(evidence['selection_semantics_executed'] is False,'no45_execution')
        need(evidence['xgrammar_factory']==dict(constructed=True,max_threads=1,cache_enabled=False,cache_limit_bytes=8388608),'x_compiler_construct')
        need(evidence['llguidance_factory']==dict(tokenizer_constructed=True,schema_factory_constructed=False,
             deferred_work=['grammar_from_json_schema','LLMatcher','first_mask']),'ll_deferred_factory')
        need(starts[-1]['kind']=='xgrammar_compiler_construct','compiler_after_domain_checks')
        need(status['native_calls']==evidence['native_calls']==425,'call_total')
        need(status['domain_verified'] and status['xgrammar_compiler_constructed'] and status['llguidance_tokenizer_constructed'],'setup_result')
        need(not status['backend_factory_ready'] and not status['request_admission'] and not status['live_ready'],'no_request_readiness')
        need(not status['cuda_initialized'] and not any(status['boundary_counts'][k] for k in ('file_denied','process_denied','forbidden_imports','network_denied')),'final_guards_cuda')
        need(one('worker_closed')['readiness_live'] is False,'readiness_expiry')
        need(status['startup_ns']==ready['ns']-process['spawn_ns'] and status['adapter_setup_ns']==end['ns']-ready['ns'],'independent_ledger')
        report.update(domain_factory_gate=True,ordinary_tokens=133,eos_id=133,vocab_size=134,
                      positive_probes=8,negative_rejections=7,public_instances_representable=45,public_instances_executed=0,
                      native_calls=425,startup_ns=status['startup_ns'],adapter_setup_ns=status['adapter_setup_ns'],
                      xgrammar_compiler_constructed=True,llguidance_tokenizer_constructed=True,llguidance_schema_factory_constructed=False,
                      cuda_initialized=False,boundary_counts=status['boundary_counts'])
    queries=[]
    for p in out.glob('lookup-*.json'):
        q=json.loads(p.read_text());need(q['argv']==['/sbin/ldconfig','-p'] and q['exit_code']==0,'query_exit')
        for stream,cap in [('stdout',262144),('stderr',65536)]:
            raw=(out/f"lookup-{q['number']}-{stream}.binlog").read_bytes()
            need(len(raw)==q[stream+'_bytes'] and len(raw)<=cap and hashlib.sha256(raw).hexdigest()==q[stream+'_sha256'],'query_bytes')
        queries.append(q)
    need(len(queries)<=4,'query_cap');report['queries']=queries
    (out/'independent_verification.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
