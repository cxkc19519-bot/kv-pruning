"""Verify frozen inputs and separate semantic conflicts from label spelling.

Additional echo-format parsing is descriptive and does not change the original
RULER scores/gates. OrgAccess is never relabelled or filtered for model scoring.
"""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,indent=2),encoding='utf-8')


def conflict_summary(rows,fields):
    groups=defaultdict(list)
    for i,row in enumerate(rows):groups[tuple(row[field] for field in fields)].append((i,row['expected_response']))
    canonical={'full','partial','rejected'};conflicts=[]
    for members in groups.values():
        labels={lab.strip().lower() for i,lab in members if lab.strip().lower() in canonical}
        if len(labels)>1:conflicts.append(dict(row_indices=[i for i,lab in members],original_labels=[lab for i,lab in members],canonical_labels=sorted(labels)))
    return dict(input_fields=fields,groups=len(conflicts),rows=sum(len(x['row_indices']) for x in conflicts),
                note='Only distinct canonical full/partial/rejected labels count as a semantic conflict; aliases are not automatically mapped.'),conflicts


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--data-root',required=True);a=p.parse_args()
    root=Path(a.run);data_root=Path(a.data_root)
    manifest=json.loads((data_root/'manifest.json').read_text())
    for name,info in manifest['upstream_files'].items():assert sha((data_root/'upstream'/name).read_bytes())==info['sha256']
    items=pq.read_table(data_root/'upstream/data/easy-00000-of-00001.parquet').to_pylist()
    official,conflicts=conflict_summary(items,['permissions','query'])
    with_metadata,full_conflicts=conflict_summary(items,['user_role','permissions','query','query_timestamp'])
    save(root/'orgaccess_canonical_conflicts.json',conflicts)
    save(root/'orgaccess_canonical_conflicts_with_role_timestamp.json',full_conflicts)
    original_labels=Counter(row['expected_response'] for row in items)
    rows=[json.loads(s) for s in (root/'generations.jsonl').read_text().splitlines()]
    cases={c['case_id']:c for c in map(json.loads,(root/'cases.jsonl').read_text().splitlines())}
    ruler=[r for r in rows if r['task']=='ruler'];counts=defaultdict(int)
    import re
    for row in ruler:
        case=cases[row['case_id']];digits=re.findall(r'\d+',row['text'])
        if digits==[case['query_key'],case['expected']]:counts['query_key_then_correct_value']+=1
        elif digits==[case['expected']]:counts['correct_value_only_numeric_sequence']+=1
        else:counts['other_numeric_sequence']+=1
    selected=[json.loads(s) for s in (data_root/'orgaccess_first32.jsonl').read_text().splitlines()]
    for item in selected:
        source=items[item['row_index']]
        assert item['source_row_sha256']==sha(json.dumps(source,sort_keys=True,ensure_ascii=False).encode())
    checks=json.loads((root/'correctness_checks.json').read_text());assert len(checks)==2
    assert all(c['native_cached_exact'] and c['custom_cached_exact'] for c in checks)
    result=dict(source_rows=len(items),source_labels=dict(original_labels),
        noncanonical_label_rows=sum(n for lab,n in original_labels.items() if lab not in ['full','partial','rejected']),
        exact_visible_input_canonical_conflicts=official,with_role_and_timestamp_canonical_conflicts=with_metadata,
        specific_example=dict(first_index=117,second_index=433,permissions_query_role_timestamp_equal=
            all(items[117][f]==items[433][f] for f in ['permissions','query','user_role','query_timestamp']),
            original_labels=[items[117]['expected_response'],items[433]['expected_response']]),
        ruler_numeric_output_patterns=dict(counts),cache_parity_requests=len(checks),selected_source_row_hashes_verified=len(selected),
        note='Raw 600-string-conflict count also includes label aliases; use canonical-conflict counts above. No generation score or gold label is changed.')
    save(root/'additional_data_analysis.json',result)
    source=Path(__file__).read_bytes();(root/'analysis_source_analyze_benchmark_controls.py').write_bytes(source)
    save(root/'analysis_manifest.json',dict(source_sha256=sha(source),input_sha256={str(path):sha(path.read_bytes()) for path in [
        root/'generations.jsonl',root/'cases.jsonl',root/'correctness_checks.json',data_root/'upstream/data/easy-00000-of-00001.parquet',data_root/'orgaccess_first32.jsonl']}))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
