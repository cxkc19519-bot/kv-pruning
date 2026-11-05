"""Independent live-profiler lineage and plain/observed control readback; stdlib."""
import sys
sys.dont_write_bytecode=True
from array import array
import gzip
import hashlib
import json
from pathlib import Path


def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()


def main():
    out=Path(sys.argv[1]);cfg=read(out/'registration_snapshot.json');summary=read(out/'observation_summary.json')
    assert summary['observation_completed'] and summary['old_numeric_engineering_accepted'] is False
    assert summary['forward_calls']==108 and summary['teacher_forced_input_tokens']==1082 and summary['observed_SDPA_calls']==2856
    assert not summary['observer_errors'] and summary['callable_restored'] and summary['development_model_calls']==0
    rows=read(out/'engineering_inputs.json');assert [r['case_id'] for r in rows]==cfg['engineering_case_ids']
    vectors={(v['case_id'],v['name']):v for v in read(out/'vectors.json')};assert len(vectors)==14
    for v in vectors.values():assert sha(out/v['file'])==v['sha256'] and (out/v['file']).stat().st_size==152064*4
    controls=read(out/'transparency_controls.json');assert len(controls)==4
    for c in controls:
        cid,name=c['case_id'],c['name'];a=vectors[cid,name+'_batch_plain'];b=vectors[cid,name+'_batch_observed']
        assert c['exact_logits_equal'] and (out/a['file']).read_bytes()==(out/b['file']).read_bytes()
    snapshots=read(out/'cache_snapshots.json');assert len(snapshots)==6
    for row in rows:
        pieces={r['name']:r for r in snapshots if r['case_id']==row['case_id']}
        raw={}
        for name,piece in pieces.items():
            data=(out/piece['file']).read_bytes();raw[name]=data
            slots=373 if name=='reference' else 186
            assert hashlib.sha256(data).hexdigest()==piece['sha256'] and len(data)==slots*57344
            assert len(piece['tensors'])==56
            for i,t in enumerate(piece['tensors']):
                assert t['shape']==[1,4,slots,128] and t['offset']==i*4*slots*256 and t['bytes']==4*slots*256
                assert hashlib.sha256(data[t['offset']:t['offset']+t['bytes']]).hexdigest()==t['sha256']
        for name in ['recency','uniform_random']:
            indices=pieces[name]['indices'];assert len(indices)==len(set(indices))==186 and set(row['anchors'])<=set(indices)
            for ref,part in zip(pieces['reference']['tensors'],pieces[name]['tensors']):
                data=raw['reference'][ref['offset']:ref['offset']+ref['bytes']]
                expected=b''.join(data[(h*373+i)*256:(h*373+i+1)*256] for h in range(4) for i in indices)
                assert expected==raw[name][part['offset']:part['offset']+part['bytes']]
        integrity=next(x for x in read(out/'reference_integrity.json') if x['case_id']==row['case_id'])
        assert integrity['reference_sha256_before']==integrity['reference_sha256_after']==pieces['reference']['sha256']
    records=read(out/'sdpa_records.json');assert len(records)==2856 and [r['call'] for r in records]==list(range(1,2857))
    assert all(r['status']=='returned' and r['query']['device']=='cuda:0' for r in records)
    argument_patterns={}
    for r in records:
        assert r['query']['shape'][0:2]==[1,28] and r['key']['shape']==r['value']['shape']
        pattern=str((r['mask_is_none'],r['enable_gqa'],r['key']['shape'][1],r['is_causal']))
        argument_patterns[pattern]=argument_patterns.get(pattern,0)+1
    profiles=read(out/'profiles.json');assert len(profiles)==10
    families={};kernels=set();seen=set()
    names={'aten::_scaled_dot_product_flash_attention':'flash','aten::_scaled_dot_product_efficient_attention':'efficient',
           'aten::_scaled_dot_product_attention_math':'math','aten::_scaled_dot_product_cudnn_attention':'cudnn'}
    for p in profiles:
        nodes=json.loads(gzip.decompress((out/p['event_snapshot']).read_bytes()));by={n['uid']:n for n in nodes};assert len(by)==len(nodes)
        marker_nodes={n['uid']:n for n in nodes if n['name'].startswith('kv_sdpa_')}
        actual={n['name']:dict(operators=[],kernels=[]) for n in marker_nodes.values()}
        for node in nodes:
            current=node;chain=set();marker=None
            while current is not None:
                assert current['uid'] not in chain and len(chain)<256
                chain.add(current['uid'])
                if current['uid'] in marker_nodes:marker=current['name'];break
                current=by[current['parent_uid']] if current['parent_uid'] is not None else None
            if marker is not None:
                if node['name'] in names:actual[marker]['operators'].append((node['name'],node['event_id']))
                actual[marker]['kernels'].extend((k['name'],k['device'],node['event_id'],node['name']) for k in node['kernels'])
        raw=json.loads(gzip.decompress((out/p['raw_trace']).read_bytes()))
        raw_markers={e.get('name') for e in raw['traceEvents'] if isinstance(e.get('name'),str) and e['name'].startswith('kv_sdpa_')}
        assert set(actual)==raw_markers
        expected_calls=range(p['first_observer_call'],p['last_observer_call']+1)
        assert set(actual)=={'kv_sdpa_'+str(i).zfill(7) for i in expected_calls}
        for entry in p['inventory']['markers']:
            want=actual[entry['marker']]
            assert want['operators'] and want['kernels']
            assert [(v['name'],v['event_id']) for v in entry['backend_operators']]==want['operators']
            assert [(v['name'],v['device'],v['owner_event_id'],v['owner_operator']) for v in entry['kernels']]==want['kernels']
            for op in entry['backend_operators']:families[op['family']]=families.get(op['family'],0)+1
            kernels.update(v['name'] for v in entry['kernels'])
        seen.update(expected_calls)
    assert seen==set(range(1,2857))
    traces=[json.loads(line) for line in (out/'forward_trace.jsonl').read_text().splitlines()]
    assert len(traces)==108 and sum(len(t['input_ids']) for t in traces)==1082
    for r in rows:
        trace=[t for t in traces if t['case_id']==r['case_id']];assert len(trace)==54
        expected=[('prefix',r['prefix_ids'],0,0)]
        for path,physical,tokenwise in [('full_batch_plain',373,False),('full_batch_observed',373,False),
          ('recency_batch_plain',186,False),('recency_batch_observed',186,False),('recency_tokenwise_observed',186,True),
          ('uniform_random_batch_observed',186,False),('uniform_random_tokenwise_observed',186,True)]:
            if tokenwise:expected.extend((path,[token],373+i,physical+i) for i,token in enumerate(r['suffix_ids']))
            else:expected.append((path,r['suffix_ids'],373,physical))
        for t,(path,ids,pos,physical) in zip(trace,expected):
            assert t['path']==path and t['input_ids']==ids and t['logical_positions']==list(range(pos,pos+len(ids)))
            assert t['cache_positions']==list(range(physical,physical+len(ids))) and t['attention_shape']==[1,physical+len(ids)]
    directory=Path(cfg['model_path'])
    for name,h in {**cfg['weights'],**cfg['model_metadata_files']}.items():assert sha(directory/name)==h
    report=dict(observation_verified=True,profiles=10,actual_SDPA_calls=2856,same_path_exact_controls=4,backend_operator_counts=families,
                raw_kernel_names=sorted(kernels),argument_patterns=argument_patterns,cache_tensors_rehashed=336,
                forward_calls=108,input_tokens=1082,old_numeric_gate_accepted=False,
                numerical_cause_fully_proven=False,H3_tested=False,development_model_calls=0)
    assert not any(n.split('.')[0] in ('torch','transformers','sdpa_observer','decoder_kv_backend','numpy') for n in sys.modules)
    (out/'independent_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
