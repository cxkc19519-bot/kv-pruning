"""Freeze official OrgAccess easy snapshot and a deterministic first-32 audit set."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request,urlopen


REV='c65ef95f7a8821098906012c4236a4fcd8144f9b'
def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).read_bytes();(root/'source_prepare_benchmark_data.py').write_bytes(source)
    manifest=dict(args=vars(a),status='preparing',rows=0,start_unix=time.time(),source_sha256={'prepare_benchmark_data.py':sha(source)},
        repository='respailab/orgaccess',revision=REV,selection='Original row indices 0..31, no filtering or shuffle')
    save(root/'manifest.json',manifest);files={}
    for name in ['data/easy-00000-of-00001.parquet','LICENSE','README.md']:
        url=f'https://raw.githubusercontent.com/respailab/orgaccess/{REV}/{name}'
        with urlopen(Request(url,headers={'User-Agent':'kv-pruning-data-freeze'}),timeout=40) as response:data=response.read(30_000_001)
        assert len(data)<=30_000_000
        dest=root/'upstream'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        files[name]=dict(url=url,bytes=len(data),sha256=sha(data))
    import pyarrow.parquet as pq
    table=pq.read_table(root/'upstream/data/easy-00000-of-00001.parquet')
    items=table.slice(0,32).to_pylist();assert len(items)==32
    labels={};selected=[]
    for i,item in enumerate(items):
        assert set(item)>={'user_role','permissions','query','expected_response','rationale'}
        label=item['expected_response'].strip().lower();assert label in ['full','partial','rejected']
        labels[label]=labels.get(label,0)+1
        selected.append(dict(row_index=i,source_row_sha256=sha(json.dumps(item,sort_keys=True,ensure_ascii=False).encode()),**item))
    with (root/'orgaccess_first32.jsonl').open('w',encoding='utf-8') as f:
        for item in selected:f.write(json.dumps(item,ensure_ascii=False)+'\n')
    save(root/'data_audit.json',dict(total_rows=table.num_rows,schema=str(table.schema),selected_n=32,label_counts=labels,
        selected_sha256=sha((root/'orgaccess_first32.jsonl').read_bytes()),pyarrow_version=__import__('pyarrow').__version__,
        note='Original GitHub snapshot, not asserted equal to entire HF split. Manual label review required before gate.'))
    manifest.update(status='complete',end_unix=time.time(),upstream_files=files,total_source_rows=table.num_rows)
    save(root/'manifest.json',manifest);print(json.dumps(dict(total_rows=table.num_rows,labels=labels,files=files)),flush=True)


if __name__=='__main__':main()
