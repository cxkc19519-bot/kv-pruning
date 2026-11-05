"""Independent stdlib readback of all saved vectors, Full gate and exploratory go/no-go."""
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
    out=Path(sys.argv[1]);cfg=read(out/'registration_snapshot.json');root=Path(cfg['root'])
    summary=read(out/'screen_summary.json');full=read(out/'Full_outcomes.json');gate=read(out/'Full_support.json')
    cases=read(out/'development_inputs.json');source={c['case_id']:c for c in read(root/cfg['selected_cases'])}
    original={c['case_id']:c for c in read(root/cfg['native_inputs'])}
    assert [c['case_id'] for c in cases]==cfg['development_case_ids'] and all(c==original[c['case_id']] and c['role']=='development' for c in cases)
    vectors={}
    for row in read(out/'vectors.json'):
        p=out/row['file'];assert sha(p)==row['sha256'] and p.stat().st_size==152064*4
        values=array('f');values.frombytes(p.read_bytes());assert len(values)==152064 and all(math.isfinite(x) for x in values)
        key=(row['case_id'],row['name']);assert key not in vectors;vectors[key]=values
    for c,row in zip(cases,full):
        cid=c['case_id'];v=vectors[cid,'full'];peak=max(v[i] for i in [32,33,34,35]);pred=[i for i in [32,33,34,35] if v[i]==peak]
        assert row==dict(case_id=cid,gold=source[cid]['gold'],legal_argmax_ids=pred,gold_correct=pred==[32+'ABCD'.index(source[cid]['gold'])])
    correct=sum(x['gold_correct'] for x in full);assert gate['correct']==correct and gate['passed']==(correct>=10)
    assert len(full)==gate['total']==12 and gate['threshold']==10
    plans=read(out/'candidate_plans.json');assert len(plans)==12
    for c,p in zip(cases,plans):
        cid=c['case_id'];scorebytes=gzip.decompress((out/(cid+'.prefix_scores.json.gz')).read_bytes())
        assert hashlib.sha256(scorebytes).hexdigest()==p['score_sha256'];scores=json.loads(scorebytes)
        assert set(scores)=={str(i) for i in range(28)}
        avg=[math.fsum(scores[str(l)][0][h][i] for l in range(28) for h in range(4))/112 for i in range(373)]
        anchors=c['anchors'];free=[i for i in range(373) if i not in anchors]
        names=['adapted_snapkv','recency']+['random_'+str(s) for s in cfg['random_seeds']]
        picks=[sorted(free,key=lambda i:(-avg[i],i))[:118],sorted(free,reverse=True)[:118]]+[random.Random(s).sample(free,118) for s in cfg['random_seeds']]
        assert p['mask_plan']['candidates']==[dict(name=n,indices=sorted(anchors+x)) for n,x in zip(names,picks)]
    analysis=read(out/'analysis.json');calls=0;tokens=0
    traces=[json.loads(x) for x in (out/'forward_trace.jsonl').read_text().splitlines()]
    for t in traces:
        c=original[t['case_id']];assert c['role']=='development'
        if t['path']=='scored_prefix':
            assert t['input_ids']==c['prefix_ids'] and t['logical_positions']==list(range(373));calls+=1;tokens+=373
        else:
            physical=373 if t['path']=='full' else 186
            assert t['input_ids']==c['suffix_ids'] and t['logical_positions']==list(range(373,397))
            assert t['cache_positions']==list(range(physical,physical+24)) and t['mask_mode']=='explicit_full_attention_dictionary'
            raw=(out/t['mask_file']).read_bytes();expected=bytes(int(k<=physical+j) for j in range(24) for k in range(physical+24))
            assert raw==expected and hashlib.sha256(raw).hexdigest()==t['mask_sha256'];calls+=1;tokens+=24
    assert calls==summary['forward_calls'] and tokens==summary['input_tokens']
    if gate['passed']:
        assert len(vectors)==108 and calls==132 and tokens==11544
        groups=read(out/'candidate_measurements.json');assert len(groups)==12
        transitions={o:{s:0 for s in ['legal_win','legal_loss','tie','ambiguous_tie']} for o in ['global','top128','top256']}
        mismatch=0;klcount=0
        for group,report in zip(groups,analysis['group_reports']):
            cid=group['case_id'];p=vectors[cid,'full'];assert group['gold']==source[cid]['gold']
            assert group['Full_legal_argmax_ids']==next(x['legal_argmax_ids'] for x in full if x['case_id']==cid)
            supports=dict(global_vocab=range(152064),top128=sorted(sorted(range(152064),key=lambda i:(-p[i],i))[:128]),top256=sorted(sorted(range(152064),key=lambda i:(-p[i],i))[:256]),legal=[32,33,34,35]);supports['global']=supports.pop('global_vocab')
            for candidate in group['candidates']:
                q=vectors[cid,candidate['name']];peak=max(q[i] for i in [32,33,34,35])
                assert candidate['legal_argmax_ids']==[i for i in [32,33,34,35] if q[i]==peak]
                for o,ids in supports.items():assert abs(candidate['scores'][o]-kl(p,q,ids))<1e-8;klcount+=1
            candidates=group['candidates'];chosen={}
            for o in ['global','top128','top256','legal']:
                best=min(c['scores'][o] for c in candidates);near=[c for c in candidates if c['scores'][o]<=best+1e-8]
                selected=near[0];fidelity=[c['legal_argmax_ids']==group['Full_legal_argmax_ids'] for c in near]
                expected=dict(chosen=selected['name'],within_tolerance=[c['name'] for c in near],legal_argmax_ids=selected['legal_argmax_ids'],Full_argmax_fidelity=fidelity[0],tied_fidelity_unambiguous=len(set(fidelity))==1,gold_correct=selected['legal_argmax_ids']==[32+'ABCD'.index(group['gold'])])
                assert report['selections'][o]==expected;chosen[o]=expected
            group_inv=False
            for o in transitions:
                inverse=[]
                for a,c1 in enumerate(candidates):
                    for c2 in candidates[a+1:]:
                        x=c1['scores'][o]-c2['scores'][o];y=c1['scores']['legal']-c2['scores']['legal']
                        if abs(x)>1e-8 and abs(y)>1e-8 and x*y<0:inverse.append([c1['name'],c2['name']])
                assert report['inversions'][o]==inverse;group_inv=group_inv or bool(inverse)
                a,b=chosen[o],chosen['legal']
                state=('ambiguous_tie' if not(a['tied_fidelity_unambiguous'] and b['tied_fidelity_unambiguous']) else
                       'legal_win' if not a['Full_argmax_fidelity'] and b['Full_argmax_fidelity'] else
                       'legal_loss' if a['Full_argmax_fidelity'] and not b['Full_argmax_fidelity'] else 'tie')
                assert report['fidelity_transitions'][o]==state;transitions[o][state]+=1
            mismatch+=group_inv
        go=mismatch>=3 and all(v['legal_win']>=2 and v['legal_win']>v['legal_loss'] for v in transitions.values())
        assert analysis['ranking_mismatch_groups']==mismatch and analysis['transitions']==transitions and analysis['development_go']==go
        assert analysis['decision']==('signal_warrants_separate_independent_review' if go else 'stop_current_H3_candidate_no_expansion')
    else:
        assert len(vectors)==12 and calls==24 and tokens==4764 and analysis['decision']=='stop_Full_support_below10of12';klcount=0
    directory=Path(cfg['model_path'])
    for name,h in {**cfg['weights'],**cfg['model_metadata_files']}.items():assert sha(directory/name)==h
    assert not any(n.split('.')[0] in ('torch','transformers','decoder_screen_analysis','decoder_objective') for n in sys.modules)
    result=dict(verified=True,groups=12,Full_correct=correct,Full_support=gate['passed'],vectors=len(vectors),KL_values_recomputed=klcount,
        forward_calls=calls,input_tokens=tokens,decision=analysis['decision'],development_go=analysis['development_go'],new_answers_generated=0,statistical_confirmation=False,novelty_established=False)
    (out/'independent_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':main()
