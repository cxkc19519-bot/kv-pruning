"""Pinned Mistral QA Full-only engineering/support run, no compression."""
import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',PYTHONDONTWRITEBYTECODE='1')
import sys
sys.dont_write_bytecode=True
import argparse
import copy
import gc
import hashlib
import importlib.metadata
import json
from pathlib import Path
import signal
import subprocess
import time
import traceback
from reliability_system_core import require,metric,measure,SCHEMA,summarize
from reliability_system_adapters import hash_json
from answer_format_task import score_response


def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=True,allow_nan=False,indent=2)+'\n')
def append(p,x):
    with p.open('a') as f:f.write(json.dumps(x,ensure_ascii=True,allow_nan=False)+'\n')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--proposal-sha256',required=True);a=ap.parse_args()
    r=Path(__file__).resolve().parent.parent;require(a.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning','server_only')
    raw=(r/'configs/mistral-squad-full-v1.json').read_bytes();require(sha(raw)==a.proposal_sha256,'proposal_pin');cfg=json.loads(raw);out=r/cfg['run']
    require(out.resolve().parent==(r/'results').resolve(),'run_boundary');out.mkdir(exist_ok=False)
    start=time.monotonic();active=None;model=None;torch=None;reference=None
    state=dict(status='running',stage='pins',pid=os.getpid(),main_outputs=0,engineering_outputs=0,generated_tokens=0,engineering_gate=None,Full_support=None)
    def timeout(*args):raise TimeoutError('Full600_second_cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(cfg['wall_seconds'])
    try:
        save(out/'summary.json',state);(out/'proposal_snapshot.json').write_bytes(raw)
        require(os.environ.get('KV_MISTRAL_FULL_WATCHDOG')=='registered_660_seconds','watchdog_required')
        require(os.environ.get('CUDA_VISIBLE_DEVICES')==cfg['gpu_uuid'],'GPU_UUID')
        for name,h in {**cfg['inputs'],**cfg['sources']}.items():
            b=(r/name).read_bytes();require(sha(b)==h,'pin:'+name)
            if name.startswith('scripts/'):(out/('source_'+Path(name).name)).write_bytes(b)
        save(out/'input_manifest.json',cfg['inputs'])
        versions={k:importlib.metadata.version(k) for k in cfg['versions']};require(versions==cfg['versions'],'versions')
        gpu=subprocess.run(['nvidia-smi','-i',cfg['gpu_uuid'],'--query-gpu=uuid,name,memory.used,memory.total,utilization.gpu,driver_version','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15).stdout.strip()
        fields=[s.strip() for s in gpu.split(',')];require(int(fields[2])<=128 and int(fields[4])==0,'selected_GPU_busy');save(out/'gpu_before.json',dict(raw=gpu,other_processes_manipulated=False))
        directory=Path(cfg['model_path']);require(directory.name==cfg['model_revision'],'revision')
        spec=json.loads((r/cfg['official_spec']).read_text());proof={};state['stage']='weight_hashes';save(out/'summary.json',state)
        for entry in spec['files']:
            name=entry['rfilename'];p=directory/name;require(p.stat().st_size==entry['size'],'model_file_size:'+name)
            if name in spec['metadata_files']:
                b=p.read_bytes();digest=sha(b) if entry.get('lfs') else hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
                require(sha(b)==cfg['model_metadata_sha256'][name],'metadata_SHA:'+name)
            else:
                h=hashlib.sha256()
                with p.open('rb') as f:
                    for b in iter(lambda:f.read(8388608),b''):h.update(b)
                digest=h.hexdigest()
            expected=entry['lfs']['sha256'] if entry.get('lfs') else entry['blobId'];require(digest==expected,'official_model_digest:'+name)
            proof[name]=dict(bytes=entry['size'],official_digest=digest,algorithm='sha256' if entry.get('lfs') else 'git_blob_sha1')
        save(out/'model_file_verification.json',proof)
        allrows=json.loads((r/cfg['tokenized']).read_text());allrows=[x for x in allrows if x['model']=='Mistral']
        engineering=[x for x in allrows if x['split_role']=='engineering'][:2];dev=[x for x in allrows if x['split_role']=='development']
        require([x['case_id'] for x in engineering]==cfg['engineering_case_ids'] and len(dev)==12,'original_engineering_and_DEV')
        cases=engineering+dev;source={x['case_id']:x for x in map(json.loads,(r/cfg['cases']).read_text().splitlines()) if x['case_id'] in {c['case_id'] for c in cases}}
        require(len(source)==14 and all(c['split_role'] in ['engineering','development'] for c in cases),'no_sealed_inputs')
        import torch as torch_module
        torch=torch_module
        from transformers import AutoTokenizer,AutoModelForCausalLM,DynamicCache,GenerationConfig
        tok=AutoTokenizer.from_pretrained(str(directory),local_files_only=True,trust_remote_code=False,use_fast=True)
        for c in cases:
            original=source[c['case_id']];require(original['prompt_sha256']==c['prompt_sha256'] and original['gold_sha256']==c['gold_sha256'],'source_identity')
            ids=tok.apply_chat_template([dict(role='system',content=original['prompt']['system']),dict(role='user',content=original['prompt']['user'])],tokenize=True,add_generation_prompt=True)
            require(ids==c['input_ids'],'native_ids_changed')
        save(out/'input_bindings.json',[dict(case_id=c['case_id'],role=c['split_role'],input_sha256=hash_json(c['input_ids']),prefix_tokens=c['prefix_tokens'],prompt_sha256=c['prompt_sha256'],gold_sha256=c['gold_sha256']) for c in cases])
        torch.set_num_threads(4);torch.manual_seed(cfg['torch_seed']);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=False
        state['stage']='load_model';save(out/'summary.json',state)
        model=AutoModelForCausalLM.from_pretrained(str(directory),torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True,trust_remote_code=False).eval().to('cuda:0')
        mc=model.config
        require(mc.model_type=='mistral' and len(model.model.layers)==32 and mc.num_key_value_heads==8 and mc.num_attention_heads==32 and mc.hidden_size//mc.num_attention_heads==128 and mc.sliding_window is None,'actual_Mistral_layout')
        require(all(layer.self_attn.config.sliding_window is None for layer in model.model.layers),'actual_all_layers_Full')
        require(mc._attn_implementation=='sdpa' and all(p.dtype==torch.bfloat16 for p in model.parameters()),'actual_BF16_SDPA')
        decode=GenerationConfig(**cfg['decode']);model.generation_config=copy.deepcopy(decode);eos=set(decode.eos_token_id if isinstance(decode.eos_token_id,list) else [decode.eos_token_id])
        runtime=dict(model_path=str(directory),model_revision=cfg['model_revision'],model_config=mc.to_dict(),versions=versions,decode=decode.to_dict(),layer_count=32,KV_heads=8,head_dimension=128,dtype='bfloat16',attention_backend='sdpa',bytes_per_slot=131072,tf32=False,bf16_reduced_precision_reduction=False,GPU=cfg['gpu_uuid'],python=sys.version)
        save(out/'actual_runtime.json',runtime);runtime_digest=hash_json(runtime)
        save(out/'execution_snapshot.json',dict(proposal_sha256=sha(raw),source_sha256=cfg['sources'],runtime_digest=runtime_digest,engineering_max=6,DEV_max=12,compact_or_protected=False,sealed_inference=False))
        def kvbytes(cache):return sum(t.numel()*t.element_size() for l in cache.layers for t in (l.keys,l.values))
        def cachehash(cache):
            h=hashlib.sha256()
            for l in cache.layers:
                for t in (l.keys,l.values):h.update(t.contiguous().view(torch.uint8).cpu().numpy().tobytes())
            return h.hexdigest()
        def validate_cache(cache,n):
            require(len(cache.layers)==32 and kvbytes(cache)==n*131072,'actual_KV_bytes')
            require(all(tuple(l.keys.shape)==tuple(l.values.shape)==(1,8,n,128) and l.keys.dtype==l.values.dtype==torch.bfloat16 for l in cache.layers),'actual_KV_shape_dtype')
        @torch.inference_mode()
        def prefill(ids):
            cache=DynamicCache();x=torch.tensor([ids],device=model.device);cp=torch.arange(len(ids),device=model.device)
            model.model(input_ids=x,past_key_values=cache,use_cache=True,position_ids=cp[None,:],cache_position=cp)
            validate_cache(cache,len(ids));return cache
        @torch.inference_mode()
        def clone(ref):
            branch=DynamicCache()
            for i,l in enumerate(ref.layers):
                keys,values=l.keys.clone(),l.values.clone();require(keys.data_ptr()!=l.keys.data_ptr() and values.data_ptr()!=l.values.data_ptr() and torch.equal(keys,l.keys) and torch.equal(values,l.values),'clone_not_exact_independent');branch.update(keys,values,i)
            require(kvbytes(branch)==kvbytes(ref),'clone_bytes');return branch
        @torch.inference_mode()
        def native(ids,cache=None,n=0):
            x=torch.tensor([ids],device=model.device);kwargs={}
            if cache is not None:kwargs=dict(past_key_values=cache,cache_position=torch.arange(n,n+len(ids),device=model.device))
            output=model.generate(input_ids=x,attention_mask=torch.ones((1,n+len(ids)),device=model.device,dtype=torch.long),generation_config=decode,logits_to_keep=1,**kwargs)
            return output[0,len(ids):].tolist(),None
        @torch.inference_mode()
        def custom(cache,n,suffix):
            x=torch.tensor([suffix],device=model.device);ids=[];trace=[]
            for step in range(128):
                physical=cache.get_seq_length();logical=n if step==0 else n+len(suffix)+step-1;require(physical==logical,'Full_physical_logical_mismatch');width=x.shape[1];cp=torch.arange(physical,physical+width,device=model.device)
                output=model(input_ids=x,past_key_values=cache,use_cache=True,position_ids=cp[None,:],cache_position=cp,logits_to_keep=1)
                token=int(output.logits[0,-1].argmax());del output;ids.append(token);trace.append(dict(step=step,physical_start=physical,logical_start=logical,input_width=width))
                require(cache.get_seq_length()==physical+width,'cache_update_width')
                if token in eos:break
                x=torch.tensor([[token]],device=model.device)
            return ids,trace
        engineering_rows=[];main_rows=[];checks=[];normalized=[]
        def emit(c,path,ids,trace,branch,reference_hash,eng):
            row=dict(case_id=c['case_id'],split_role=c['split_role'],condition='full',path=path,status='ok',ids=ids,truncated=not(ids and ids[-1] in eos),trace=trace,prefix_tokens=c['prefix_tokens'],suffix_tokens=c['suffix_tokens'],actual_prefix_kv_bytes=c['prefix_tokens']*131072 if branch is not None else None,final_live_kv_bytes=kvbytes(branch) if branch is not None else None,reference_prefix_sha256=reference_hash,prompt_sha256=c['prompt_sha256'],gold_sha256=c['gold_sha256'],runtime_digest=runtime_digest)
            append(out/'raw_generations.jsonl',row);state['engineering_outputs' if eng else 'main_outputs']+=1;state['generated_tokens']+=len(ids);save(out/'summary.json',state)
            require(ids and len(ids)<=128 and state['engineering_outputs']<=6 and state['main_outputs']<=12 and state['generated_tokens']<=2304,'answer_token_cap')
            if branch is not None:validate_cache(branch,c['prefix_tokens']+c['suffix_tokens']+len(ids)-1)
            row['text']=tok.decode(ids[:-1] if ids[-1] in eos else ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
            row['raw_with_terminal']=tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
            row['metrics']=score_response(row['text'],[a['text'] for a in source[c['case_id']]['answers']])
            append(out/('engineering.jsonl' if eng else 'generations.jsonl'),row);(engineering_rows if eng else main_rows).append(row);return row
        state['stage']='three_path_engineering';save(out/'summary.json',state)
        for c in engineering:
            n=c['prefix_tokens'];suffix=c['input_ids'][n:]
            active=dict(case_id=c['case_id'],phase='engineering',path='native_whole');ids,tr=native(c['input_ids']);a=emit(c,'native_whole',ids,tr,None,None,True)
            reference=prefill(c['input_ids'][:n]);before=cachehash(reference);branch=clone(reference)
            active=dict(case_id=c['case_id'],phase='engineering',path='native_split');ids,tr=native(suffix,branch,n);b=emit(c,'native_split',ids,tr,branch,before,True);require(cachehash(reference)==before,'native_reference_mutated');del branch
            branch=clone(reference);active=dict(case_id=c['case_id'],phase='engineering',path='custom_split');ids,tr=custom(branch,n,suffix);cc=emit(c,'custom_split',ids,tr,branch,before,True)
            exact=a['ids']==b['ids']==cc['ids'] and a['truncated']==b['truncated']==cc['truncated'];unchanged=cachehash(reference)==before
            checks.append(dict(case_id=c['case_id'],token_and_termination_equal=exact,reference_unmodified=unchanged,bytes_per_slot=131072,reference_sha256=before));save(out/'engineering_checks.json',checks)
            require(exact and unchanged,'three_path_mismatch');del branch;reference=None;gc.collect();active=None
        state['engineering_gate']=True;state['stage']='Full_DEV';save(out/'summary.json',state)
        for c in dev:
            active=dict(case_id=c['case_id'],phase='development',path='custom_split');n=c['prefix_tokens'];reference=prefill(c['input_ids'][:n]);before=cachehash(reference);branch=clone(reference);ids,tr=custom(branch,n,c['input_ids'][n:]);row=emit(c,'custom_split',ids,tr,branch,before,False)
            require(cachehash(reference)==before,'DEV_reference_mutated');m=row['metrics']
            norm=dict(schema=SCHEMA,cohort_id='Mistral_SQuADtrain_Full_DEV12',case_id=c['case_id'],condition_id='full',execution_state='ok',truncated=row['truncated'],reason=None,input_digest=c['prompt_sha256'],gold_digest=c['gold_sha256'],comparison_digest=runtime_digest,metrics=dict(task=metric(m['em'],'squad_v11_bidaf_pinned_em_v1',reason=m['reason']),constraint=metric(m['format'],'json_answer_format_v1'),f1=metric(m['f1'],'squad_v11_bidaf_pinned_f1_v1','unit_interval',m['reason'])),costs=dict(prefix_kv_bytes=measure(row['actual_prefix_kv_bytes']),final_live_kv_bytes=measure(row['final_live_kv_bytes']),peak_gpu_bytes=measure(None,'not_benchmarked'),latency_ms=measure(None,'not_benchmarked')),origin=cfg['run'])
            normalized.append(norm);append(out/'normalized_records.jsonl',norm);del branch;reference=None;gc.collect();active=None
        plan=dict(cohort_id='Mistral_SQuADtrain_Full_DEV12',case_ids=[c['case_id'] for c in dev],conditions=[dict(condition_id='full',budget_group=None)],metrics={k:dict(kind=v['kind'],metric_id=v['metric_id']) for k,v in normalized[0]['metrics'].items()},scientific_role='second_model_same12DEV_Full_support_not_independent_context_confirmation',context_group_ids=[c['context_group_id'] for c in dev])
        report=summarize(plan,normalized);report.update(inference_performed=True,task_text_rescored=True);save(out/'plan.json',plan);save(out/'report.json',report)
        valid=[x for x in main_rows if not x['truncated']];task=sum(x['metrics']['em'] is True for x in valid);fmt=sum(x['metrics']['format'] is True for x in valid);joint=sum(x['metrics']['joint_success'] for x in valid);truncated=sum(x['truncated'] for x in main_rows)
        gate=task>=cfg['Full_support']['task_min'] and fmt>=cfg['Full_support']['format_min'] and truncated<=cfg['Full_support']['truncated_max'] and len(main_rows)==12
        save(out/'Full_support.json',dict(passed=gate,task_correct=task,task_evaluated=sum(x['metrics']['em'] is not None for x in valid),format_correct=fmt,format_evaluated=len(valid),joint_delivered=joint,truncated=truncated,errors=0,scheduled=12,thresholds=cfg['Full_support'],scope='Task adaptation support only;not protection/compact/independent confirmation'))
        for name,h in {**cfg['inputs'],**cfg['sources']}.items():require(sha((r/name).read_bytes())==h,'input_changed:'+name)
        state.update(status='complete',stage='complete',Full_support=gate,task_correct=task,format_correct=fmt,joint_delivered=joint,truncated=truncated,scientific_confirmation=False,compact_or_sealed_generated=False)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc),active_request=active);(out/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0);reference=None;model=None;gc.collect()
        if torch is not None:torch.cuda.empty_cache()
        state['elapsed_seconds']=time.monotonic()-start;save(out/'summary.json',state);files=[p for p in out.iterdir() if p.is_file()]
        if len(files)>=cfg['archive_files_max'] or sum(p.stat().st_size for p in files)>=cfg['archive_bytes_max']:state.update(status='failed',archive_cap_exceeded=True);save(out/'summary.json',state)
        save(out/'manifest.json',{p.name:sha(p.read_bytes()) for p in files});print(json.dumps(state),flush=True)
    return 0 if state['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
