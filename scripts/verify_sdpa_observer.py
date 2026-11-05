"""Independent stdlib serialization/identity-assertion and archive readback."""
import sys
sys.dont_write_bytecode=True
import hashlib
import json
from pathlib import Path


def main():
    out=Path(sys.argv[1]);results=json.loads((out/'software_results.json').read_text());by={r['id']:r['output'] for r in results}
    assert [r['id'] for r in results]==['O'+str(i).zfill(2) for i in range(1,19)]+['A'+str(i).zfill(2) for i in range(1,7)]
    expected_errors={6:['sink_error:RuntimeError'],7:['marker_enter_error:RuntimeError'],8:['marker_exit_error:RuntimeError'],
        9:['marker_exit_error:RuntimeError'],11:['target_replaced_by_foreign_owner'],12:['metadata_error:RuntimeError'],14:['record_limit_exceeded']}
    for i in range(1,17):
        r=by['O'+str(i).zfill(2)]
        assert r['errors']==expected_errors.get(i,[]) and r['argument_objects_and_keyword_order_preserved']
        assert all(r['returned_identity'])
        assert r['original_restored']==(i!=11)
        assert r['observer_calls']==(3 if i==14 else 2 if i==15 else 1)
        assert r['original_body_calls']==(0 if i==16 else r['observer_calls'])
        assert len(r['records'])==(2 if i in (14,15) else 1)
        assert [e['call'] for e in r['records']]==list(range(1,len(r['records'])+1))
        for e in r['records']:
            assert e['marker']=='kv_sdpa_'+str(e['call']).zfill(7)
            assert e['status']==('original_exception' if i in (4,5,9,16) else 'returned')
            if i!=12:assert e['query']['shape']==[1,28,24 if i==2 else 1,128]
            assert e['key']['shape']==e['value']['shape']==[1,4,210 if i==2 else 187,128]
        if i in (4,5,9,16):assert r['original_exception_identity']
        if i==10:assert r['nested_refused']
        if i==11:assert r['foreign_preserved'] and r['conflict_refused']
        if i==13:assert r['marker_events']==[]
    assert by['O02']['records'][0]['attn_mask']['shape']==[1,1,24,210]
    assert by['O02']['records'][0]['scale']==.125
    assert by['O03']['records'][0]['positional_count']==6 and by['O03']['records'][0]['is_causal'] is True
    assert by['O03']['records'][0]['enable_gqa'] is True and by['O03']['records'][0]['mask_is_none']
    inv=by['O17']['inventory']
    assert inv['association']=='explicit_cpu_parent_lineage_only' and inv['deduplicated_or_summed_kernel_durations'] is False
    assert len(inv['markers'])==2 and [m['event_id'] for m in inv['markers']]==[1,4]
    assert inv['markers'][0]['backend_operators']==[dict(name='aten::_scaled_dot_product_flash_attention',family='flash',event_id=3)]
    assert inv['markers'][1]['backend_operators']==[dict(name='aten::_scaled_dot_product_attention_math',family='math',event_id=5)]
    assert inv['markers'][0]['kernels']==[dict(name='flash_kernel',device=0,owner_event_id=3,owner_operator='aten::_scaled_dot_product_flash_attention')]
    assert inv['markers'][1]['kernels']==[dict(name='bmm_kernel',device=0,owner_event_id=6,owner_operator='aten::bmm')]
    assert inv['unassigned_events'][0]['event_id']==7 and by['O18']['error']=='profiler_parent_cycle_or_depth'
    total=0
    for i in range(1,7):
        r=by['A'+str(i).zfill(2)];directory=out/r['directory']
        summary=json.loads((directory/'launcher_summary.json').read_text());manifest=json.loads((directory/'manifest.json').read_text())
        files=[p for p in directory.rglob('*') if p.is_file()]
        assert len(files)==r['result']['files']==summary['archive_files_including_closure']
        assert sum(p.stat().st_size for p in files)==r['result']['bytes']
        assert summary['archive_caps_checked_before_success'] and (directory/'payload.txt').read_text()=='preserve me\n'
        for rel,h in manifest.items():assert hashlib.sha256((directory/rel).read_bytes()).hexdigest()==h
        count_ok=len(files)<=r['limits']['max_files'];bytes_ok=r['result']['bytes']<=r['limits']['max_bytes']
        assert summary['status']==('complete' if i in (1,6) else 'failed')
        assert (r['result']['archive_error'] is None)==(i in (1,4,6))
        assert summary['status']!='complete' or (count_ok and bytes_ok)
        if i==6:assert r['duplicate_refused']
        total+=len(files)
    assert not any(n.split('.')[0] in ('torch','transformers','numpy','tokenizers','sdpa_observer','checked_archive','accept_sdpa_observer') for n in sys.modules)
    report=dict(passed=True,observer_software_cases=18,archive_fault_cases=6,archive_fixture_files_verified=total,
        identity_scope='Worker runtime object-identity assertions plus independent serialized-contract readback',
        synthetic_profiler_only=True,real_Torch_SDPA_tested=False,real_CUDA_profiler_validated=False,
        new_model_calls=0,GPU_queries=0)
    (out/'independent_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
