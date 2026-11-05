"""Index server-only run artifacts and verify their recorded source snapshots."""
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('results')
p.add_argument('--out',required=True)
a=p.parse_args()
root=Path(a.results);items=[]
for folder in sorted(root.iterdir()):
    manifest=folder/'manifest.json'
    if not folder.is_dir() or not manifest.exists():continue
    data=json.loads(manifest.read_text());generations=folder/'generations.jsonl'
    rows=[json.loads(s) for s in generations.read_text().splitlines()] if generations.exists() else []
    expected={}
    if 'script_sha256' in data:expected['source_pilot.py']=data['script_sha256']
    if 'code_sha256' in data:expected['source_baseline_audit.py']=data['code_sha256']
    if 'pilot_sha256' in data:expected['source_pilot.py']=data['pilot_sha256']
    expected.update({'source_'+name:digest for name,digest in data.get('source_sha256',{}).items()})
    checks={}
    for name,digest in expected.items():
        path=folder/name
        checks[name]=hashlib.sha256(path.read_bytes()).hexdigest()==digest if path.exists() else None
        assert checks[name] is not False,'Source snapshot mismatch: '+str(path)
    if data.get('status')=='complete':assert data['rows']==len(rows),'Row count mismatch: '+str(folder)
    items.append({'run':folder.name,'status':data.get('status','incomplete_or_failed'),
                  'rows':len(rows),'args':data.get('args'),'source_checks':checks,
                  'bytes':sum(path.stat().st_size for path in folder.rglob('*') if path.is_file())})
result={'runs':items,'total_rows':sum(x['rows'] for x in items),'note':'Repeated development and control conditions are not independent samples.'}
Path(a.out).write_text(json.dumps(result,indent=2))
for x in items:print(x['run'],x['status'],x['rows'],x['source_checks'])
print('TOTAL_ROWS',result['total_rows'])
