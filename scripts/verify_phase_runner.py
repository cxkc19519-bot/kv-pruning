"""Reconstruct phase deadlines and interval accounting without importing worker code."""
import hashlib
import json
from pathlib import Path
import sys


def need(value,reason):
    if not value:raise AssertionError(reason)


def derive(trace):
    need(trace and trace[0]['event']=='startup_begin','startup_origin')
    origin=trace[0]['t_ns'];owner=trace[0]['owner'];scope=trace[0]['scope_hash']
    need(trace[0]['deadline_ns']==origin+30_000_000_000,'startup30')
    ready=None;factory_begin=None;factory_end=None;closed=None;jobs=[];current=None
    last=origin
    for r in trace:
        now=r['t_ns'];need(now>=last and r['owner']==owner and r['scope_hash']==scope,'trace_identity_clock');last=now
        event=r['event']
        if event=='library_import_ready':ready=now;need(now<origin+30_000_000_000,'ready_after_timeout')
        if event=='factory_begin':factory_begin=now
        if event=='backend_factory_ready':factory_end=now;need(factory_begin is not None,'factory_missing_begin')
        if event=='request_submitted':
            need(ready is not None and factory_end is not None and current is None,'request_before_factory')
            need(r['deadline_ns']==now+5_000_000_000,'request5_origin')
            current=dict(request_id=r['request_id'],submit_ns=now,deadline_ns=r['deadline_ns'],stages=[],caller_return_ns=None,work_end_ns=None,censored=False);jobs.append(current)
        if event=='request_stage':
            need(current is not None and r['deadline_ns']==current['deadline_ns'] and now<current['deadline_ns'],'stage_reset_or_late')
            current['stages'].append(dict(name=r['name'],t_ns=now))
        if event=='caller_timeout':
            need(current is not None and now>=current['deadline_ns'] and not r['work_ended'],'timeout_not_work_end')
            current['caller_return_ns']=now
        if event=='work_finished':
            need(current is not None and current['request_id']==r['request_id'],'finish_wrong_job')
            current['work_end_ns']=now;current=None
        if event=='closed':
            closed=now
            if current is not None:current['censored']=True
    intervals=[]
    if ready is not None:intervals.append((origin,ready))
    if factory_end is not None:intervals.append((factory_begin,factory_end))
    intervals.extend((j['submit_ns'],j['work_end_ns']) for j in jobs if j['work_end_ns'] is not None)
    points=sorted({p for interval in intervals for p in interval})
    covered=sum(b-a for a,b in zip(points,points[1:]) if any(x<=a and b<=y for x,y in intervals))
    durations=[None if j['work_end_ns'] is None else j['work_end_ns']-j['submit_ns'] for j in jobs]
    return dict(startup_ns=None if ready is None else ready-origin,
                factory_setup_ns=None if factory_end is None else factory_end-factory_begin,
                cold_first_request_ns=durations[0] if durations else None,warm_request_ns=durations[1:],
                end_to_end_ns=None if closed is None else closed-origin,accounted_interval_union_ns=covered,
                unallocated_or_idle_ns=None if closed is None else closed-origin-covered,
                request_jobs=jobs,live_ready=False if closed is not None else ready is not None)


