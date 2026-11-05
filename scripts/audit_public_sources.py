"""Read-only pinned public benchmark source audit; never import upstream code.

Downloaded source/license artifacts live only under the server results path.
This is not a dataset or model benchmark run and generates no model outputs.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request,urlopen


SOURCES={
    'ruler':dict(repo='NVIDIA/RULER',revision='c3f5e3b4f87f97e048793bb510a3a6b19a46bf3a',
        files=['README.md','LICENSE','scripts/data/synthetic/niah.py','scripts/data/synthetic/constants.py']),
    'orgaccess':dict(repo='respailab/orgaccess',revision='c65ef95f7a8821098906012c4236a4fcd8144f9b',
        files=['README.md','LICENSE','evaluation.py']),
    'accessdenied':dict(repo='DrenFazlija/AccessDeniedInc',revision='1a43c47a3d6619d2bc6a0e05899dab900760ecdc',
        files=['README.md','LICENSE','scripts/grade.py','question_prompt.py','scripts/questionnaire.py'])}


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,indent=2),encoding='utf-8')


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False)
    data=Path(__file__).read_bytes();(root/'source_audit_public_sources.py').write_bytes(data)
    manifest=dict(args=vars(a),status='running',start_unix=time.time(),source_sha256={'audit_public_sources.py':sha(data)},
        public_sources=SOURCES,rows=0,scope='Pinned code/license metadata inspection; no upstream imports, dataset generation or model execution')
    save(root/'manifest.json',manifest);results=[]
    for name,spec in SOURCES.items():
        for path in spec['files']:
            url=f'https://raw.githubusercontent.com/{spec["repo"]}/{spec["revision"]}/{path}'
            entry=dict(project=name,path=path,url=url)
            try:
                with urlopen(Request(url,headers={'User-Agent':'kv-pruning-source-audit'}),timeout=30) as response:
                    data=response.read(2_000_001)
                assert len(data)<=2_000_000,'Unexpectedly large source'
                dest=root/'upstream'/name/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
                entry.update(status='fetched',bytes=len(data),sha256=sha(data))
                if path.endswith('.py'):
                    try:ast.parse(data.decode('utf-8-sig'));entry['python_syntax']='parse_ok'
                    except SyntaxError as error:
                        entry.update(python_syntax='syntax_error',error_line=error.lineno,error_message=error.msg)
                if name=='orgaccess' and path=='evaluation.py':
                    source=data.decode('utf-8-sig')
                    role=source.index('"Senior_Software_Engineer"');next_role=source.index('"Finance_Intern"',role)
                    example=source[role:next_role]
                    entry['example_label_rationale_conflict']=('"expected_response": "full"' in example and "expected response is 'rejected'" in example)
                    entry['placeholder_predictions_present']='Placeholder predictions' in source
                if name=='accessdenied' and path=='scripts/grade.py':
                    entry['evaluates_extracted_answer_blocks']='extract_and_concatenate' in data.decode()
            except Exception as error:entry.update(status='fetch_failed',error_type=type(error).__name__,error_message=str(error))
            results.append(entry);save(root/'source_checks.json',results)
            print(name,path,entry['status'],entry.get('python_syntax',''),flush=True)
    manifest.update(status='complete',end_unix=time.time(),fetch_failures=sum(e['status']=='fetch_failed' for e in results))
    save(root/'manifest.json',manifest);print('COMPLETE_SOURCE_AUDIT',len(results),'files',manifest['fetch_failures'],'fetch failures',flush=True)


if __name__=='__main__':main()
