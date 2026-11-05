"""Independent stdlib audit of actual DEV text scoring, traces and full60cell report."""
import sys
sys.dont_write_bytecode=True
import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import string
from decimal import Decimal
from fractions import Fraction
from collections import Counter
import subprocess


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return hashlib.sha256(json.dumps(x,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def rows(p):return list(map(json.loads,p.read_text().splitlines()))
def save(p,x):
    assert not p.exists(),p
    p.write_text(json.dumps(x,ensure_ascii=True,indent=2,allow_nan=False)+'\n')


class BadJSON(ValueError):pass


def independent_score(text,golds):
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:raise BadJSON('duplicate_key')
            d[k]=v
        return d
    def finite(x):raise BadJSON('nonfinite_constant')
    def unicode_check(x):
        if isinstance(x,str):
            try:x.encode('utf-8')
            except UnicodeEncodeError:raise BadJSON('invalid_unicode')
        elif isinstance(x,dict):
            for k,v in x.items():unicode_check(k);unicode_check(v)
        elif isinstance(x,list):
            for v in x:unicode_check(v)
    stripped=text.strip(' \t\r\n');candidate=None;good=False
    try:
        unicode_check(text)
        if text.lstrip(' \t\r\n').startswith('\ufeff'):raise BadJSON('bom')
        value=json.loads(text,object_pairs_hook=unique,parse_constant=finite,parse_float=Decimal);unicode_check(value)
    except BadJSON as e:reason=str(e)
    except json.JSONDecodeError:
        if stripped.startswith(('{','[','"','```')):reason='structured_parse_failure'
        else:candidate=stripped;reason='whole_plain_text'
    else:
        if isinstance(value,dict):
            if not isinstance(value.get('answer'),str):reason='no_string_answer'
            else:candidate=value['answer'];good=set(value)=={'answer'} and bool(candidate.strip());reason='object_answer'
        elif isinstance(value,str):candidate=value;reason='json_string'
        elif isinstance(value,list):reason='unsupported_json_root'
        else:candidate=stripped;reason='json_scalar_as_plain_text'
    def normalize(s):return ' '.join(re.sub(r'\b(a|an|the)\b',' ',''.join(c for c in s.lower() if c not in string.punctuation)).split())
    if candidate is None:em=f1=None
    else:
        p=normalize(candidate);pt=p.split();em=False;f1=0.0
        for g in golds:
            n=normalize(g);gt=n.split();em=em or p==n
            common=sum((Counter(pt)&Counter(gt)).values());f1=max(f1,2*common/(len(pt)+len(gt)) if common else 0.0)
    return dict(format=good,candidate=candidate,reason=reason,em=em,f1=f1,candidate_status='unavailable' if candidate is None else 'available',joint_success=bool(good and em))


def main():
    r=Path(__file__).resolve().parent.parent;assert str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning'
    d=r/'results/20261030-hf-DEV-acceptance-v2';cfg=read(d/'proposal_snapshot.json');s=read(d/'summary.json')
    assert s['status']=='complete' and s['main_outputs']==s['raw_outputs']==36 and s['engineering_outputs']==0 and s['blocked_cells']==24
    for n,h in read(d/'manifest.json').items():assert sha(d/n)==h,n
    for n,h in {**cfg['inputs'],**cfg['execution_sources']}.items():assert sha(r/n)==h,n
    checkpoint=r/cfg['engineering_checkpoint'];descriptor=read(d/'backend_execution_snapshot.json')
    for n,h in descriptor['source_files'].items():assert sha(r/n)==h,n
    scope=read(d/'execution_scope.json');assert canon(scope['material'])==scope['execution_protocol_digest']
    assert scope['material']['proposal_sha256']==sha(d/'proposal_snapshot.json')
    runtime=cfg['generator_runtime_digest'];assert scope['material']['generator_runtime_digest']==runtime==read(checkpoint/'registered_runtime_scope.json')['runtime_digest']
    assert read(d/'restored_engineering_evidence.json')==read(checkpoint/'engineering_evidence.json')
    assert len(read(d/'resume_software_acceptance.json'))==8 and all(x['passed'] and x['model_calls']==0 for x in read(d/'resume_software_acceptance.json'))
    assert read(d/'config_JSON_comparison.json')['entire_config_JSON_equal'] is True
    assert read(d/'actual_runtime.json')['observed']==read(checkpoint/'actual_runtime.json')['observed']
    source={x['case_id']:x for x in rows(r/cfg['cases'])};cases={x['case_id']:dict(x,context_group_id=source[x['case_id']]['context_group_id']) for x in read(r/cfg['tokenized'])}
    specs={x['condition_id']:x for x in read(r/cfg['specs'])['specs']};plan=read(d/'admission_plan.json');dispatch=rows(d/'dispatch_log.jsonl')
    raw=rows(d/'raw_generations.jsonl');scored=rows(d/'scored_generations.jsonl');records=rows(d/'normalized_records.jsonl')
    assert len(plan)==len(dispatch)==len(records)==60 and len(raw)==len(scored)==36
    attempts=rows(d/'model_attempts.jsonl');assert attempts==[x['request'] for x in raw]
    byraw={(x['request']['case_id'],x['request']['condition_id']):x for x in raw};byscored={(x['case_id'],x['condition']):x for x in scored}
    byrec={(x['case_id'],x['condition_id']):x for x in records};assert len(byraw)==len(byscored)==36 and len(byrec)==60
    old={}
    for p in cfg['old_DEV_generations']:
        for x in rows(r/p):
            if x['status']=='ok' and not x['condition'].endswith('_system_pinned'):old[(x['case_id'],x['condition'])]=x
    states=Counter();trace_steps=0
    for p,log in zip(plan,dispatch):
        req=p['request'];cid=req['case_id'];name=req['condition_id'];c=cases[cid];sp=specs[name];key=(cid,name);rec=byrec[key]
        assert c['split_role']==req['phase']=='development' and log['decision']==p
        assert canon({k:v for k,v in req.items() if k!='request_digest'})==req['request_digest']
        assert req['case_input_digest']==canon({k:c[k] for k in ['case_id','split_role','input_ids','prefix_tokens','header_ids','prompt_sha256','context_group_id']})
        assert req['runtime_digest']==runtime and req['condition_fingerprint']==canon(dict(version='condition_admission_v1',runtime_digest=runtime,condition=sp))
        n=c['prefix_tokens'];ratio=Fraction(sp['retention']);slots=n*ratio.numerator//ratio.denominator
        required=set(range(min(4,n)))|set(range(max(0,n-64),n))|(set(c['header_ids']) if sp['protect_system'] else set())
        expected='blocked_budget' if len(required)>slots else 'blocked_engineering_unverified' if sp['protect_system'] else 'eligible_for_configured_run'
        assert p['decision']['admission_state']==expected;states[expected]+=1
        assert rec['input_digest']==c['prompt_sha256'] and rec['gold_digest']==source[cid]['gold_sha256']
        if expected!='eligible_for_configured_run':
            assert log['state']=='blocked' and not log['model_called'] and key not in byraw
            assert rec['execution_state']==('infeasible_budget' if expected=='blocked_budget' else 'not_run')
            assert all(x['value'] is None for x in rec['metrics'].values());continue
        assert log['state']=='executed' and log['model_called'] and log['result']==byraw[key]['result']
        result=log['result'];prior=old[key];sc=byscored[key]
        assert result['request_digest']==req['request_digest'] and result['ids']==sc['ids']==prior['ids']
        assert result['truncated']==sc['truncated']==prior['truncated'] and result['trace']==prior['trace']
        assert sc['text']==prior['text'];m=independent_score(sc['text'],[x['text'] for x in source[cid]['answers']])
        assert m==sc['metrics']==prior['metrics']
        for mn,field in [('task','em'),('constraint','format'),('f1','f1')]:assert rec['metrics'][mn]['value']==m[field]
        assert result['actual_prefix_kv_bytes']==rec['costs']['prefix_kv_bytes']['value']==slots*57344
        physical=slots;suffix=len(c['input_ids'])-n
        assert len(result['trace'])==len(result['ids'])
        for i,t in enumerate(result['trace']):
            width=suffix if i==0 else 1;logical=n if i==0 else n+suffix+i-1
            assert t==dict(step=i,physical_start=physical,logical_start=logical,input_width=width);physical+=width;trace_steps+=1
        assert result['final_live_kv_bytes']==physical*57344==rec['costs']['final_live_kv_bytes']['value']
    assert states=={'eligible_for_configured_run':36,'blocked_budget':20,'blocked_engineering_unverified':4}
    assert sum(len(x['result']['ids']) for x in raw)==s['generated_tokens']
    mapping_heads=snap_rankings=0;olddir=r/'results/20261030-independent-squad-compression-v1';oldmanifest=read(olddir/'manifest.json')
    for cid,c in cases.items():
        if c['split_role']!='development':continue
        n=c['prefix_tokens'];required=set(range(min(4,n)))|set(range(max(0,n-64),n))
        scores=json.loads(gzip.decompress((d/(cid+'.scores.json.gz')).read_bytes()))
        for suffix in ('.scores.json.gz','.maps.json.gz'):assert sha(olddir/(cid+suffix))==oldmanifest[cid+suffix]
        assert scores==json.loads(gzip.decompress((olddir/(cid+'.scores.json.gz')).read_bytes()))
        oldmaps=json.loads(gzip.decompress((olddir/(cid+'.maps.json.gz')).read_bytes()))
        for name in ['adapted_snapkv','uniform_random']:
            maps=json.loads(gzip.decompress((d/(cid+'.'+name+'.maps.json.gz')).read_bytes()));assert maps==oldmaps[name]
            for layer,batches in maps.items():
                assert len(batches)==1 and len(batches[0])==4
                for head,indices in enumerate(batches[0]):
                    assert indices==sorted(set(indices)) and len(indices)==n//2 and required<=set(indices) and all(0<=i<n for i in indices);mapping_heads+=1
                    if name=='adapted_snapkv':
                        values=scores[layer][0][head];free=[i for i in range(n) if i not in required];top=sorted(free,key=lambda i:(-values[i],i))[:n//2-len(required)]
                        assert indices==sorted(required|set(top));snap_rankings+=1
    report=read(d/'report.json');paired=report['paired'];dev=[cid for cid,c in cases.items() if c['split_role']=='development']
    assert len(dev)==12 and len(paired['cells'])==60 and paired['inference_performed'] and paired['task_text_rescored']
    def available(row,m):return row['execution_state']=='ok' and not row['truncated'] and row['metrics'][m]['value'] is not None
    def equal(a,b):assert (a is None and b is None) or (a is not None and b is not None and math.isclose(a,b,abs_tol=1e-12)),(a,b)
    compact={}
    for name,cr in paired['conditions'].items():
        selected=[byrec[(cid,name)] for cid in dev];execution=cr['execution']
        assert execution['scheduled']==12
        for status in ['ok','error','not_run','infeasible_budget']:assert execution[status]==sum(x['execution_state']==status for x in selected)
        assert execution['truncated']==sum(x['execution_state']=='ok' and x['truncated'] for x in selected)
        for metric_name,m in cr['metrics'].items():
            vals=[x['metrics'][metric_name]['value'] for x in selected if available(x,metric_name)]
            assert m['evaluated_count']==len(vals) and m['unavailable_count']==12-len(vals);equal(m['mean'],sum(vals)/len(vals) if vals else None)
            if metric_name!='f1':assert m['pass_count']==sum(vals)
            if name=='full':continue
            trans=Counter();deltas=[];D=eligible=unknown=0
            for cid,x in zip(dev,selected):
                b=byrec[(cid,'full')];ba=available(b,metric_name);xa=available(x,metric_name)
                if metric_name!='f1' and ba and b['metrics'][metric_name]['value']:
                    D+=1;eligible+=int(xa);unknown+=int(not xa)
                if not(ba and xa):continue
                a,z=b['metrics'][metric_name]['value'],x['metrics'][metric_name]['value'];deltas.append(float(z)-float(a))
                if metric_name!='f1':trans[('C' if a else 'W')+'2'+('C' if z else 'W')]+=1
            assert m['paired_count']==len(deltas) and m['unavailable_pair_count']==12-len(deltas);equal(m['mean_paired_delta'],sum(deltas)/len(deltas) if deltas else None)
            if metric_name!='f1':
                assert m['transitions']=={k:trans[k] for k in ['C2C','C2W','W2C','W2W']}
                assert (m['available_Full_pass_count'],m['eligible_Full_pass_pair_count'],m['unassessed_Full_pass_count'])==(D,eligible,unknown)
                equal(m['strict_conditional_damage'],trans['C2W']/eligible if eligible else None)
                assert m['all_Full_pass_damage_bounds']==([trans['C2W']/D,(trans['C2W']+unknown)/D] if D else None)
        joint=sum(x['execution_state']=='ok' and not x['truncated'] and byscored[(x['case_id'],name)]['metrics']['joint_success'] for x in selected)
        assert report['delivery'][name]['joint_delivered']==joint
        compact[name]=dict(generated=execution['ok'],budget_blocked=execution['infeasible_budget'],not_run=execution['not_run'],truncated=execution['truncated'],task_pass=cr['metrics']['task']['pass_count'],task_evaluated=cr['metrics']['task']['evaluated_count'],format_pass=cr['metrics']['constraint']['pass_count'],format_evaluated=cr['metrics']['constraint']['evaluated_count'],joint_delivered=joint)
    for pid in [s['pid'],read(Path(str(d)+'.launch.json'))['launcher_pid']]:assert not Path('/proc/'+str(pid)).exists()
    gpu=subprocess.run(['nvidia-smi','-i',descriptor['gpu_uuid'],'--query-gpu=uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15).stdout.strip()
    value=dict(status='passed',checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)),pinned_inputs_unchanged=len(cfg['inputs']),same_generator_runtime=True,checkpoint_evidence_restored_without_calls=14,resume_software_cases_passed=8,actual_DEV_answers=36,new_engineering_answers=0,generated_tokens=s['generated_tokens'],all36_tokens_trace_text_metrics_match_old=True,independent_text_scores=36,independent_trace_steps=trace_steps,unique_layer_head_maps=mapping_heads,independent_Snap_rankings=snap_rankings,all60_normalized_cells_and_metrics_recomputed=True,admission=dict(states),condition_results=compact,own_worker_and_launcher_exited=True,gpu_after_raw=gpu,independent_scientific_confirmation=False)
    save(d/'independent_verification.json',value);print(json.dumps(value),flush=True)


if __name__=='__main__':main()
