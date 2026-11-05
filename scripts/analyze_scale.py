"""Paired descriptive analysis and physical-index audit of server-only scale runs."""
import argparse
import hashlib
import json
from pathlib import Path

import torch


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--baseline');a=p.parse_args()
    root=Path(a.run);rows=read(root/'generations.jsonl');cases={c['id']:c for c in read(root/'cases.jsonl')}
    if a.baseline:
        assert (root/'cases.jsonl').read_bytes()==(Path(a.baseline)/'cases.jsonl').read_bytes(), 'Frozen case mismatch'
    full={(r['case_id'],r['query_index']):r for r in rows if r['policy']=='full'}
    full_worlds={cid for cid,c in cases.items() if all(full[(cid,i)]['metrics']['correct'] for i in range(len(c['requests'])))}
    cohorts=[]
    for count in sorted({c['record_count'] for c in cases.values()}):
        cc=[c for c in cases.values() if c['record_count']==count]
        assert len({len(c['prefix_ids']) for c in cc})==1
        assert len({len(q['suffix_ids']) for c in cc for q in c['requests']})==1
        for policy in sorted({r['policy'] for r in rows}):
            subset=[r for r in rows if r['record_count']==count and r['policy']==policy]
            assert len({r['prefix_kv_bytes'] for r in subset})==1
            expected=(len(cc[0]['prefix_ids']) if policy=='full' else len(cc[0]['prefix_ids'])//2)*57344
            assert all(r['prefix_kv_bytes']==expected for r in subset)
            cohorts.append(dict(record_count=count,policy=policy,prefix_tokens=len(cc[0]['prefix_ids']),
                                suffix_tokens=len(cc[0]['requests'][0]['suffix_ids']),prefix_kv_bytes=expected))
    coverage={};index_checks=0
    for cid,case in cases.items():
        path=root/'cache_maps'/f'{cid}.pt'
        if not path.exists():continue
        evidence=torch.load(path,map_location='cpu',weights_only=False)
        for policy,indices in evidence['kept_indices'].items():
            counts=[];rule=[];by_object={q['object']:[] for q in case['requests']}
            for layer,heads in indices.items():
                assert heads.shape==(1,4,len(case['prefix_ids']) if policy=='full' else len(case['prefix_ids'])//2)
                for head in heads[0]:
                    ids=head.tolist();kept=set(ids);assert len(ids)==len(kept) and ids==sorted(ids)
                    assert set(range(4))|set(range(len(case['prefix_ids'])-64,len(case['prefix_ids']))) <= kept
                    if policy in ['expected_rules','expected_rows','random_rows']:
                        assert set(case['rule_ids']) <= kept
                    counts.append(sum(set(row)<=kept for row in case['fact_row_ids']))
                    rule.append(len(set(case['rule_ids'])&kept)/len(case['rule_ids']))
                    for obj in by_object:
                        pos=case['fact_row_objects'].index(obj);row=set(case['fact_row_ids'][pos])
                        by_object[obj].append((len(row&kept)/len(row),row<=kept))
                    index_checks+=1
            coverage[(cid,policy)]=dict(mean_complete_rows=sum(counts)/len(counts),rule_fraction=sum(rule)/len(rule),
                queries={obj:dict(mean_token_fraction=sum(x[0] for x in vv)/len(vv),complete_head_fraction=sum(x[1] for x in vv)/len(vv)) for obj,vv in by_object.items()})
    stats=[]
    for task,policy in sorted({(r['task'],r['policy']) for r in rows}):
        subset=[r for r in rows if r['task']==task and r['policy']==policy]
        conditional=[r for r in subset if r['case_id'] in full_worlds]
        errors={name:0 for name in ['schema','group','groups_correct_wrong_result','forbidden_value']}
        for r in subset:
            m=r['metrics']
            if m['forbidden_value_present']:errors['forbidden_value']+=1
            if not m['format_ok']:errors['schema']+=1
            elif not m['groups_correct']:errors['group']+=1
            elif not m['answer_correct']:errors['groups_correct_wrong_result']+=1
        world_keys={(r['base'],r['query_index']) for r in subset}
        both=sum(all(r['metrics']['correct'] for r in subset if (r['base'],r['query_index'])==key) for key in world_keys)
        cov=[coverage[(r['case_id'],policy)]['queries'][r['object']] for r in subset if (r['case_id'],policy) in coverage]
        stats.append(dict(task=task,policy=policy,n=len(subset),correct=sum(r['metrics']['correct'] for r in subset),
                         conditional_world_n=len({r['case_id'] for r in conditional}),conditional_n=len(conditional),
                         conditional_correct=sum(r['metrics']['correct'] for r in conditional),errors=errors,
                         allowed_n=sum(r['allowed'] for r in subset),allowed_correct=sum(r['metrics']['correct'] for r in subset if r['allowed']),
                         denied_n=sum(not r['allowed'] for r in subset),denied_correct=sum(r['metrics']['correct'] for r in subset if not r['allowed']),
                         swap_pair_n=len(world_keys),swap_pair_correct=both,
                         mean_target_complete_head_fraction=sum(c['complete_head_fraction'] for c in cov)/len(cov) if cov else None))
    gaps=[]
    for policy in sorted({r['policy'] for r in rows}):
        per_base=[]
        for base in sorted({r['base'] for r in rows}):
            scores={task:[r['metrics']['correct'] for r in rows if r['base']==base and r['policy']==policy and r['task']==task] for task in ['permission','routing']}
            per_base.append(dict(base=base,permission_minus_routing=sum(scores['permission'])/len(scores['permission'])-sum(scores['routing'])/len(scores['routing'])))
        gaps.append(dict(policy=policy,cluster_gaps=per_base,mean_gap=sum(x['permission_minus_routing'] for x in per_base)/len(per_base)))
    result=dict(groups=stats,byte_audit=cohorts,index_head_checks=index_checks,permission_routing_gaps=gaps,
                full_correct_worlds=len(full_worlds),total_worlds=len(cases),
                base_worlds=len({r['base'] for r in rows}),
                notes=['Small development set; swaps/tasks/queries are dependent. No significance or generalization claim.',
                       'Complete row retention is an index diagnostic, not a faithful causal explanation of model state.',
                       'groups_correct_wrong_result combines payload lookup and decision failures; not automatically binding failure.'])
    (root/'paired_error_analysis.json').write_text(json.dumps(result,indent=2))
    source=Path(__file__).read_bytes()
    (root/'analysis_source_analyze_scale.py').write_bytes(source)
    (root/'analysis_manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source).hexdigest(),
        inputs={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['cases.jsonl','generations.jsonl']},
        index_files=len(list((root/'cache_maps').glob('*.pt')))),indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
