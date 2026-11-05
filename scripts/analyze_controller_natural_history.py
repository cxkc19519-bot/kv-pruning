"""Independent stdlib audit of saved trace math; no model, CUDA or native code."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def choose_budget(confidences,draft_cost,verify_cost):
    scores=[]
    for row in confidences:
        survival=1.0
        for q in row:
            assert math.isfinite(q) and 0<=q<=1
            survival*=q;scores.append(survival)
    scores.sort(reverse=True)
    n=len(confidences);est=float(n);objectives=[]
    for k in range(len(scores)+1):
        if k:est+=scores[k-1]
        cost=draft_cost[n]+verify_cost[n+k]
        assert cost>0
        objectives.append(est/cost)
    return max(range(len(objectives)),key=objectives.__getitem__),objectives


def audit_trace(path,begin,cost):
    rows=[json.loads(l) for l in path.read_text().splitlines()]
    assert rows[0]['event']=='verification' and rows[0]['num_sampled']==[1]
    assert rows[0]['num_accepted']==rows[0]['num_rejected']==[0]
    assert (len(rows)-1)%3==0
    assert [x['index'] for x in rows]==list(range(1,len(rows)+1))
    phase,refits=begin['status']['phase'],begin['status']['refits']
    counts=list(begin['counts']);allocation=None;budgets=[];conf=[];objectives=[]
    admitted=accepted=target=0
    for row in rows:
        if row['event']=='budget':
            assert len(row['request_ids'])==1 and row['non_draft_tokens']==[1]
            assert row['scheduled_drafts']==[4]
            budget,objective=choose_budget(row['stale_confidences'],*cost)
            assert budget==row['selected_draft_budget']
            assert row['total_tokens']==1+budget
            budgets.append(budget);conf.append(row['stale_confidences'][0]);objectives.append(objective)
        elif row['event']=='allocation':
            allocation=row
            assert row['selected_draft_budget']==row['capacities'][0]==budgets[-1]
            assert row['cu_num_logits']==[0,budgets[-1]+1]
            assert row['query_start_loc']==[0,budgets[-1]+1]
            admitted+=budgets[-1];target+=budgets[-1]+1
        elif row['event']=='verification':
            assert row['phase_before']==phase and row['refits_before']==refits
            acc=max(row['num_sampled'][0]-1,0);rej=row['num_rejected'][0]
            assert acc==row['num_accepted'][0]
            assert acc+rej==(0 if allocation is None else allocation['capacities'][0])
            for features,predictions in zip(row['features'],row['predictions']):
                assert all(math.isfinite(x) and abs(x)<=40 for x in features)
                assert all(math.isfinite(x) and 0<=x<=1 for x in predictions)
            if not row['frozen']:
                # Counts are integer-valued: only accepted prefix + first reject.
                for k in range(min(acc+1,acc+rej)):counts[k]+=1
                phase+=1
                if phase==100:phase=0;refits+=1;counts=[0.0]*4
            assert counts==row['counts_after']
            assert phase==row['phase_after'] and refits==row['refits_after']
            accepted+=acc
        else:raise AssertionError(row['event'])
    return dict(events=len(rows),verification_steps=sum(x['event']=='verification' for x in rows),
                decode_steps=len(budgets),budgets=budgets,admitted=admitted,accepted=accepted,
                decode_target_query_tokens=target,end_phase=phase,end_refits=refits,end_counts=counts,
                confidences=conf,objectives=objectives)


def sigmoid(x):return 1/(1+math.exp(-x))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-dir',required=True);a=ap.parse_args()
    run=Path(a.run_dir).resolve();assert (run/'independent_analysis.json').exists() is False
    s=json.loads((run/'summary.json').read_text());assert s['status']=='complete'
    manifest=json.loads((run/'manifest.json').read_text())
    assert all(digest(run/f)==h for f,h in manifest.items())
    rows=[json.loads(l) for l in (run/'answers.jsonl').read_text().splitlines()]
    by={r['label']:r for r in rows};assert len(by)==len(rows)==34
    assert collections.Counter(r['kind'] for r in rows)==dict(main=30,warmup=2,engineering=2)
    assert sum(len(r['token_ids']) for r in rows)==1856
    assert all(len(r['token_ids'])==r['requested_tokens'] for r in rows)
    b=s['boundaries'];common=b['common'];cost=common['cost_tables']
    assert all(x['cost_sha256']==common['cost_sha256'] for x in b.values())
    assert by['engineering_hook_off']['token_ids']==by['engineering_hook_on']['token_ids']
    assert b['engineering_hook_off_end']['status']['learning_digest']==b['engineering_hook_on_end']['status']['learning_digest']
    audits={}
    audits['engineering_hook_on']=audit_trace(run/'engineering_hook_on.trace.jsonl',common,cost)
    audits['baseline_probe']=audit_trace(run/'baseline_probe.trace.jsonl',common,cost)
    for group in ['A','B','A_frozen','B_frozen']:
        begin=common
        for i in range(6):
            name=group+f'_history_{i}'
            r=audit_trace(run/(name+'.trace.jsonl'),begin,cost);audits[name]=r
            begin=dict(status=dict(phase=r['end_phase'],refits=r['end_refits']),counts=r['end_counts'])
        actual=b[group.replace('_frozen','')+('_frozen_history_after' if '_frozen' in group else '_history_after')]
        assert begin['counts']==actual['counts']
        assert begin['status']['phase']==actual['status']['phase'] and begin['status']['refits']==actual['status']['refits']
        if '_frozen' not in group:assert actual['status']['refits']>common['status']['refits']
        else:assert actual['status']['learning_digest']==common['status']['learning_digest']
        name=group+'_probe';audits[name]=audit_trace(run/(name+'.trace.jsonl'),actual,cost)
    audits['restored_B_probe']=audit_trace(run/'restored_B_probe.trace.jsonl',common,cost)
    probes=['baseline_probe','A_probe','B_probe','A_frozen_probe','B_frozen_probe','restored_B_probe']
    base=audits['baseline_probe'];comparison={}
    for name in probes:
        assert by[name]['token_ids']==by['baseline_probe']['token_ids']
        r=audits[name]
        assert all(r[k]==s['probe_comparison'][name][mapping] for k,mapping in [
            ('verification_steps','steps'),('budgets','decode_budgets'),('admitted','total_admitted'),
            ('accepted','total_accepted'),('decode_target_query_tokens','decode_target_query_tokens')])
        assert len(r['confidences'])==len(base['confidences'])
        delta=max(abs(v-w) for row1,row2 in zip(r['confidences'],base['confidences']) for v,w in zip(row1,row2))
        comparison[name]={k:r[k] for k in ['verification_steps','decode_steps','budgets','admitted','accepted','decode_target_query_tokens']}
        comparison[name]['max_confidence_abs_difference_from_baseline']=delta
        comparison[name]['token_ids_exact']=True
    plateau=all(cost[1][i]==cost[1][1] for i in range(1,6))
    assert plateau
    # Offline selector sensitivity only: use physically possible uniform logits
    # and duplicate each probability vector for N=2. No batched model was run.
    xmin=-math.log(151936-1)
    theoretical={}
    for label,point in [('common',common),('A_history',b['A_history_after']),('B_history',b['B_history_after'])]:
        st=point['status'];probs=[sigmoid(st['slope']*xmin+bias) for bias in st['intercepts']]
        one,obj1=choose_budget([probs],*cost);two,obj2=choose_budget([probs,probs],*cost)
        theoretical[label]=dict(feature=xmin,confidence=probs,N1_budget=one,N2_budget=two,
                                N1_objectives=obj1,N2_objectives=obj2)
    report=dict(status='pass',main_answers=30,engineering_answers=2,warmup_answers=2,
        total_answers=34,generated_tokens=1856,trace_files=len(audits),
        budget_decisions_recomputed=sum(len(x['budgets']) for x in audits.values()),
        verification_steps_checked=sum(x['verification_steps'] for x in audits.values()),
        censored_counts_and_phases_exact=True,observer_transparency_pass=True,
        all_probe_ids_exact=True,probe_comparison=comparison,
        all_probe_allocation_sequences_identical=all(audits[n]['budgets']==base['budgets'] for n in probes),
        native_costs=dict(draft_N1=cost[0][1],draft_N2=cost[0][2],verify_first11=cost[1][:11],
                          single_request_cost_plateau=plateau),
        controller_before={k:common['status'][k] for k in ['phase','refits','slope','intercepts']},
        controller_after_histories={n:{k:b[n+'_history_after']['status'][k] for k in ['phase','refits','slope','intercepts']} for n in ['A','B']},
        offline_uniform_logit_selector_replay=theoretical,
        qualifications=['No observed allocation or accepted-token loss on these probes',
          'Cost plateau makes this N1 regime insensitive to positive survival scores',
          'Offline N2 replay is synthetic uniform-logit input, not actual batched model evidence',
          'No latency/availability attack or novelty established; no statistical generalization from repeated fixed histories'])
    (run/'analysis_source.py').write_bytes(Path(__file__).read_bytes())
    (run/'independent_analysis.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
