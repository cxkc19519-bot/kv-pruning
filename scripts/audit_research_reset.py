"""CPU-only synthesis of frozen local evidence and pinned upstream source text.

No model imports, third-party code execution, new data generation, or inference.
"""
import argparse
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    p=argparse.ArgumentParser();p.add_argument('--results',required=True);p.add_argument('--sources',required=True)
    p.add_argument('--proposal',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False);results=Path(a.results).resolve();start=time.time()
    source=Path(__file__).read_bytes();(root/'source_audit_research_reset.py').write_bytes(source)
    manifest=dict(args=vars(a),status='preparing',rows=0,start_unix=start,source_sha256={'audit_research_reset.py':sha(source)},
        scope='CPU-only evidence synthesis and static source audit. No third-party code import or model outputs.')
    save(root/'manifest.json',manifest);inputs={};source_checks=[]
    try:
        source_path=Path(a.sources).resolve();inputs[str(source_path)]=sha(source_path.read_bytes())
        for entry in json.loads(source_path.read_text(encoding='utf-8')):
            data=entry['content'].encode();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            assert blob==entry['git_blob_sha1'],'Connector content differs from Git blob: '+entry['destination']
            dest=root/'upstream'/entry['destination'];assert dest.resolve().is_relative_to(root.resolve())
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            check={k:v for k,v in entry.items() if k!='content'};check.update(bytes=len(data),sha256=sha(data),git_blob_verified=True)
            if dest.suffix=='.py':
                tree=ast.parse(data);check.update(ast_valid=True,classes=[n.name for n in tree.body if isinstance(n,ast.ClassDef)],
                    imports=[ast.unparse(n) for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))])
            source_checks.append(check)
        save(root/'upstream_checks.json',source_checks)
        proposal=Path(a.proposal).resolve();inputs[str(proposal)]=sha(proposal.read_bytes());(root/'proposal.json').write_bytes(proposal.read_bytes())
        def rows(name):
            folder=results/name;mfile=folder/'manifest.json';gfile=folder/'generations.jsonl'
            m=json.loads(mfile.read_text());assert m['status']=='complete'
            values=[json.loads(s) for s in gfile.read_text().splitlines()];assert m['rows']==len(values)
            for path in [mfile,gfile]:inputs[str(path)]=sha(path.read_bytes())
            for filename,digest in m.get('source_sha256',{}).items():assert sha((folder/('source_'+filename)).read_bytes())==digest
            return values
        access=[]
        for name in ['20261028-access-full-v1','20261028-qwen3-access-dev-v1','20261028-mistral-access-dev-v1']:
            values=rows(name);assert len(values)==24
            groups={condition:dict(n=sum(r['condition']==condition for r in values),
                correct=sum(r['metrics']['correct'] for r in values if r['condition']==condition),
                raw_forbidden=sum(r['metrics']['forbidden_salary_emitted'] for r in values if r['condition']==condition))
                for condition in ['self_allowed','peer_denied','self_missing']}
            access.append(dict(run=name,groups=groups,base_contexts=len({r['base'] for r in values})))
        trace=rows('20261027-trace-facts-diagnostic-v1');grouped=defaultdict(list)
        for row in trace:grouped[(row['policy'],row['keep'])].append(row)
        facts=[dict(policy=k[0],keep=k[1],n=len(v),correct=sum(r['metrics']['correct'] for r in v),
            kv_bytes=sorted({r['prefix_kv_bytes'] for r in v})) for k,v in grouped.items()]
        fresh=rows('20261027-trace-fresh-baseline-v1')
        scale=rows('20261027-scale-fresh-baseline-v2')
        result=dict(access_original_task=access,small_directory_facts_diagnostic=facts,
            structured_fresh_baseline=dict(n=len(fresh),correct=sum(r['metrics']['correct'] for r in fresh)),
            larger_directory_full={task:dict(n=sum(r['task']==task for r in scale),correct=sum(r['metrics']['correct'] for r in scale if r['task']==task)) for task in ['permission','routing']},
            upstream_files=len(source_checks),upstream_python_ast_checked=sum(c.get('ast_valid',False) for c in source_checks),
            all_upstream_blobs_verified=True,new_model_outputs=0,
            inference='Existing data do not establish a safety-specific binding failure; all-fact protection explains the tested small-directory degradation, and larger/full task quality is insufficient.',
            limitation='Selected evidence summary, not new independent samples, third-party execution, full reproduction, or exhaustive novelty certification.')
        save(root/'evidence_summary.json',result)
        manifest.update(status='complete',end_unix=time.time(),input_sha256=inputs,upstream_files=len(source_checks),new_model_outputs=0)
        save(root/'manifest.json',manifest);print(json.dumps(result,indent=2))
    except Exception as error:
        manifest.update(status='failed',end_unix=time.time(),input_sha256=inputs,error_type=type(error).__name__,error_message=str(error));save(root/'manifest.json',manifest);raise


if __name__=='__main__':main()
