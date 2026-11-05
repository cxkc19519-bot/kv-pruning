"""Bounded fixed-Qwen2.5 Full/half-KV gates. Reuses pinned project KV primitives."""
import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
import sys
sys.dont_write_bytecode=True
import argparse
import copy
import gc
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import signal
import subprocess
import time
import traceback


def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=True,allow_nan=False,indent=2)+'\n')
def append(p,x):
    with p.open('a') as f:f.write(json.dumps(x,ensure_ascii=True,allow_nan=False)+'\n')
def check(ok,s):
    if not ok:raise ValueError(s)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--proposal',required=True);ap.add_argument('--execute',action='store_true');args=ap.parse_args()
    r=Path(__file__).resolve().parent.parent
    check(args.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning','server execute required')
    raw=(r/args.proposal).read_bytes();cfg=json.loads(raw);out=r/cfg['run']
    check(out.resolve().parent==(r/'results').resolve(),'output boundary');out.mkdir(exist_ok=False)
    start=time.monotonic();state=dict(status='running',stage='inputs',pid=os.getpid(),main_outputs=0,engineering_outputs=0,full_support=None)
    rows=[];engineering=[];active=None
    def timeout(*a):raise TimeoutError('frozen wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(cfg['wall_seconds'])
    try:
        save(out/'summary.json',state);(out/'proposal_snapshot.json').write_bytes(raw);(out/'source_runner.py').write_bytes(Path(__file__).read_bytes())
        for key in ['decision_contract','tokenizer_proposal','tokenized','tokenizer_manifest','cases']:
            check(sha((r/cfg[key]).read_bytes())==cfg[key+'_sha256'],'input pin:'+key)
        for name,h in cfg['sources'].items():
            b=(r/'scripts'/name).read_bytes();check(sha(b)==h,'source pin:'+name);(out/('source_'+name)).write_bytes(b)
        tp=json.loads((r/cfg['tokenizer_proposal']).read_text());model_dir=Path(tp['model'])
        for name,h in tp['files'].items():check(sha((model_dir/name).read_bytes())==h,'model metadata pin:'+name)
        versions={k:importlib.metadata.version(k) for k in cfg['versions']};check(versions==cfg['versions'],'framework versions')
        check(os.environ.get('CUDA_VISIBLE_DEVICES')==cfg['gpu_uuid'],'device UUID')
        gpu=subprocess.run(['nvidia-smi','-i',cfg['gpu_uuid'],'--query-gpu=uuid,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15).stdout.strip()
        fields=[s.strip() for s in gpu.split(',')];check(int(fields[2])<=cfg['gpu_idle_memory_mib_max'] and int(fields[4])==0,'selected GPU busy')
        save(out/'gpu_before.json',dict(raw=gpu,other_processes_manipulated=False))
        state['stage']='weight_hashes';save(out/'summary.json',state)
        weight_hashes={}
        for name,expected in cfg['weights'].items():
            hh=hashlib.sha256()
            with (model_dir/name).open('rb') as f:
                for b in iter(lambda:f.read(8388608),b''):hh.update(b)
            check(hh.hexdigest()==expected,'weight pin:'+name);weight_hashes[name]=hh.hexdigest()
        save(out/'weight_verification.json',weight_hashes)
        from answer_format_task import score_response
        import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM,GenerationConfig
        from trec_context_gate import native,prefill,clone_cache,cache_state
        from trec_pruning_run import scored_prefill,decode_compact,native_compact,build_maps,equal_cache
        from trec_pruning_utils import gather_prefix_cache,kv_bytes
        torch.set_num_threads(4);torch.manual_seed(20261030)
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        tok=AutoTokenizer.from_pretrained(str(model_dir),local_files_only=True,trust_remote_code=False,use_fast=True)
        tokenized=json.loads((r/cfg['tokenized']).read_text());cases={x['case_id']:x for x in map(json.loads,(r/cfg['cases']).read_text().splitlines()) if x['case_id'] in {t['case_id'] for t in tokenized}}
        check(len(cases)==len(tokenized)==14,'case roles')
        for x in tokenized:
            c=cases[x['case_id']];ids=tok.apply_chat_template([dict(role='system',content=c['prompt']['system']),dict(role='user',content=c['prompt']['user'])],tokenize=True,add_generation_prompt=True)
            check(ids==x['input_ids'] and c['prompt_sha256']==x['prompt_sha256'],'retokenized mismatch')
        state['stage']='load_model';save(out/'summary.json',state)
        model=AutoModelForCausalLM.from_pretrained(str(model_dir),torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True,trust_remote_code=False).eval().to('cuda:0')
        check(len(model.model.layers)==28 and set(model.config.layer_types)=={'full_attention'} and not model.config.use_sliding_window,'runtime Full Attention')
        check(all(getattr(x.self_attn,'sliding_window',None) is None for x in model.model.layers),'runtime sliding attention')
        check(all(p.dtype==torch.bfloat16 for p in model.parameters()),'runtime BF16')
        decode=GenerationConfig(**cfg['decode']);model.generation_config=copy.deepcopy(decode);eos=set(decode.eos_token_id)
        save(out/'execution_snapshot.json',dict(proposal_sha256=sha(raw),runner_sha256=sha(Path(__file__).read_bytes()),execution_enabled=True,versions=versions,model_path=str(model_dir),decode_actual=decode.to_dict(),model_generation_config= model.generation_config.to_dict(),runtime_full_layers=28,kv_heads=4,head_dim=128,kv_dtype='bfloat16',bytes_per_token=57344,source_hashes=cfg['sources'],old_scorer_not_called=True,gpu_uuid=cfg['gpu_uuid']))

        def cache_hash(cache):
            hh=hashlib.sha256()
            for layer in cache.layers:
                for t in [layer.keys,layer.values]:hh.update(t.contiguous().view(torch.uint8).cpu().numpy().tobytes())
            return hh.hexdigest()

        def prepare(x,save_scores=True):
            n=x['prefix_tokens'];ref,scores=scored_prefill(model,x['input_ids'][:n])
            check(kv_bytes(ref)==n*57344 and len(ref.layers)==28,'actual prefix KV size')
            for layer in ref.layers:check(tuple(layer.keys.shape)==(1,4,n,128) and layer.keys.dtype==torch.bfloat16,'actual KV shape')
            payload=gzip.compress(json.dumps({str(k):v.tolist() for k,v in scores.items()},separators=(',',':'),allow_nan=False).encode(),mtime=0)
            if save_scores:(out/(x['case_id']+'.scores.json.gz')).write_bytes(payload)
            return ref,scores,cache_hash(ref),sha(payload)

        def result(x,condition,ids,cache,prefix_bytes,trace=None):
            content=ids[:-1] if ids and ids[-1] in eos else ids
            text=tok.decode(content,skip_special_tokens=False,clean_up_tokenization_spaces=False)
            score=score_response(text,[a['text'] for a in cases[x['case_id']]['answers']])
            return dict(case_id=x['case_id'],split_role=x['split_role'],condition=condition,status='ok',ids=ids,text=text,raw_with_terminal=tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False),generated_tokens=len(ids),truncated=not (ids and ids[-1] in eos),metrics=score,prompt_sha256=x['prompt_sha256'],gold_sha256=cases[x['case_id']]['gold_sha256'],prefix_tokens=x['prefix_tokens'],prefix_kv_bytes=prefix_bytes,final_live_kv_bytes=kv_bytes(cache) if cache is not None else None,trace=trace,peak_memory=None,latency=None,cost_reason='not_benchmarked; full reference retained for gather')

        def emit(x,condition,ids,cache,bytes_,trace=None,eng=False):
            nonlocal active
            rr=result(x,condition,ids,cache,bytes_,trace);(engineering if eng else rows).append(rr)
            append(out/('engineering.jsonl' if eng else 'generations.jsonl'),rr)
            active=None
            state['engineering_outputs' if eng else 'main_outputs']+=1
            check(state['engineering_outputs']<=cfg['engineering_answers_max'] and state['main_outputs']<=cfg['main_answers_max'],'answer cap')
            save(out/'summary.json',state);return rr

        engcases=[x for x in tokenized if x['split_role']=='engineering'];dev=[x for x in tokenized if x['split_role']=='development']
        check(len(engcases)==2 and len(dev)==12,'cohort count')
        if cfg['phase']=='full':
            state['stage']='three_path_engineering'
            for x in engcases:
                n=x['prefix_tokens'];suffix=x['input_ids'][n:]
                active=(x,'native_whole',True);a=native(model,x['input_ids'],decode);emit(x,'native_whole',a,None,n*57344,eng=True)
                rawref=prefill(model,x['input_ids'][:n]);ref,scores,digest,ssha=prepare(x)
                check(equal_cache(rawref,ref),'scoring hook changed prefix cache');before=cache_state(ref)
                branch=clone_cache(rawref);active=(x,'native_split',True);b=native(model,suffix,decode,branch,n);emit(x,'native_split',b,branch,n*57344,eng=True);del branch,rawref
                branch=clone_cache(ref);active=(x,'custom_split',True);c,tr=decode_compact(model,branch,n,suffix,cfg['decode']['max_new_tokens'],eos);emit(x,'custom_split',c,branch,n*57344,tr,eng=True)
                check(a==b==c and cache_state(ref)==before,'three path token mismatch or shared cache mutation');del branch,ref,scores;gc.collect()
            state['engineering_gate']=True;state['stage']='Full_development'
            for x in dev:
                ref,scores,digest,ssha=prepare(x);n=x['prefix_tokens'];before=cache_state(ref)
                branch=clone_cache(ref);active=(x,'full',False);ids,tr=decode_compact(model,branch,n,x['input_ids'][n:],cfg['decode']['max_new_tokens'],eos)
                rr=emit(x,'full',ids,branch,n*57344,tr);rr.update(reference_prefix_sha256=digest,score_archive_sha256=ssha)
                # The append-only row already exists; supplemental identities are a separate fixed map.
                save(out/(x['case_id']+'.reference.json'),dict(reference_prefix_sha256=digest,score_archive_sha256=ssha))
                check(cache_state(ref)==before,'Full shared reference mutation');del ref,branch,scores;gc.collect()
            good=[x for x in rows if not x['truncated']]
            counts=dict(n=len(rows),truncated=sum(x['truncated'] for x in rows),candidates=sum(x['metrics']['candidate_status']=='available' for x in good),em=sum(x['metrics']['em'] is True for x in good),format=sum(x['metrics']['format'] for x in good),joint=sum(x['metrics']['joint_success'] for x in good))
            gate=cfg['full_gate'];passed=len(rows)==12 and counts['truncated']<=gate['truncated_max'] and all(counts[k]>=gate[k+'_min'] for k in ['candidates','em','format','joint'])
            state.update(full_support=passed,full_counts=counts,status='complete',stage='complete')
        else:
            check(cfg['phase']=='compression','unknown phase')
            check(sha((r/cfg['full_manifest']).read_bytes())==cfg['full_manifest_sha256'],'Full manifest pin')
            fullout=(r/cfg['full_manifest']).parent;fs=json.loads((fullout/'summary.json').read_text());check(fs['full_support'] is True,'Full support prerequisite')
            baseline={z['case_id']:z for z in map(json.loads,(fullout/'generations.jsonl').read_text().splitlines())};check(len(baseline)==12,'Full row count')
            methods=cfg['methods'];conditions=[dict(method=m,pin_shared_header=m.endswith('_system_pinned')) for m in methods]
            for eng,xs in [(True,engcases),(False,dev)]:
                state['stage']='compact_engineering' if eng else 'compressed_development'
                for x in xs:
                    ref,scores,digest,ssha=prepare(x);n=x['prefix_tokens'];before=cache_state(ref)
                    if not eng:
                        expected=json.loads((fullout/(x['case_id']+'.reference.json')).read_text());check(expected==dict(reference_prefix_sha256=digest,score_archive_sha256=ssha),'Full/compression prefix or score mismatch')
                    applicable=[]
                    for cond in conditions:
                        if cond['pin_shared_header'] and x['budget_state']=='infeasible_budget':
                            missing=dict(case_id=x['case_id'],split_role=x['split_role'],condition=cond['method'],status='infeasible_budget',reason='complete_system_plus_anchors_exceeds_fixed_half_budget',prefix_tokens=n,prefix_kv_bytes=None,budget_slots=x['budget'],required_union_count=len(x['required_pinned_ids']),prompt_sha256=x['prompt_sha256'],gold_sha256=cases[x['case_id']]['gold_sha256'])
                            append(out/('engineering.jsonl' if eng else 'generations.jsonl'),missing)
                            state['infeasible_engineering_cells' if eng else 'infeasible_main_cells']=state.get('infeasible_engineering_cells' if eng else 'infeasible_main_cells',0)+1
                        else:applicable.append(cond)
                    maps=build_maps(scores,cases[x['case_id']]['context_group_id'],n,dict(header_ids=x['header_ids']),applicable)
                    mp={m:{str(i):v.tolist() for i,v in layers.items()} for m,layers in maps.items()};(out/(x['case_id']+'.maps.json.gz')).write_bytes(gzip.compress(json.dumps(mp,separators=(',',':')).encode(),mtime=0))
                    for cond in applicable:
                        method=cond['method'];pin=cond['pin_shared_header'];idx=maps[method]
                        branch=gather_prefix_cache(ref,idx,n,n//2,x['header_ids'],pin);check(kv_bytes(branch)==x['budget']*57344,'actual equal-byte prefix')
                        for li,layer in enumerate(branch.layers):
                            ii=idx[li].to(model.device).unsqueeze(-1).expand(1,4,x['budget'],128)
                            check(torch.equal(layer.keys,ref.layers[li].keys.gather(2,ii)) and torch.equal(layer.values,ref.layers[li].values.gather(2,ii)),'gather bit equality')
                        if eng:
                            b2=clone_cache(branch);active=(x,method+'_native',True);a,tr1=native_compact(model,b2,n,x['input_ids'][n:],decode);emit(x,method+'_native',a,b2,x['budget']*57344,tr1,True);del b2
                        active=(x,method,eng);b,tr2=decode_compact(model,branch,n,x['input_ids'][n:],cfg['decode']['max_new_tokens'],eos);emit(x,method,b,branch,x['budget']*57344,tr2,eng)
                        if eng:check(a==b and tr1==tr2,'native/custom compact mismatch')
                        check(cache_state(ref)==before,'compressed shared cache mutation');del branch
                    del maps,idx,ref,scores;gc.collect()
            state.update(status='complete',stage='complete',engineering_gate=True,full_support=True)
        active=None
    except BaseException as exc:
        if active:
            x,method,eng=active;append(out/('engineering.jsonl' if eng else 'generations.jsonl'),dict(case_id=x['case_id'],condition=method,status='error',reason=repr(exc)))
        state.update(status='failed',error=repr(exc));(out/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0);state['elapsed_seconds']=time.monotonic()-start;save(out/'summary.json',state)
        files=[p for p in out.iterdir() if p.is_file()];check(len(files)<cfg['max_archive_files'] and sum(p.stat().st_size for p in files)<cfg['max_archive_bytes'],'archive cap')
        save(out/'manifest.json',{p.name:sha(p.read_bytes()) for p in files});print(json.dumps(state),flush=True)
    return 0 if state['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
