"""Summarize all rows and baseline-correct paired worlds without cherry-picking."""
import argparse
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("run")
args=p.parse_args()
root=Path(args.run)
rows=[json.loads(s) for s in (root/'generations.jsonl').read_text().splitlines()]
full={(r['case_id'],r['query_index']):r for r in rows if r['policy']=='full'}
pair_ok={cid: all(full[(cid,q)]['metrics']['correct'] for q in [0,1]) for cid,q in full}
groups={}
for r in rows:
 key=(r['task'],r['target_length'],r['policy'],r['keep'])
 groups.setdefault(key,[]).append(r)
out=[]
for key,items in groups.items():
 allowed=[r for r in items if r['allowed']]
 denied=[r for r in items if not r['allowed']]
 pairs={r['case_id'] for r in items}
 qualified=[r for r in items if pair_ok[r['case_id']]]
 qualified_pairs={r['case_id'] for r in qualified}
 bad_pairs={r['case_id'] for r in qualified if not r['metrics']['correct']}
 out.append(dict(task=key[0],target_length=key[1],policy=key[2],keep=key[3],n=len(items),
                 correct=sum(r['metrics']['correct'] for r in items),
                 allowed_correct=sum(r['metrics']['correct'] for r in allowed),allowed_n=len(allowed),
                 denied_correct=sum(r['metrics']['correct'] for r in denied),denied_n=len(denied),
                 forbidden_release=sum(r['metrics']['forbidden_value_present'] for r in denied),
                 false_deny=sum(r['metrics']['exact_deny'] for r in allowed),
                 pair_correct=sum(all(r['metrics']['correct'] for r in items if r['case_id']==cid) for cid in pairs),pair_n=len(pairs),
                 full_correct_pair_n=len(qualified_pairs),full_correct_pairs_turned_bad=len(bad_pairs),
                 prefix_kv_bytes_min=min(r['prefix_kv_bytes'] for r in items),prefix_kv_bytes_max=max(r['prefix_kv_bytes'] for r in items),
                 independent_base_worlds=len({r['base'] for r in items})))
result={'groups':out,'note':'Development diagnostic only; no population CI with three base worlds; timings include reference-cache overhead.'}
(root/'paired_analysis.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
