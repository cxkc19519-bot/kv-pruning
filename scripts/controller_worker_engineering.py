"""One bounded real-engine attempt. No history-effect or performance claims."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-dir',required=True)
    ap.add_argument('--config',default='configs/controller-worker-engineering-v1.json');a=ap.parse_args()
    root=Path(__file__).resolve().parents[1];out=Path(a.run_dir).resolve()
    assert out.parent==root/'results';out.mkdir(exist_ok=False)
    cfg=json.loads((root/a.config).read_text())
    for name,value in cfg.get('environment_overrides',{}).items():
        assert name in ('VLLM_USE_FLASHINFER_SAMPLER','VLLM_ALLOW_INSECURE_SERIALIZATION') and value=='0'
        os.environ[name]=value
    cfg['execution_enabled']=True
    (out/'execution_snapshot.json').write_text(json.dumps(cfg,indent=2)+'\n')
    for f in ['controller_worker_engineering.py','controller_worker_state.py']:
        (out/('source_'+f)).write_bytes((root/'scripts'/f).read_bytes())
    state=dict(status='running',pid=os.getpid(),start_unix=time.time(),main_outputs=0,
               engineering_answers=0,stage='imports',rpc=[])
    def save(): (out/'summary.json').write_text(json.dumps(state,indent=2)+'\n')
    def timeout(*_):raise TimeoutError('600 second worker engineering limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(cfg['max_seconds']);save()
    llm=None
    generations=(out/'engineering_answers.jsonl').open('x')
    try:
        from vllm import LLM,SamplingParams,EngineArgs
        from vllm.config import CompilationConfig
        from transformers import AutoTokenizer
        from controller_worker_state import control
        kwargs=dict(model=str(root/cfg['target']),tokenizer=str(root/cfg['target']),
            dtype='bfloat16',trust_remote_code=False,tensor_parallel_size=1,
            max_model_len=cfg['max_model_len'],max_num_seqs=cfg['max_num_seqs'],
            max_num_batched_tokens=cfg['max_num_batched_tokens'],
            gpu_memory_utilization=cfg['gpu_memory_utilization'],enforce_eager=cfg['enforce_eager'],
            enable_prefix_caching=False,async_scheduling=False,seed=42,
            generation_config='vllm',disable_log_stats=True,
            speculative_config=dict(method='draft_model',model=str(root/cfg['draft']),
                 num_speculative_tokens=4,enable_adaptive_verification=True,
                 use_local_argmax_reduction=False,draft_sample_method='greedy'))
        if cfg.get('compilation_config') is not None:
            kwargs['compilation_config']=CompilationConfig(**cfg['compilation_config'])
        if cfg.get('attention_config') is not None:
            kwargs['attention_config']=cfg['attention_config']
        if cfg.get('worker_extension_cls') is not None:
            kwargs['worker_extension_cls']=cfg['worker_extension_cls']
        state['stage']='config_validation';save()
        validated=EngineArgs(**kwargs).create_engine_config()
        state['validated_cudagraph_mode']=str(validated.compilation_config.cudagraph_mode)
        state['stage']='engine_init';save()
        llm=LLM(**kwargs)
        def rpc(op,key='common',enabled=False):
            assert not llm.llm_engine.has_unfinished_requests(),'Frontend not drained'
            method='controller_history_control' if cfg.get('worker_extension_cls') else control
            v=llm.collective_rpc(method,timeout=45,args=(op,key,enabled))
            assert len(v)==1
            state['rpc'].append(v[0]);save();return v[0]
        state['stage']='inspect';save();rpc('inspect')
        tok=AutoTokenizer.from_pretrained(root/cfg['target'],local_files_only=True)
        params=SamplingParams(temperature=0,top_p=1,seed=42,max_tokens=32,ignore_eos=True)
        def generate(label,text):
            assert state['engineering_answers']<6
            prompt=tok.apply_chat_template([{'role':'user','content':text}],tokenize=False,
                                            add_generation_prompt=True,enable_thinking=False)
            assert len(tok.encode(prompt))+32<=512
            state['stage']=label;save()
            result=llm.generate([prompt],params,use_tqdm=False)
            assert len(result)==1 and len(result[0].outputs)==1
            answer=result[0].outputs[0]
            row=dict(label=label,request_id=result[0].request_id,token_ids=list(answer.token_ids),
                     text=answer.text,finish_reason=answer.finish_reason)
            generations.write(json.dumps(row)+'\n');generations.flush()
            state['engineering_answers']+=1;save();return row
        generate('warmup_probe',cfg['probe']);generate('warmup_history',cfg['history'])
        rpc('save','before_refit_warmup');rpc('warm_refit');rpc('restore','before_refit_warmup')
        rpc('boundary');base=rpc('save')
        changed=rpc('mutate');assert changed['digest']!=base['digest']
        restored=rpc('restore');assert restored['digest']==base['digest']
        assert restored['tensor_addresses']==base['tensor_addresses']
        first=generate('probe_original',cfg['probe']);end=rpc('status')
        assert end['refits']>base['refits'],'Probe must cross synthetic refit boundary'
        generate('intervening_history',cfg['history'])
        restored=rpc('restore');assert restored['digest']==base['digest']
        second=generate('probe_replay',cfg['probe']);replayed=rpc('status')
        assert first['token_ids']==second['token_ids'],'Greedy probe replay token mismatch'
        assert end['learning_digest']==replayed['learning_digest'],'Controller learning replay mismatch'
        rpc('restore');frozen=rpc('freeze',enabled=True)
        generate('probe_frozen',cfg['probe']);frozen_end=rpc('status')
        assert frozen['learning_digest']==frozen_end['learning_digest'],'Frozen estimator learned'
        rpc('restore')
        state.update(status='pass',stage='complete',controller_restore_exact=True,
                     probe_tokens_exact=True,learning_replay_exact=True,freeze_pass=True)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc));(out/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0);generations.close()
        if llm is not None:
            try:llm.llm_engine.engine_core.shutdown()
            except Exception as exc:state['shutdown_note']=repr(exc)
        state['elapsed_seconds']=time.time()-state['start_unix'];save()
        (out/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in out.iterdir() if p.is_file() and p.name!='console.log'},indent=2)+'\n')
        print(json.dumps(state,indent=2),flush=True)
    return 0 if state['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main())
