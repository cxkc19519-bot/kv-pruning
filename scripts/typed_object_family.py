"""Freeze a prospective small typed record family; no backend or old-case input."""
import hashlib
import json
from pathlib import Path
import sys


def freeze(out):
    out.mkdir(exist_ok=False)
    cases=[]
    for width in [1,2,4]:
        keys=[f'k{i:03d}' for i in range(width)]
        schema={'type':'object','properties':{k:{'type':'string','enum':['red','blue']} for k in keys},
                'required':keys,'additionalProperties':False}
        good={k:'red' for k in keys}
        variants=[('all_red',good),('alternating',{k:('blue' if i%2==0 else 'red') for i,k in enumerate(keys)}),
                  ('missing_key',{k:v for k,v in good.items() if k!=keys[-1]}),
                  ('extra_key',dict(good,extra='red')),('wrong_enum',dict(good,**{keys[0]:'green'})),
                  ('wrong_value_type',dict(good,**{keys[0]:0})),('wrong_root_type',[])]
        def predicate(value):
            return type(value) is dict and set(value)==set(keys) and all(type(v) is str and v in ['red','blue'] for v in value.values())
        tests=[dict(description=name,data=value,valid=predicate(value)) for name,value in variants]
        assert [t['valid'] for t in tests]==[True,True,False,False,False,False,False]
        cases.append(dict(case_id=f'typed-record-w{width}',schema=schema,tests=tests))
    selection=dict(id='typed-object-enum-v1',widths=[1,2,4],cases=cases,
                   purpose='Correctness of fixed-field categorical records; not a resource stress or fullJSONSchema claim.')
    raw=[json.dumps(c,ensure_ascii=True,sort_keys=True,separators=(',',':')) for c in cases]
    plan=[]
    for backend in ['xgrammar','llguidance']:
        for c in cases:
            for i,t in enumerate(c['tests']):
                text=json.dumps(t['data'],ensure_ascii=True,sort_keys=True,separators=(',',':'))
                plan.append(dict(backend=backend,case_id=c['case_id'],test_index=i,expected=t['valid'],serialized=text,tokens=list(text.encode())+[133]))
    positions=sum(len(t['tokens']) for t in plan)
    values={'selection.json':selection,'raw-groups.json':raw,'planned-instances.json':plan,
            'bounds.json':dict(instances=42,groups=6,mask_positions_cap=positions,mask_api_calls_cap=3*positions//2,
                               native_calls_cap=6*positions+400,old_results_read=False,resource_experiment=False)}
    for name,obj in values.items():
        (out/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
    (out/'source_generator.py').write_bytes(Path(__file__).read_bytes())
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
    (out/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},bounds=values['bounds.json'])))


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    target=(root/sys.argv[1]).resolve()
    assert target.is_relative_to(root/'literature')
    freeze(target)
