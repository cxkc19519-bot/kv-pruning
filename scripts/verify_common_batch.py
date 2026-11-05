"""Independent stdlib check of canonical masks, candidates, bytes and repeated KL."""
import sys
sys.dont_write_bytecode=True
from array import array
import gzip
import hashlib
import json
import math
from pathlib import Path
import random


def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
def kl(p,q,ids):
    a=[p[i] for i in ids];b=[q[i] for i in ids];ma,mb=max(a),max(b)
    za=math.log(math.fsum(math.exp(v-ma) for v in a));zb=math.log(math.fsum(math.exp(v-mb) for v in b))
    return max(0.,math.fsum(math.exp(x-ma-za)*((x-ma-za)-(y-mb-zb)) for x,y in zip(a,b)))


def main():
    out=Path(sys.argv[1]);cfg=read(out/'registration_snapshot.json');root=Path(cfg['root']);summary=read(out/'contract_summary.json')
    assert summary['operational_contract_passed'] and summary['old_cross_path_gate_passed'] is False
    assert summary['forward_calls']==40 and summary['input_tokens']==2356 and summary['archived_logit_vectors']==36
    cases=read(out/'engineering_inputs.json');assert [c['case_id'] for c in cases]==cfg['engineering_case_ids']
    original={c['case_id']:c for c in read(root/cfg['native_inputs'])};assert all(c==original[c['case_id']] for c in cases)
    masks={x['file']:x for x in read(out/'mask_records.json')};assert len(masks)==2
    for name,m in masks.items():
        raw=(out/name).read_bytes();physical=m['shape'][-1]-24
        assert m['shape']==[1,1,24,physical+24] and physical in (186,373)
        expected=bytes(int(k<=physical+j) for j in range(24) for k in range(physical+24))
        assert raw==expected and sha(out/name)==m['sha256'] and len(raw)==m['bytes']
    plans=read(out/'candidate_plans.json');assert len(plans)==2
    snapshots=read(out/'cache_snapshots.json');assert len(snapshots)==18
    vectors=read(out/'vectors.json');assert len(vectors)==36
    byvec={(v['case_id'],v['name']):v for v in vectors};objectives=read(out/'objective_repeats.json')
    for c,plan in zip(cases,plans):
        cid=c['case_id'];assert plan['case_id']==cid and plan['hook_cache_equal'] and plan['hook_logits_equal'] and plan['hook_restored']
        scores=json.loads(gzip.decompress((out/(cid+'.prefix_scores.json.gz')).read_bytes()))
        assert set(scores)=={str(i) for i in range(28)}
        assert all(len(v)==1 and len(v[0])==4 and all(len(h)==373 for h in v[0]) for v in scores.values())
        aggregate=[math.fsum(scores[str(l)][0][h][i] for l in range(28) for h in range(4))/112 for i in range(373)]
        assert aggregate==plan['score_aggregate']
        anchors=c['anchors'];free=[i for i in range(373) if i not in anchors]
        picks=[('adapted_snapkv',sorted(free,key=lambda i:(-aggregate[i],i))[:118]),('recency',sorted(free,reverse=True)[:118])]
        picks += [('random_'+str(s),random.Random(s).sample(free,118)) for s in cfg['random_seeds']]
        expected={name:sorted(anchors+picked) for name,picked in picks}
        assert plan['mask_plan']['candidates']==[dict(name=name,indices=expected[name]) for name,picked in picks]
        records={v['name']:v for v in snapshots if v['case_id']==cid};assert set(records)==set(expected)|{'reference'}
        rawref=(out/records['reference']['file']).read_bytes()
        assert hashlib.sha256(rawref).hexdigest()==records['reference']['sha256'] and len(rawref)==373*57344
        for name,record in records.items():
            raw=(out/record['file']).read_bytes();n=373 if name=='reference' else 186
            assert len(raw)==record['bytes']==n*57344 and sha(out/record['file'])==record['sha256']
            assert len(record['tensors'])==56
            for i,t in enumerate(record['tensors']):
                assert t['shape']==[1,4,n,128] and t['offset']==i*4*n*256 and t['bytes']==4*n*256
                block=raw[t['offset']:t['offset']+t['bytes']];assert hashlib.sha256(block).hexdigest()==t['sha256']
                if name!='reference':
                    assert record['indices']==expected[name]
                    ref=rawref[i*4*373*256:(i+1)*4*373*256]
                    wanted=b''.join(ref[(h*373+j)*256:(h*373+j+1)*256] for h in range(4) for j in expected[name])
                    assert block==wanted
        integrity=next(x for x in read(out/'reference_integrity.json') if x['case_id']==cid)
        assert integrity['reference_sha256_before']==integrity['reference_sha256_after']==records['reference']['sha256']
        values={}
        for name in ['full']+list(expected):
            a,b=byvec[cid,name+'.repeat0'],byvec[cid,name+'.repeat1']
            assert sha(out/a['file'])==a['sha256'] and sha(out/b['file'])==b['sha256']
            assert (out/a['file']).read_bytes()==(out/b['file']).read_bytes()
            data=array('f');data.frombytes((out/a['file']).read_bytes());assert len(data)==152064 and all(math.isfinite(x) for x in data)
            values[name]=data
        full=values['full'];top=lambda k:sorted(sorted(range(len(full)),key=lambda i:(-full[i],i))[:k])
        supports=dict(global_vocab=list(range(152064)),top128=top(128),top256=top(256),legal=[32,33,34,35])
        supports['global']=supports.pop('global_vocab')
        for name,data in values.items():
            r=next(x for x in objectives if x['case_id']==cid and x['name']==name)
            assert r['repeats'][0]==r['repeats'][1]
            for key,ids in supports.items():
                assert r['repeats'][0][key]['status']=='finite' and abs(r['repeats'][0][key]['kl']-kl(full,data,ids))<1e-8
    records=json.loads(gzip.decompress((out/'sdpa_records.json.gz').read_bytes()));assert len(records)==1008
    assert all(not r['mask_is_none'] and r['enable_gqa'] is False and r['is_causal'] is False and r['key']['shape'][1]==28 for r in records)
    profiles=json.loads(gzip.decompress((out/'profiles.json.gz').read_bytes()));assert len(profiles)==2
    for p in profiles:
        nodes=json.loads(gzip.decompress((out/p['events']).read_bytes()));by={n['uid']:n for n in nodes}
        scopes={n['name']:[] for n in nodes if n['device_type']=='CPU' and n['name'].startswith('kv_sdpa_')}
        assert len(scopes)==504
        for n in nodes:
            if n['device_type']!='CPU' or not n['name'].startswith('aten::_scaled_dot_product_'):continue
            parent=n;seen=set()
            while parent is not None and parent['name'] not in scopes:
                assert parent['uid'] not in seen;seen.add(parent['uid']);parent=by[parent['parent_uid']] if parent['parent_uid'] is not None else None
            if parent is not None:scopes[parent['name']].append(n['name'])
        assert all(names==['aten::_scaled_dot_product_efficient_attention'] for names in scopes.values())
        chrome=json.loads(gzip.decompress((out/p['trace']).read_bytes()))
        assert {e.get('name') for e in chrome['traceEvents'] if str(e.get('name','')).startswith('kv_sdpa_')}==set(scopes)
    trace=[json.loads(x) for x in (out/'forward_trace.jsonl').read_text().splitlines()];assert len(trace)==40 and sum(len(x['input_ids']) for x in trace)==2356
    for c,plan in zip(cases,plans):
        rows=[t for t in trace if t['case_id']==c['case_id']];assert len(rows)==20
        assert [t['path'] for t in rows[:2]]==['plain_prefix','scored_prefix'] and all(t['input_ids']==c['prefix_ids'] for t in rows[:2])
        names=['full']+[v['name'] for v in plan['mask_plan']['candidates']]
        expected=[name+'.repeat0' for name in names]+[name+'.repeat1' for name in reversed(names)]
        assert [t['path'] for t in rows[2:]]==expected
        for t in rows[2:]:
            physical=373 if t['path'].startswith('full.') else 186
            assert t['input_ids']==c['suffix_ids'] and t['logical_positions']==list(range(373,397))
            assert t['cache_positions']==list(range(physical,physical+24)) and t['mask_mode']=='explicit_full_attention_dictionary'
            assert t['mask_sha256']==masks[t['mask_file']]['sha256']
    directory=Path(cfg['model_path'])
    for p,h in {**cfg['weights'],**cfg['model_metadata_files']}.items():assert sha(directory/p)==h
    assert not any(n.split('.')[0] in ('torch','transformers','common_batch_backend','decoder_objective','pilot') for n in sys.modules)
    result=dict(operational_contract_verified=True,cases=2,candidates=8,bitwise_repeated_states=18,KL_values_recomputed=72,
        actual_mask_geometries=2,cache_tensors_rehashed=1008,actual_efficient_SDPA_calls=1008,forward_calls=40,input_tokens=2356,
        old_cross_path_gate_passed=False,Full12_support_tested=False,H3_candidate_rankings_computed=False)
    (out/'independent_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':main()
