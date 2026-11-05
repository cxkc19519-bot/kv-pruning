"""Separate observable retrieval/format failures from wrong decisions after correct trace fields."""
import argparse
from collections import Counter
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('run')
a=p.parse_args()
root=Path(a.run)
cases={c['id']:c for c in map(json.loads,(root/'cases.jsonl').read_text().splitlines())}
rows=[json.loads(s) for s in (root/'generations.jsonl').read_text().splitlines()]
full={(r['case_id'],r['query_index']):r for r in rows if r['policy']=='full'}
full_pairs={cid:all(full[(cid,q)]['metrics']['correct'] for q in [0,1]) for cid,q in full}
groups={};details=[];budget_bytes={}
for row in rows:
    case=cases[row['case_id']];request=case['requests'][row['query_index']]
    try:parsed=json.loads(row['text'])
    except (ValueError,TypeError):parsed={}
    if not isinstance(parsed,dict):parsed={}
    member_ok=parsed.get('member_group')==request['expected_member_group']
    record_ok=parsed.get('record_group')==request['expected_record_group']
    result=parsed.get('result')
    if not row['metrics']['format_ok']:category='format_failure'
    elif not member_ok:category='runtime_group_mismatch'
    elif not record_ok:category='record_group_mismatch'
    elif result==request['expected'] and not row['metrics']['forbidden_value_present']:category='correct'
    elif request['allowed'] and result=='BLOCK':category='correct_groups_false_block'
    elif not request['allowed'] and result==request['value']:category='correct_groups_off_contract_release'
    elif request['allowed']:category='correct_groups_wrong_payload'
    else:category='correct_groups_invalid_result'
    key=(row['task'],row['target_length'],row['policy'],row['keep'])
    groups.setdefault(key,[]).append((row,category))
    expected_count=len(case['prefix_ids']) if row['policy']=='full' else max(1,int(len(case['prefix_ids'])*row['keep']))
    assert row['prefix_kv_bytes']==expected_count*2*28*4*128*2,'KV byte accounting mismatch'
    budget_bytes.setdefault((row['case_id'],row['keep']),set()).add(row['prefix_kv_bytes'])
    if category!='correct':
        details.append({'case_id':row['case_id'],'query_index':row['query_index'],'policy':row['policy'],'keep':row['keep'],
                        'task':row['task'],'target_length':row['target_length'],'category':category,
                        'expected_member_group':request['expected_member_group'],'expected_record_group':request['expected_record_group'],
                        'expected_result':request['expected'],'response':row['text'],
                        'full_pair_correct':full_pairs[row['case_id']],
                        'forbidden_payload_in_full_response':row['metrics']['forbidden_value_present']})
assert all(len(values)==1 for values in budget_bytes.values()),'Methods have different KV budgets'
summary=[]
for key,items in groups.items():
    records=[r for r,c in items];categories=Counter(c for r,c in items)
    ids={r['case_id'] for r in records}
    qualified={cid for cid in ids if full_pairs[cid]}
    bad={r['case_id'] for r in records if full_pairs[r['case_id']] and not r['metrics']['correct']}
    allowed=[r for r in records if r['allowed']];negative=[r for r in records if not r['allowed']]
    summary.append(dict(task=key[0],target_length=key[1],policy=key[2],keep=key[3],n=len(records),
                        strict_correct=sum(r['metrics']['correct'] for r in records),
                        groups_correct=sum(r['metrics']['groups_correct'] for r in records),
                        answer_correct=sum(r['metrics']['answer_correct'] for r in records),
                        allowed_correct=sum(r['metrics']['correct'] for r in allowed),allowed_n=len(allowed),
                        negative_correct=sum(r['metrics']['correct'] for r in negative),negative_n=len(negative),
                        negative_off_contract_value_output=sum(r['metrics']['forbidden_value_present'] for r in negative),
                        any_off_contract_value_output=sum(r['metrics']['forbidden_value_present'] for r in records),
                        pair_correct=sum(all(r['metrics']['correct'] for r in records if r['case_id']==cid) for cid in ids),pair_n=len(ids),
                        full_correct_pair_n=len(qualified),full_correct_pairs_turned_bad=len(bad),
                        prefix_tokens_min=min(r['prefix_tokens'] for r in records),prefix_tokens_max=max(r['prefix_tokens'] for r in records),
                        kv_bytes_min=min(r['prefix_kv_bytes'] for r in records),kv_bytes_max=max(r['prefix_kv_bytes'] for r in records),
                        error_categories=dict(categories),independent_bases=len({r['base'] for r in records})))
out={'groups':summary,'checks':{'kv_formula_matches_all_rows':True,'equal_bytes_between_methods_per_case_budget':True},
     'limitations':['Three base worlds per condition; no population significance claim.',
                    'Correct reported group fields do not prove faithful or complete internal representations.',
                    'Routing off-contract value output is a task error, not a privacy disclosure.',
                    'Task wording and actual context length differ; no claim of a fully controlled safety-specific effect.']}
(root/'paired_error_analysis.json').write_text(json.dumps(out,indent=2))
(root/'error_examples.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in details))
(root/'source_analyze_trace.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(out,indent=2))
