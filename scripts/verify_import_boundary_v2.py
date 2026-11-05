"""Independent boundary-result, query-byte and import-event verification."""
import hashlib
import json
from pathlib import Path
import sys


def need(value,reason):
    if not value:raise AssertionError(reason)


def verify(out):
    for name,h in json.loads((out/'worker_manifest.json').read_text()).items():
        path=(out/name).resolve();need(path.is_relative_to(out),'manifest_boundary')
        need(hashlib.sha256(path.read_bytes()).hexdigest()==h,'hash:'+name)
    cfg=json.loads((out/'registration_snapshot.json').read_text())
    process=json.loads((out/'worker-process.json').read_text())
    rows=[json.loads(line) for line in (out/'events.jsonl').read_text().splitlines()]
    for i,r in enumerate(rows):
        need(r['seq']==i+1,'event_sequence')
        need(r['owner_pid']==process['worker_pid'] and r['owner_starttime']==process['worker_starttime'],'owner_identity')
        if i:need(r['ns']>=rows[i-1]['ns'],'clock')
    records=[]
    pins=json.loads((out/'input_pins.json').read_text())
    for f in sorted(out.glob('lookup-*.json')):
        r=json.loads(f.read_text());n=r['number']
        need(r['argv']==['/sbin/ldconfig','-p']==pins['loader']['argv'],'literal_command')
        for name in ('stdout','stderr'):
            data=(out/f'lookup-{n}-{name}.binlog').read_bytes()
            need(len(data)==r[name+'_bytes'] and hashlib.sha256(data).hexdigest()==r[name+'_sha256'],'query_bytes')
            need(len(data)<=(262144 if name=='stdout' else 65536),'query_output_bound')
        need(r['exit_code'] is not None,'query_reaped')
        need(r['seconds']<2,'query_timeout_and_cleanup_bound')
        records.append(r)
    need(len(records)<=4,'query_count')
    denied=[r for r in rows if r['event']=='boundary_denied']
    report=dict(status='complete',mode=cfg['mode'],queries=len(records),query_processes=records,
                finite_semantic_gate=False,guarded_native_import_gate=False,schema_mask_model_calls=0)
    if cfg['mode']=='software':
        result=json.loads((out/'software-results.json').read_text())
        expected_true={'devnull_rdwr','run_write_allowed','query_exact','query_count_cap','capture_overflow','capture_timeout','actual_query_bounded','raw_popen_bypass_denied','pinned_devnull_buffered_writer','pinned_devnull_pyio_writer','actual_builtin_and_pyio_writers'}
        expected_false={'devnull_append_denied','devnull_create_denied','devnull_wrong_identity_denied','outside_write_denied','model_read_denied','query_extra_arg_denied','query_alias_denied','query_shell_denied','query_env_denied','query_stdout_denied','query_cwd_denied','query_identity_denied'}
        cases=result['cases'];need(len(cases)==23,'case_count')
        need({c['case'] for c in cases}==expected_true|expected_false,'case_set')
        for c in cases:
            expected=c['case'] in expected_true
            need(c['expected']==expected and c['actual']==expected and c['passed'],'independent_case:'+c['case'])
        need(len(records)==1 and records[0]['exit_code']==0 and records[0]['error'] is None,'actual_query')
        need(len(denied)==1 and denied[0]['category']=='process_denied','expected_bypass_denial_only')
        need(result['query_count']==1 and result['boundary_counts']['devnull_allowed']>=1,'device_observed')
        report.update(software_cases=23,software_passed=True,boundary_counts=result['boundary_counts'])
    else:
        begins=[r for r in rows if r['event']=='aggregate_import_begin'];ends=[r for r in rows if r['event']=='aggregate_import_end']
        need(len(begins)==1 and len(ends)<=1 and begins[0]['deadline_ns']==5_000_000_000,'one_aggregate_deadline')
        expected=['torch_import_begin','torch_import_end','torch_thread_settings_begin','torch_thread_settings_end','xgrammar_import_begin','xgrammar_import_end']
        names=[r['event'] for r in rows if r['event'] in expected]
        need(names==expected[:len(names)],'checkpoint_prefix')
        report.update(checkpoints=names,import_completed=bool(ends),boundary_denials=denied)
        if process.get('aggregate_expired'):
            need(not ends and process['worker_exit_code']==-9,'timeout_censored')
            need(process['watchdog_ns']-begins[0]['ns']>=5_000_000_000,'original_clock_not_reset')
        if ends:
            duration=ends[0]['ns']-begins[0]['ns'];report['aggregate_ns']=duration
            report['cuda_initialized']=ends[0]['cuda_initialized']
            report['guarded_native_import_gate']=duration<=5_000_000_000 and not denied and not ends[0]['cuda_initialized'] and process['worker_exit_code']==0
        else:
            report['failure_or_censoring']=True
        need(all(r['error'] is None and r['exit_code']==0 for r in records) or process['worker_exit_code']!=0,'query_failure_preserved')
    (out/'independent_verification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report))


if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
