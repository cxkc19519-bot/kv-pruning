"""Paired descriptive frontend audit; raw artifacts remain on experiment server."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();root=Path(a.run)
    read=lambda name:[json.loads(s) for s in (root/name).read_text().splitlines()]
    rows=read('generations.jsonl');cases=read('cases.jsonl')
    original={(r['case_id'],r['query_index']):r for r in rows if r['variant']=='original'}
    result=[]
    for task,variant in sorted({(r['task'],r['variant']) for r in rows}):
        subset=[r for r in rows if r['task']==task and r['variant']==variant]
        errors=dict(schema=0,wrong_reported_groups=0,groups_correct_wrong_result=0,forbidden_value=0)
        for r in subset:
            m=r['metrics']
            if not m['format_ok']:errors['schema']+=1
            elif not m['groups_correct']:errors['wrong_reported_groups']+=1
            elif not m['answer_correct']:errors['groups_correct_wrong_result']+=1
            if m['forbidden_value_present']:errors['forbidden_value']+=1
        entry=dict(task=task,variant=variant,n=len(subset),correct=sum(r['metrics']['correct'] for r in subset),errors=errors,
            allowed_n=sum(r['allowed'] for r in subset),allowed_correct=sum(r['metrics']['correct'] for r in subset if r['allowed']),
            denied_n=sum(not r['allowed'] for r in subset),denied_correct=sum(r['metrics']['correct'] for r in subset if not r['allowed']))
        if original:
            entry.update(fixed=sum(r['metrics']['correct'] and not original[(r['case_id'],r['query_index'])]['metrics']['correct'] for r in subset),
                regressed=sum(not r['metrics']['correct'] and original[(r['case_id'],r['query_index'])]['metrics']['correct'] for r in subset),
                original_n=len(subset))
        result.append(entry)
    shapes=[]
    for variant in sorted({c['frontend'] for c in cases}):
        subset=[c for c in cases if c['frontend']==variant]
        shapes.append(dict(variant=variant,prefix_tokens=sorted({len(c['prefix_ids']) for c in subset}),
            suffix_tokens=sorted({len(q['suffix_ids']) for c in subset for q in c['requests']}),
            full_tokens=sorted({len(c['prefix_ids'])+len(q['suffix_ids']) for c in subset for q in c['requests']}),
            first_fact_by_task={task:sorted({c['fact_row_ids'][0][0] for c in subset if c['task']==task}) for task in ['permission','routing']},
            rules_anchors_tokens=sorted({c['capacity_audit']['rules_anchors_tokens'] for c in subset})))
    correctness=json.loads((root/'correctness_checks.json').read_text())
    assert all(c['native_cached_exact'] and c['custom_cached_exact'] for c in correctness)
    exact=[r for r in rows if r['variant']=='original']
    output=dict(groups=result,shapes=shapes,cache_path_queries_checked=len(correctness),base_worlds=len({c['base'] for c in cases}),
        original_repeat_n=len(exact),original_repeat_token_exact=sum(r['token_exact_with_source'] for r in exact),
        note='Small dependent development data. Padding and role changes are joint interventions; oracle row cannot establish a deployable method.')
    (root/'paired_error_analysis.json').write_text(json.dumps(output,indent=2))
    source=Path(__file__).read_bytes();(root/'analysis_source_analyze_frontend.py').write_bytes(source)
    manifest=dict(source_sha256=digest(source),input_sha256={name:digest((root/name).read_bytes()) for name in ['cases.jsonl','generations.jsonl','correctness_checks.json']})
    (root/'analysis_manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(output,indent=2))


if __name__=='__main__':main()
