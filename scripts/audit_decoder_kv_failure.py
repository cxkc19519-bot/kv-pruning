"""Post-hoc CPU-only independent readback of both failed engineering archives.

This does not turn a failed gate into acceptance and does not rank different masks.
"""
import sys
sys.dont_write_bytecode = True
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import random
import signal


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()


def load(p):
    return json.loads(p.read_text())


def stable_logs(values):
    peak=max(values); z=math.log(math.fsum(math.exp(x-peak) for x in values))
    return [x-peak-z for x in values]


def audit_vectors(p,q):
    lp,lq=stable_logs(p),stable_logs(q)
    ap,aq=[p[i] for i in [32,33,34,35]],[q[i] for i in [32,33,34,35]]
    la,lb=stable_logs(ap),stable_logs(aq)
    diffs=[abs(x-y) for x,y in zip(p,q)];maximum=max(diffs)
    bad=[i for i,d in enumerate(diffs) if d>.25]
    pp,qp=max(p),max(q)
    return dict(max_abs=maximum,global_KL=max(0.,math.fsum(math.exp(x)*(x-y) for x,y in zip(lp,lq))),
        allowed_KL=max(0.,math.fsum(math.exp(x)*(x-y) for x,y in zip(la,lb))),
        global_argmax_equal=[i for i,x in enumerate(p) if x==pp]==[i for i,x in enumerate(q) if x==qp],
        allowed_argmax_equal=[i for i,x in enumerate(ap) if x==max(ap)]==[i for i,x in enumerate(aq) if x==max(aq)],
        max_error_token_ids=[i for i,d in enumerate(diffs) if d==maximum],
        tokens_over025=len(bad),reference_path_mass_on_tokens_over025=math.fsum(math.exp(lp[i]) for i in bad),
        compared_mass_on_tokens_over025=math.fsum(math.exp(lq[i]) for i in bad),
        allowed_max_abs=max(abs(x-y) for x,y in zip(ap,aq)))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-sha256',required=True);ap.add_argument('--v1-manifest-sha256',required=True);ap.add_argument('--v2-manifest-sha256',required=True);a=ap.parse_args()
    root=Path(__file__).resolve().parent.parent
    assert str(root)=='/home/user/jhk/project/Directional Exploration/kv-pruning' and digest(Path(__file__))==a.source_sha256
    signal.signal(signal.SIGALRM,lambda *unused:(_ for _ in ()).throw(TimeoutError('CPU90seconds')));signal.alarm(90)
    reports=[]
    for version,pin in [('v1',a.v1_manifest_sha256),('v2',a.v2_manifest_sha256)]:
        out=root/('results/20261031-decoder-kv-engineering-'+version)
        assert digest(out/'manifest.json')==pin
        for name,h in load(out/'manifest.json').items():assert digest(out/name)==h
        status=load(out/'launcher_summary.json');assert status['status']=='failed'
        report=dict(archive=out.name,original_manifest_sha256=pin,status_remains_failed=True,
                    audit_source_sha256=a.source_sha256,new_model_calls=0,thresholds_modified=False)
        if version=='v1':
            assert not (out/'forward_trace.jsonl').exists() and not (out/'actual_runtime.json').exists()
            assert load(out/'worker_guard.json')['file_attempts']==1
            assert 'tempfile.py' in (out/'worker.log').read_text()
            report.update(forward_calls=0,logit_vectors=0,cause='run-external tempfile probe blocked during Torch import')
        else:
            cfg=load(out/'registration_snapshot.json');case=load(out/'engineering_inputs.json')[0]
            assert case['case_id']=='decoder_engineering_00'
            vectors={}
            for row in load(out/'vectors.json'):
                path=out/row['file'];assert digest(path)==row['sha256'] and path.stat().st_size==152064*4
                x=array('f');x.frombytes(path.read_bytes());assert len(x)==152064 and all(math.isfinite(v) for v in x)
                vectors[row['name']]=x
            assert len(vectors)==7
            results=[]
            for label,p,q in [('whole_vs_full_batch','whole','full_batch'),('whole_vs_split_full_batch','whole','split_full_batch'),
                ('recency_batch_vs_tokenwise','recency_batch','recency_tokenwise'),
                ('uniform_random_batch_vs_tokenwise','uniform_random_batch','uniform_random_tokenwise')]:
                value=audit_vectors(vectors[p],vectors[q])
                old=next(x for x in load(out/'comparisons.json') if x['name']==label)
                for k,v in old['metrics'].items():
                    if isinstance(v,bool):assert v==value[k]
                    else:assert abs(v-value[k])<1e-8
                assert old['passed'] is False and value['max_abs']>cfg['numeric']['max_abs_logit']
                results.append(dict(name=label,metrics=value,original_gate_passed=False))
            snapshots={x['name']:x for x in load(out/'cache_snapshots.json')};raw={}
            assert set(snapshots)=={'reference','recency','uniform_random'}
            for name,record in snapshots.items():
                data=(out/record['file']).read_bytes();raw[name]=data
                assert hashlib.sha256(data).hexdigest()==record['sha256'] and len(data)==record['bytes']
                slots=373 if name=='reference' else 186
                assert len(data)==slots*57344 and len(record['tensors'])==56
                for i,t in enumerate(record['tensors']):
                    assert t['shape']==[1,4,slots,128] and t['offset']==i*4*slots*256 and t['bytes']==4*slots*256
                    assert t['layer']==i//2 and t['kind']==['K','V'][i%2]
                    assert hashlib.sha256(data[t['offset']:t['offset']+t['bytes']]).hexdigest()==t['sha256']
            anchors=case['anchors'];free=[i for i in range(373) if i not in anchors]
            expected={'recency':sorted(anchors+sorted(free,reverse=True)[:118]),
                      'uniform_random':sorted(anchors+random.Random(cfg['random_seeds'][0]).sample(free,118))}
            for name,indices in expected.items():
                assert snapshots[name]['indices']==indices
                for full,part in zip(snapshots['reference']['tensors'],snapshots[name]['tensors']):
                    source=raw['reference'][full['offset']:full['offset']+full['bytes']]
                    wanted=b''.join(source[(h*373+i)*256:(h*373+i+1)*256] for h in range(4) for i in indices)
                    assert wanted==raw[name][part['offset']:part['offset']+part['bytes']]
            integrity=load(out/'reference_integrity.json')[0]
            assert integrity['reference_sha256_before']==integrity['reference_sha256_after']==snapshots['reference']['sha256']
            trace=[json.loads(x) for x in (out/'forward_trace.jsonl').read_text().splitlines()]
            prefix,suffix=case['prefix_ids'],case['suffix_ids']
            plan=[('whole',prefix+suffix,0,0),('prefix',prefix,0,0),('full_batch',suffix,373,373),
                  ('split_prefix',prefix[:128],0,0),('split_prefix',prefix[128:],128,128),('split_full_batch',suffix,373,373)]
            for name in ['recency','uniform_random']:
                plan.append((name+'_batch',suffix,373,186))
                plan.extend((name+'_tokenwise',[token],373+i,186+i) for i,token in enumerate(suffix))
            assert len(trace)==len(plan)==56 and sum(len(x['input_ids']) for x in trace)==1287
            for t,(path,ids,logical,physical) in zip(trace,plan):
                assert t['case_id']==case['case_id'] and t['path']==path and t['input_ids']==ids
                assert t['logical_positions']==list(range(logical,logical+len(ids))) and t['cache_positions']==list(range(physical,physical+len(ids)))
                assert t['attention_shape']==[1,physical+len(ids)] and t['physical_before']==physical
            guard=load(out/'worker_guard.json');assert all(v==0 for k,v in guard.items() if k!='blocked_loopback_capability_probes')
            report.update(forward_calls=56,teacher_forced_tokens=1287,logit_vectors=7,engineering_groups_completed_computation=1,
                second_engineering_group_model_calls=0,development_model_calls=0,comparisons=results,
                actual_gather_bytes_verified=True,cache_tensors_rehashed=168,reference_bytes_unchanged=True,
                numerical_failure_independently_confirmed=True,Full_support_or_H3_signal_established=False)
        target=out/'postmortem_verification.json'
        with target.open('x') as f:json.dump(report,f,indent=2,allow_nan=False);f.write('\n')
        reports.append(report)
    assert not any(x.split('.')[0] in ('torch','transformers','numpy','decoder_kv_backend','engineer_decoder_kv') for x in sys.modules)
    signal.alarm(0)
    print(json.dumps(reports),flush=True)


if __name__=='__main__':main()