def verify(out):
    for name,h in json.loads((out/'worker_manifest.json').read_text()).items():
        p=(out/name).resolve();need(p.is_relative_to(out),'manifest_path')
        need(hashlib.sha256(p.read_bytes()).hexdigest()==h,'hash:'+name)
    cfg=json.loads((out/'registration_snapshot.json').read_text());process=json.loads((out/'worker-process.json').read_text())
    rows=[json.loads(line) for line in (out/'events.jsonl').read_text().splitlines()]
    for i,r in enumerate(rows):
        need(r['seq']==i+1 and r['owner_pid']==process['worker_pid'] and r['owner_starttime']==process['worker_starttime'],'event_identity')
        if i:need(r['ns']>=rows[i-1]['ns'],'event_clock')
    report=dict(status='complete',mode=cfg['mode'],finite_semantic_gate=False,old_cold5_gate=False,request_admission=False)
    if cfg['mode']=='software':
        cases=json.loads((out/'software-cases.json').read_text())
        expected=json.loads((out/'input_startup-request-contract-draft-v1.json').read_text())['next_software_acceptance']['case_ids']
        need([c['case'] for c in cases]==expected and len(cases)==8,'fixed_cases')
        for c in cases:need(derive(c['trace'])==c['ledger'],'independent_ledger:'+c['case'])
        need(cases[0]['evidence']['callback_calls']==0 and any(r.get('reason')=='no_active_request' for r in cases[0]['trace']),'startup_schema_block')
        need(any(r['event']=='startup_timeout' for r in cases[1]['trace']) and not cases[1]['ledger']['request_jobs'],'startup_timeout_admission')
        need(cases[2]['ledger']['startup_ns'] is not None and cases[2]['ledger']['factory_setup_ns'] is None and not cases[2]['ledger']['request_jobs'],'imports_not_factory')
        for c in cases[3:5]:
            j=c['ledger']['request_jobs'][0];need(j['submit_ns']==2_000_000_000 and j['deadline_ns']==7_000_000_000,'validation_and_stage_clock')
            need(any(r.get('reason')=='request_deadline' and r['t_ns']>=j['deadline_ns'] for r in c['trace']),'stage_deadline_observed')
        j=cases[5]['ledger']['request_jobs'][0];need(j['caller_return_ns']==7_000_000_000 and j['work_end_ns']==8_000_000_000,'separate_return_and_stop')
        invalid=[r for r in cases[6]['trace'] if r['event']=='scope_invalidated'];need(len(invalid)==1 and invalid[0]['observed_scope_hash']!=invalid[0]['scope_hash'],'scope_invalidated')
        ownertrace=cases[6]['evidence']['owner_trace'];derive(ownertrace)
        need(any(r['event']=='scope_invalidated' and r['observed_owner']!=r['owner'] for r in ownertrace),'owner_invalidated')
        ledger=cases[7]['ledger'];need(ledger['startup_ns']==20_000_000_000 and ledger['factory_setup_ns']==4_000_000_000,'startup_factory_cost')
        need(ledger['cold_first_request_ns']==4_500_000_000 and ledger['warm_request_ns']==[2_000_000_000],'cold_warm_cost')
        need(ledger['end_to_end_ns']==45_000_000_000 and ledger['unallocated_or_idle_ns']==14_500_000_000,'interval_union_not_double_counted')
        status=json.loads((out/'worker-status.json').read_text());need(not any(status['guard'].values()),'software_scope_guard')
        report.update(phase_software_passed=True,cases=8,ledger_recomputations=9,guard=status['guard'])
    else:
        traces=[r['detail'] for r in rows if r['event']=='phase_event']
        ready=[r for r in traces if r['event']=='library_import_ready']
        need(traces and traces[0]['t_ns']==process['spawn_ns'],'startup_from_parent_spawn')
        need(not any(r['event'] in ('request_submitted','request_stage','factory_begin','backend_factory_ready') for r in traces),'import_only_scope')
        query_records=[]
        for p in sorted(out.glob('lookup-*.json')):
            q=json.loads(p.read_text());need(q['argv']==['/sbin/ldconfig','-p'] and q['exit_code'] is not None,'lookup_identity_exit')
            for name,cap in [('stdout',262144),('stderr',65536)]:
                b=(out/f"lookup-{q['number']}-{name}.binlog").read_bytes();need(len(b)==q[name+'_bytes'] and len(b)<=cap and hashlib.sha256(b).hexdigest()==q[name+'_sha256'],'lookup_bytes')
            need(q['seconds']<2,'lookup_time_and_cleanup');query_records.append(q)
        need(len(query_records)<=4,'lookup_count')
        if ready:
            need(len(ready)==1 and ready[0]['t_ns']-process['spawn_ns']<30_000_000_000 and process['worker_exit_code']==0,'startup_gate')
            status=json.loads((out/'worker-status.json').read_text());need(not status['cuda_initialized'] and not status['backend_factory_ready'] and not status['request_admission'],'imports_only_ready')
            state=json.loads((out/'phase-state.json').read_text());need(state['ledger']==derive(state['trace']) and not state['ledger']['live_ready'],'readiness_expires_at_exit')
            report.update(library_import_ready_observed=True,startup_import_gate=True,startup_ns=ready[0]['t_ns']-process['spawn_ns'],ledger=state['ledger'],boundary_counts=status['boundary_counts'])
        else:
            need(process['worker_exit_code']!=0,'missing_readiness_outcome')
            if process.get('startup_timeout'):need(process['watchdog_ns']-process['spawn_ns']>=30_000_000_000,'timeout_early')
            report.update(library_import_ready_observed=False,startup_import_gate=False,failure_or_censoring=True)
        report['queries']=query_records
    (out/'independent_verification.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
