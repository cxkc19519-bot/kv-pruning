"""Posthoc CPU selector replay of every saved real draft feature vector.

Duplicating a vector for N=2 is a counterfactual, not a batched model run.
No contexts are selected or newly generated, and no performance is measured.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path

from analyze_controller_natural_history import choose_budget


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-dir',required=True);a=ap.parse_args()
    run=Path(a.run_dir).resolve();out=run/'real_feature_selector_replay.json';assert not out.exists()
    summary=json.loads((run/'summary.json').read_text());assert summary['status']=='complete'
    b=summary['boundaries'];cost=b['common']['cost_tables']
    states={label:b[key]['status'] for label,key in [('common','common'),('A','A_history_after'),('B','B_history_after')]}
    answers={x['label']:x for x in (json.loads(l) for l in (run/'answers.jsonl').read_text().splitlines())}
    rows=[];unique=set();minimum=40.0;maximum=-40.0
    for path in sorted(run.glob('*.trace.jsonl')):
        label=path.name.removesuffix('.trace.jsonl');events=[json.loads(l) for l in path.read_text().splitlines()]
        assert label in answers
        # The first prefill verification has no current draft features.
        for event in events[1:]:
            if event['event']!='verification':continue
            assert len(event['features'])==1
            features=event['features'][0];unique.add(tuple(features))
            minimum=min(minimum,*features);maximum=max(maximum,*features)
            decisions={}
            for name,state in states.items():
                probabilities=[1/(1+math.exp(-(state['slope']*x+v))) for x,v in zip(features,state['intercepts'])]
                single,_=choose_budget([probabilities],*cost)
                double,objectives=choose_budget([probabilities,probabilities],*cost)
                descending=sorted(objectives,reverse=True)
                decisions[name]=dict(N1=single,N2=double,N2_objective_margin=descending[0]-descending[1])
            rows.append(dict(label=label,kind=answers[label]['kind'],event_index=event['index'],
                             features=features,decisions=decisions))
    report=dict(kind='posthoc_counterfactual_cpu_selector_replay',total_real_feature_vectors=len(rows),
        unique_vectors=len(unique),feature_min=minimum,feature_max=maximum,
        max_q_min=1/(1+math.exp(-minimum)),max_q_max=1/(1+math.exp(-maximum)),
        N1_choices={name:dict(collections.Counter(str(r['decisions'][name]['N1']) for r in rows)) for name in states},
        N2_choices={name:dict(collections.Counter(str(r['decisions'][name]['N2']) for r in rows)) for name in states},
        N2_disagreements_from_common={name:sum(r['decisions'][name]['N2']!=r['decisions']['common']['N2'] for r in rows) for name in ['A','B']},
        qualifications=['All recorded decode feature vectors retained, including repeated contexts; not independent statistical samples',
            'Counterfactual N2 duplicates one saved vector and reuses the cost table; no batched logits, allocation, outputs or latency observed',
            'No prompt search, new inference or model/backend change',
            'A positive hypothetical uniform-logit example is not evidence of naturally occurring harm'],rows=rows)
    out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (run/'selector_replay_source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))


if __name__=='__main__':main()
