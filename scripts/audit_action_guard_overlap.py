"""Check the fixed cohort against public guard training prompts, without inference."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import time
import traceback

from fetch_pinned_model import verify


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')


def norm(text):
    return re.sub(r'\s+',' ',text).strip().casefold()


def main():
    p=argparse.ArgumentParser()
    for key in ['cpu-run','training-run','training-dir','out']:p.add_argument('--'+key,required=True)
    args=p.parse_args();root=Path(args.out);root.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).read_bytes();(root/'source.py').write_bytes(source)
    m=dict(status='running',start_unix=time.time(),args=vars(args),rows=0,new_model_outputs=0,
           source_sha256=sha(source),model_executed=False)
    save(root/'manifest.json',m)
    try:
        cpu=Path(args.cpu_run);summary=json.loads((cpu/'summary.json').read_text())
        assert summary['cpu_gate'] is True
        raw_cases=(cpu/'provisional_cases.jsonl').read_bytes()
        assert sha(raw_cases)==summary['input_case_sha256']
        cases=[json.loads(l) for l in raw_cases.splitlines()]
        tr=Path(args.training_run);tm=json.loads((tr/'manifest.json').read_text());assert tm['status']=='complete'
        spec=json.loads((tr/'spec.json').read_text());td=Path(args.training_dir)
        inputs=[];counts={}
        for entry in spec['files']:
            path=td/entry['rfilename'];assert verify(path,entry)
            if not path.name.endswith('.jsonl'):continue
            rows=[json.loads(l) for l in path.read_text().splitlines()]
            counts[entry['rfilename']]=len(rows)
            for i,row in enumerate(rows):
                if 'instruction' in row:
                    texts=[row['instruction']]
                else:
                    texts=[x['value'] for x in row['conversations'] if x['from']=='human']
                for text in texts:inputs.append(dict(source=entry['rfilename'],row=i,text=text,normalized=norm(text)))
        assert sum(counts.values())==7000
        exact={sha(x['text'].encode()) for x in inputs}
        normalized={sha(x['normalized'].encode()) for x in inputs}
        checks=[]
        for case in cases:
            rendered=case['rendered']['full'];raw=case['raw_source']
            prompt=rendered['prompt']
            fields=[norm(raw['instruction']),norm(rendered['history_text']),norm(rendered['current_action_text'])]
            raw_fields=[norm(raw['instruction']),norm(raw['history']),norm(raw['current_action'])]
            assert all(len(s)>20 for s in fields) and all(len(s)>20 for s in raw_fields)
            hits=[dict(source=x['source'],row=x['row']) for x in inputs
                  if all(s in x['normalized'] for s in fields) or all(s in x['normalized'] for s in raw_fields)]
            checks.append(dict(key=case['key'],exact_full_prompt=sha(prompt.encode()) in exact,
                               normalized_full_prompt=sha(norm(prompt).encode()) in normalized,
                               complete_three_field_hits=hits))
        overlap=sum(r['exact_full_prompt'] or r['normalized_full_prompt'] or bool(r['complete_three_field_hits']) for r in checks)
        gate=overlap==0
        result=dict(public_training_rows=counts,training_human_inputs=len(inputs),cohort_n=len(cases),
                    cases_with_exact_or_complete_field_overlap=overlap,overlap_gate=gate,
                    model_execution_enabled=False,checks=checks,
                    caveats=['Only released SFT/RL inputs were scanned, not pretraining or any undisclosed data.',
                             'No exact match does not prove semantic independence or absence of template/tool overlap.',
                             'Native serializer and benchmark versions remain explicit; this is a development cohort, not a publication test set.'])
        save(root/'summary.json',result)
        if gate:(root/'frozen_cases.jsonl').write_bytes(raw_cases)
        m.update(status='complete',end_unix=time.time(),overlap_gate=gate,case_sha256=sha(raw_cases),
                 cpu_manifest_sha256=sha((cpu/'manifest.json').read_bytes()),
                 training_manifest_sha256=sha((tr/'manifest.json').read_bytes()))
    except Exception as error:
        m.update(status='failed',end_unix=time.time(),error_type=type(error).__name__,error_message=str(error),traceback=traceback.format_exc());raise
    finally:save(root/'manifest.json',m)
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
