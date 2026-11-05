"""Independent stdlib Mistral Full trace, task scoring and support audit."""
import sys
sys.dont_write_bytecode=True
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
from verify_hf_DEV_acceptance import independent_score


def read(p):return json.loads(p.read_text())
def rows(p):return list(map(json.loads,p.read_text().splitlines()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return hashlib.sha256(json.dumps(x,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main():
    r=Path(__file__).resolve().parent.parent;assert str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning'
    d=r/'results/20261030-mistral-squad-full-v1';cfg=read(d/'proposal_snapshot.json');s=read(d/'summary.json')
    assert s['status']=='complete' and s['engineering_outputs']==6 and s['main_outputs']==12
    for name,h in read(d/'manifest.json').items():assert sha(d/name)==h,name
    for name,h in {**cfg['inputs'],**cfg['sources']}.items():assert sha(r/name)==h,name
    runtime=read(d/'actual_runtime.json');digest=canon(runtime);assert read(d/'execution_snapshot.json')['runtime_digest']==digest
    assert runtime['layer_count']==32 and runtime['KV_heads']==8 and runtime['head_dimension']==128 and runtime['bytes_per_slot']==131072
    assert runtime['model_config']['sliding_window'] is None and runtime['dtype']=='bfloat16' and runtime['attention_backend']=='sdpa'
    assert not runtime['tf32'] and not runtime['bf16_reduced_precision_reduction']
    mc=runtime['model_config'];assert 2*mc['num_hidden_layers']*mc['num_key_value_heads']*(mc['hidden_size']//mc['num_attention_heads'])*2==131072
    tok=[x for x in read(r/cfg['tokenized']) if x['model']=='Mistral'];engineering=[x for x in tok if x['split_role']=='engineering'][:2];dev=[x for x in tok if x['split_role']=='development'];cases={x['case_id']:x for x in engineering+dev}
    source={x['case_id']:x for x in rows(r/cfg['cases']) if x['case_id'] in cases}
    raw=rows(d/'raw_generations.jsonl');eng=rows(d/'engineering.jsonl');mainrows=rows(d/'generations.jsonl')
    assert len(raw)==18 and len(eng)==6 and len(mainrows)==12
    saved=eng+mainrows;seen=set();trace_steps=0
    for rr,row in zip(raw,saved):
        assert all(rr[k]==v for k,v in row.items() if k in rr)
        key=(row['case_id'],row['path']);assert key not in seen;seen.add(key)
        c=cases[row['case_id']];assert row['split_role']==c['split_role'] and row['condition']=='full' and row['runtime_digest']==digest
        assert row['prompt_sha256']==c['prompt_sha256'] and row['gold_sha256']==c['gold_sha256']
        ids=row['ids'];assert 0<len(ids)<=128 and row['truncated']==(ids[-1]!=2)
        n=c['prefix_tokens'];suffix=c['suffix_tokens'];assert row['prefix_tokens']==n and row['suffix_tokens']==suffix
        if row['path']=='native_whole':assert row['actual_prefix_kv_bytes'] is None and row['final_live_kv_bytes'] is None and row['trace'] is None
        else:
            assert row['actual_prefix_kv_bytes']==n*131072 and row['final_live_kv_bytes']==(n+suffix+len(ids)-1)*131072
            if row['path']=='custom_split':
                assert len(row['trace'])==len(ids);physical=n
                for i,t in enumerate(row['trace']):
                    width=suffix if i==0 else 1;logical=n if i==0 else n+suffix+i-1
                    assert t==dict(step=i,physical_start=physical,logical_start=logical,input_width=width);physical+=width;trace_steps+=1
            else:assert row['path']=='native_split' and row['trace'] is None
        assert row['metrics']==independent_score(row['text'],[a['text'] for a in source[c['case_id']]['answers']])
    for c in engineering:
        rr=[x for x in eng if x['case_id']==c['case_id']];assert {x['path'] for x in rr}=={'native_whole','native_split','custom_split'}
        assert all(x['ids']==rr[0]['ids'] and x['truncated']==rr[0]['truncated'] for x in rr)
        split=[x for x in rr if x['path']!='native_whole'];assert split[0]['reference_prefix_sha256']==split[1]['reference_prefix_sha256']
    assert all(x['token_and_termination_equal'] and x['reference_unmodified'] for x in read(d/'engineering_checks.json'))
    normalized=rows(d/'normalized_records.jsonl');report=read(d/'report.json');assert len(normalized)==12 and report['inference_performed'] and report['task_text_rescored']
    by={x['case_id']:x for x in mainrows};condition=report['conditions']['full'];complete=[x for x in mainrows if not x['truncated']]
    for row in normalized:
        prior=by[row['case_id']]
        for mn,field in [('task','em'),('constraint','format'),('f1','f1')]:assert row['metrics'][mn]['value']==prior['metrics'][field]
        assert row['comparison_digest']==digest and row['costs']['prefix_kv_bytes']['value']==prior['actual_prefix_kv_bytes']
    assert condition['execution']['ok']==12 and condition['execution']['truncated']==sum(x['truncated'] for x in mainrows)
    for mn,field in [('task','em'),('constraint','format'),('f1','f1')]:
        values=[x['metrics'][field] for x in complete if x['metrics'][field] is not None];m=condition['metrics'][mn]
        assert m['evaluated_count']==len(values) and m['unavailable_count']==12-len(values)
        if mn!='f1':assert m['pass_count']==sum(values)
        assert m['mean']==(sum(values)/len(values) if values else None)
    support=read(d/'Full_support.json');task=sum(x['metrics']['em'] is True for x in complete);fmt=sum(x['metrics']['format'] for x in complete);joint=sum(x['metrics']['joint_success'] for x in complete);trunc=sum(x['truncated'] for x in mainrows)
    gate=task>=6 and fmt>=9 and trunc<=1
    assert support['task_correct']==task and support['format_correct']==fmt and support['joint_delivered']==joint and support['truncated']==trunc and support['passed']==gate==s['Full_support']
    assert sum(len(x['ids']) for x in raw)==s['generated_tokens']
    # Independent stream pass of all3 shard SHA values and10 metadata official digests.
    official=read(r/cfg['official_spec']);directory=Path(cfg['model_path'])
    for entry in official['files']:
        p=directory/entry['rfilename'];assert p.stat().st_size==entry['size']
        if entry.get('lfs'):
            h=hashlib.sha256()
            with p.open('rb') as f:
                for chunk in iter(lambda:f.read(8388608),b''):h.update(chunk)
            assert h.hexdigest()==entry['lfs']['sha256']
        else:
            data=p.read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==entry['blobId']
    launch=read(Path(str(d)+'.launch.json'));assert launch['exit_code']==0 and not launch.get('watchdog_expired',False)
    for pid in [s['pid'],launch['launcher_pid']]:assert not Path('/proc/'+str(pid)).exists()
    gpu=subprocess.run(['nvidia-smi','-i',cfg['gpu_uuid'],'--query-gpu=uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15).stdout.strip()
    value=dict(status='passed',checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)),independent_scorer_source_sha256=sha(r/'scripts/verify_hf_DEV_acceptance.py'),engineering_answers=6,DEV_answers=12,generated_tokens=s['generated_tokens'],three_paths_equal_for_both_engineering_cases=True,trace_steps_independently_recomputed=trace_steps,independent_text_scores=18,model_metadata_files=10,weight_shards_rehashed=3,Full_support=gate,task_correct=task,format_correct=fmt,joint_delivered=joint,truncated=trunc,strict_task_evaluated=support['task_evaluated'],strict_format_evaluated=support['format_evaluated'],pinned_inputs_unchanged=len(cfg['inputs']),GPU_after=gpu,own_worker_and_launcher_exited=True,compact_or_sealed_outputs=0,independent_scientific_confirmation=False)
    p=d/'independent_verification.json';assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value),flush=True)


if __name__=='__main__':main()
