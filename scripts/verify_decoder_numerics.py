"""Independent readback: formulas for dispatch, causal visibility and probabilities."""
import sys
sys.dont_write_bytecode = True
from array import array
from decimal import Decimal, localcontext
import json
import math
import struct
from pathlib import Path


def read(p):return json.loads(p.read_text())


def probabilities(values):
    maximum=max(values);weights=[math.exp(x-maximum) for x in values];z=math.fsum(weights)
    return [w/z for w in weights]


def verify_metrics(actual,p,q):
    a,b=probabilities(p),probabilities(q)
    maximum_p,maximum_q=max(p),max(q)
    assert actual['reference_argmax_indices']==[i for i,v in enumerate(p) if v==maximum_p]
    assert actual['comparison_argmax_indices']==[i for i,v in enumerate(q) if v==maximum_q]
    assert actual['argmax_equal']==(actual['reference_argmax_indices']==actual['comparison_argmax_indices'])
    near=lambda x,y:abs(x-y)<=1e-10
    assert near(actual['total_variation'],math.fsum(abs(x-y) for x,y in zip(a,b))/2)
    assert near(actual['max_probability_error'],max(abs(x-y) for x,y in zip(a,b)))
    assert near(actual['max_abs_logit'],max(abs(x-y) for x,y in zip(p,q)))
    assert near(actual['reference_top_probability'],max(a)) and near(actual['comparison_top_probability'],max(b))
    ordered=sorted(a,reverse=True);margin=ordered[0]-ordered[1]
    assert near(actual['reference_probability_margin'],margin)
    assert actual['same_decision_margin_sufficient']==(margin>2*max(abs(x-y) for x,y in zip(a,b)))
    delta=[y-x for x,y in zip(p,q)];shift=math.fsum(x*d for x,d in zip(a,delta))
    assert near(actual['probability_weighted_logit_shift'],shift)
    assert near(actual['reference_weighted_centered_RMS'],math.sqrt(math.fsum(x*(d-shift)**2 for x,d in zip(a,delta))))
    assert near(actual['shift_centered_max_logit_error'],max(abs(d-shift) for d in delta))
    klpq=math.fsum(x*math.log(x/y) for x,y in zip(a,b) if x and y)
    klqp=math.fsum(y*math.log(y/x) for x,y in zip(a,b) if x and y)
    assert near(actual['KL_p_q'],max(0.,klpq)) and near(actual['KL_q_p'],max(0.,klqp))
    js=.5*math.fsum((x*math.log(x/((x+y)/2)) if x else 0)+(y*math.log(y/((x+y)/2)) if y else 0) for x,y in zip(a,b))
    assert near(actual['Jensen_Shannon'],max(0.,js))
    if len(p)==4:
        with localcontext() as context:
            context.prec=60
            dp=[Decimal(str(x)).exp() for x in p];dq=[Decimal(str(x)).exp() for x in q]
            zp,zq=sum(dp),sum(dq);dp=[x/zp for x in dp];dq=[x/zq for x in dq]
            precise=sum(x*(x.ln()-y.ln()) for x,y in zip(dp,dq))
            assert near(actual['KL_p_q'],float(precise))


def main():
    out=Path(sys.argv[1]);cfg=read(out/'registration_snapshot.json');parent=Path(cfg['root'])/cfg['parent_run']
    trace=[json.loads(x) for x in (parent/'forward_trace.jsonl').read_text().splitlines()]
    rows=read(out/'source_branch_replay.json');assert len(rows)==len(trace)==56
    for row,t in zip(rows,trace):
        n=len(t['input_ids']);m=t['physical_before'];mask_none=n==1 or m==0
        assert row['call']==t['call'] and row['path']==t['path']
        assert row['query_length']==n and row['physical_before']==m and row['mask_none']==mask_none
        assert row['is_causal']==(mask_none and n>1) and row['enable_gqa']==mask_none
        assert row['key_shape']==row['value_shape']==[1,4 if mask_none else 28,m+n,128]
        assert row['repeat_kv_calls']==(0 if mask_none else 2)
        assert row['query_shape']==[1,28,n,128]
    case=read(parent/'engineering_inputs.json')[0]
    maps={r['name']:r['indices'] for r in read(parent/'gather_plans.json')}
    for name,indices in maps.items():
        for j in range(24):
            batch_physical=[k for k in range(186+24) if k<=186+j]
            serial_physical=list(range(186+j+1))
            assert batch_physical==serial_physical
            logical=indices+list(range(373,397))
            assert [logical[k] for k in batch_physical]==indices+list(range(373,373+j+1))
    summary=read(out/'summary.json');branch=summary['source_branch_analysis']
    assert {k:branch[k] for k in ['replayed_calls','mask_none','explicit_mask','enable_gqa','explicit_KV_repeat','is_causal_true','mathematical_causal_rows_checked']}==dict(
        replayed_calls=56,mask_none=51,explicit_mask=5,enable_gqa=51,explicit_KV_repeat=5,is_causal_true=3,mathematical_causal_rows_checked=1287)
    assert branch['exact_CUDA_kernel_observed'] is False and summary['all_error_due_to_backend_switch_proven'] is False
    vectors={}
    for row in read(parent/'vectors.json'):
        values=array('f');values.frombytes((parent/row['file']).read_bytes());vectors[row['name']]=values
    reports=read(out/'logit_probability_metrics.json');assert len(reports)==4
    for report in reports:
        p,q=vectors[report['reference_path']],vectors[report['comparison_path']]
        assert report['all_values_on_BF16_grid']==all(struct.unpack('<I',struct.pack('<f',x))[0]&65535==0 for x in list(p)+list(q))
        verify_metrics(report['scopes']['global'],p,q)
        verify_metrics(report['scopes']['allowed'],[p[i] for i in [32,33,34,35]],[q[i] for i in [32,33,34,35]])
    assert summary['parent_engineering_status']=='failed_unchanged' and summary['H3_candidate_rankings_computed'] is False
    assert summary['new_tolerance_selected'] is False
    assert not any(n.split('.')[0] in ('torch','transformers','numpy','tokenizers','audit_decoder_numerics') for n in sys.modules)
    result=dict(passed_scoped_readback=True,branch_rows_recomputed=56,causal_rows=1287,logit_path_pairs=4,
                probability_scopes=8,Decimal60_allowed_KL_checks=4,source_logic_not_CUDA_observation=True,
                no_new_model_or_GPU_actions=True,original_engineering_failed_unchanged=True)
    (out/'independent_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
