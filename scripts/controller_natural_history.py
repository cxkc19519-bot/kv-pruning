"""One frozen natural-history mechanism screen, with a two-answer hook gate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback

PROPOSAL_SHA='d5dac66847f89c1d7974d7def42a95c5d6b8c824a07137101a5a7101016e72ec'
HELPER_SHA='ae0edd47557034c168aa4287d4ba36e3f112252d008d2ad9388c476ccd52895e'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')


def check_trace(path):
    events=[json.loads(l) for l in path.read_text().splitlines()]
    # MRV2 skips budget/allocation when the first full prefill has no drafts.
    # The prompt still reaches observe_verification and advances refit phase.
    assert len(events)>=4 and (len(events)-1)%3==0,'Missing native decode trace stage'
    prefill=events[0]
    assert prefill['event']=='verification' and prefill['num_sampled']==[1]
    assert prefill['num_accepted']==[0] and prefill['num_rejected']==[0]
    assert len(prefill['slots'])==1
    for v in [x for x in events if x['event']=='verification']:
        if v['frozen']:
            assert v['phase_after']==v['phase_before'] and v['refits_after']==v['refits_before']
        else:
            assert v['phase_after']==(v['phase_before']+1)%100
            assert v['refits_after']==v['refits_before']+int(v['phase_before']==99)
    for i in range(1,len(events),3):
        b,a,v=events[i:i+3]
        assert [b['event'],a['event'],v['event']]==['budget','allocation','verification']
        assert b['request_ids']==a['request_ids'] and b['slots']==a['slots']==v['slots']
        assert len(b['request_ids'])==1,'Frozen single-request screen'
        assert b['selected_draft_budget']==a['selected_draft_budget']==sum(a['capacities'])
        assert b['total_tokens']==sum(b['non_draft_tokens'])+sum(a['capacities'])
        assert a['cu_num_logits'][-1]==sum(a['capacities'])+1
        assert 0<=a['capacities'][0]<=b['scheduled_drafts'][0]<=4
        assert v['num_accepted'][0]+v['num_rejected'][0]==a['capacities'][0]
    return dict(events=len(events),steps=1+(len(events)-1)//3,prefill_steps=1,
                selected_budgets=[x['selected_draft_budget'] for x in events if x['event']=='budget'],
                decode_budgets=[x['selected_draft_budget'] for x in events if x['event']=='budget' and sum(x['scheduled_drafts'])>0],
                decode_target_query_tokens=sum(sum(x['query_start_loc'][j+1]-x['query_start_loc'][j] for j in range(len(x['capacities']))) for x in events if x['event']=='allocation'),
                total_admitted=sum(sum(x['capacities']) for x in events if x['event']=='allocation'),
                total_accepted=sum(sum(x['num_accepted']) for x in events if x['event']=='verification'))


class InsufficientRefit(Exception):pass


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-dir',required=True)
    ap.add_argument('--correction');a=ap.parse_args()
    root=Path(__file__).resolve().parents[1];out=Path(a.run_dir).resolve()
    assert out.parent==root/'results';out.mkdir(exist_ok=False)
    llm=None;stream=None;started=time.monotonic()
    state=dict(status='running',pid=os.getpid(),start_unix=time.time(),stage='prepare',
               main_answers=0,engineering_answers=0,warmup_answers=0,total_answers=0,
               generated_tokens=0,rpc=[],boundaries={},traces={},unexecuted_conditions=[])
    planned=['warmup_probe','warmup_history','engineering_hook_off','engineering_hook_on','baseline_probe']
    for group in ['A','B','A_frozen','B_frozen']:
        planned.extend([group+f'_history_{i}' for i in range(6)]+[group+'_probe'])
    planned.append('restored_B_probe')
    state['planned_labels']=planned
    state['attempted_labels']=[]
    def save():dump(out/'summary.json',state)
    def timeout(*_):raise TimeoutError('900 second natural-history bound')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(900);save()
    try:
        proposal_path=root/'configs/controller-natural-history-proposal-v1.json'
        assert sha(proposal_path)==PROPOSAL_SHA and sha(root/'scripts/controller_worker_state.py')==HELPER_SHA
        correction=None
        if a.correction:
            correction_path=root/a.correction;correction=json.loads(correction_path.read_text())
            assert correction['base_proposal_sha256']==PROPOSAL_SHA
            prior=root/correction['prior_run']
            assert sha(prior/'manifest.json')==correction['prior_manifest_sha256']
            assert sha(prior/'engineering_hook_on.trace.jsonl')==correction['prior_trace_sha256']
            (out/'correction_snapshot.json').write_bytes(correction_path.read_bytes())
        p=json.loads(proposal_path.read_text());runtime_path=root/p['runtime_config']
        assert sha(runtime_path)==p['runtime_config_sha256']
        cfg=json.loads(runtime_path.read_text())
        native={
            'acceptance_estimator.py':'f7a4a2f2c1e3221407d12c70cc067cc8cc045bd1',
            'speculator.py':'d86a0b0351f05073ebecf59af06e68cdcb1ad96c',
            'adaptive_verification.py':'5f91af59e5924bfb89b0c6cc0b6eb62e02010d06'}
        site=root/'.venv-controller-history/lib/python3.11/site-packages/vllm/v1/worker/gpu/spec_decode'
        checked={}
        for filename,expected in native.items():
            raw=(site/filename).read_bytes()
            actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            assert actual==expected
            checked[filename]=dict(expected_blob=expected,actual_blob=actual,match=True)
        dump(out/'native_source_checks.json',checked)
        for name,value in cfg['environment_overrides'].items():os.environ[name]=value
        for name in ['controller_natural_history.py','controller_history_observer.py','controller_worker_state.py']:
            (out/('source_'+name)).write_bytes((root/'scripts'/name).read_bytes())
        (out/'proposal_snapshot.json').write_bytes(proposal_path.read_bytes())
        (out/'runtime_snapshot.json').write_bytes(runtime_path.read_bytes())
        execution=dict(proposal_sha256=PROPOSAL_SHA,execution_enabled=True,main_execution_enabled=False,
            max_answers=34,max_main_answers=30,max_seconds=900,max_generated_tokens=1856,
            source_sha256={n:sha(root/'scripts'/n) for n in ['controller_natural_history.py','controller_history_observer.py','controller_worker_state.py']},
            worker_extension_cls='controller_history_observer.ControllerNaturalHistoryExtension',synthetic_phase_in_main=False)
        if correction is not None:
            execution['correction_sha256']=sha(correction_path)
        dump(out/'execution_snapshot.json',execution)
        from vllm import LLM,SamplingParams,EngineArgs
        from vllm.config import CompilationConfig
        from transformers import AutoTokenizer
        kwargs=dict(model=str(root/cfg['target']),tokenizer=str(root/cfg['target']),dtype='bfloat16',
            trust_remote_code=False,tensor_parallel_size=1,max_model_len=512,max_num_seqs=2,
            max_num_batched_tokens=512,gpu_memory_utilization=0.9,enforce_eager=False,
            enable_prefix_caching=False,async_scheduling=False,seed=42,generation_config='vllm',
            disable_log_stats=True,compilation_config=CompilationConfig(**cfg['compilation_config']),
            attention_config=cfg['attention_config'],
            worker_extension_cls=execution['worker_extension_cls'],
            speculative_config=dict(method='draft_model',model=str(root/cfg['draft']),
                num_speculative_tokens=4,enable_adaptive_verification=True,
                use_local_argmax_reduction=False,draft_sample_method='greedy'))
        state['stage']='config_validation';save();EngineArgs(**kwargs).create_engine_config()
        state['stage']='engine_init';save();llm=LLM(**kwargs)
        tok=AutoTokenizer.from_pretrained(root/cfg['target'],local_files_only=True)
        stream=(out/'answers.jsonl').open('x')

        def rpc(method,*args):
            assert not llm.llm_engine.has_unfinished_requests()
            result=llm.collective_rpc(method,timeout=45,args=args);assert len(result)==1
            return result[0]
        def ctl(op,key='common',enabled=False):
            r=rpc('controller_history_control',op,key,enabled)
            state['rpc'].append(r);save();return r
        def detail(label):
            r=rpc('controller_history_detail')
            state['boundaries'][label]=r;save();return r
        hooks=False
        def generate(label,text,count,kind,trace=True):
            state['stage']=label;save()
            assert state['total_answers']<34
            assert state[kind+'_answers']<{'main':30,'warmup':2,'engineering':2}[kind]
            prompt=tok.apply_chat_template([{'role':'user','content':text}],tokenize=False,
                                           add_generation_prompt=True,enable_thinking=False)
            ids=tok.encode(prompt);assert len(ids)<=256 and len(ids)+count<=512
            assert label in planned and label not in state['attempted_labels']
            state['attempted_labels'].append(label);save()
            path=out/(label+'.trace.jsonl')
            if trace:
                assert hooks;rpc('controller_history_trace','begin',label,str(path))
            params=SamplingParams(temperature=0,top_p=1,seed=42,max_tokens=count,ignore_eos=True)
            results=llm.generate([prompt],params,use_tqdm=False)
            assert len(results)==1 and len(results[0].outputs)==1
            answer=results[0].outputs[0]
            row=dict(label=label,kind=kind,text_input=text,prompt=prompt,prompt_ids=ids,
                     request_id=results[0].request_id,token_ids=list(answer.token_ids),
                     text=answer.text,finish_reason=answer.finish_reason,requested_tokens=count)
            stream.write(json.dumps(row,allow_nan=False)+'\n');stream.flush()
            state[kind+'_answers']+=1;state['total_answers']+=1
            state['generated_tokens']+=len(row['token_ids']);save()
            assert len(row['token_ids'])==count and state['generated_tokens']<=1856
            if trace:
                stats=rpc('controller_history_trace','end')
                parsed=check_trace(path);assert stats['events']==parsed['events']
                state['traces'][label]=parsed;save()
            return row

        ctl('inspect')
        generate('warmup_probe',p['probe'],32,'warmup',False)
        generate('warmup_history',p['histories']['B'],32,'warmup',False)
        warm=ctl('save','warm_before_refit');ctl('warm_refit')
        restored=ctl('restore','warm_before_refit');assert restored['digest']==warm['digest']
        common=ctl('save');base_detail=detail('common')
        generate_off=generate('engineering_hook_off',p['probe'],32,'engineering',False)
        off=detail('engineering_hook_off_end')
        assert ctl('restore')['digest']==common['digest']
        rpc('controller_history_trace','install');hooks=True
        generate_on=generate('engineering_hook_on',p['probe'],32,'engineering')
        on=detail('engineering_hook_on_end')
        assert generate_off['token_ids']==generate_on['token_ids'],'Observer changed probe tokens'
        assert off['status']['learning_digest']==on['status']['learning_digest'],'Observer changed learning state'
        dump(out/'engineering_gate.json',dict(status='pass',answers=2,
            token_ids_exact=True,learning_digest_exact=True,learning_digest=on['status']['learning_digest']))
        execution['main_execution_enabled']=True
        dump(out/'main_execution_snapshot.json',execution)

        assert ctl('restore')['digest']==common['digest']
        detail('baseline_before');baseline=generate('baseline_probe',p['probe'],32,'main');detail('baseline_after')
        probe_rows={'baseline':baseline}
        for name in ['A','B']:
            assert ctl('restore')['digest']==common['digest']
            before=detail(name+'_learning_before')
            for i in range(6):generate(name+f'_history_{i}',p['histories'][name],64,'main')
            after=detail(name+'_history_after')
            if after['status']['refits']<=before['status']['refits']:
                raise InsufficientRefit(name+' history did not naturally cross a refit in six requests')
            if name=='B':ctl('save','after_B_history')
            probe=generate(name+'_probe',p['probe'],32,'main');detail(name+'_probe_after')
            assert probe['token_ids']==baseline['token_ids'],'Main probe token mismatch: '+name
            probe_rows[name]=probe
        for name in ['A','B']:
            assert ctl('restore')['digest']==common['digest']
            frozen=ctl('freeze',enabled=True);detail(name+'_frozen_before')
            for i in range(6):generate(name+f'_frozen_history_{i}',p['histories'][name],64,'main')
            after=detail(name+'_frozen_history_after')
            assert after['status']['learning_digest']==frozen['learning_digest']
            probe=generate(name+'_frozen_probe',p['probe'],32,'main')
            end=detail(name+'_frozen_probe_after')
            assert end['status']['learning_digest']==frozen['learning_digest']
            assert probe['token_ids']==baseline['token_ids'],'Frozen probe token mismatch'
            probe_rows[name+'_frozen']=probe
        ctl('restore','after_B_history')
        assert ctl('restore')['digest']==common['digest']
        detail('restored_B_before')
        restored_probe=generate('restored_B_probe',p['probe'],32,'main');detail('restored_B_after')
        assert restored_probe['token_ids']==baseline['token_ids']
        assert state['main_answers']==30 and state['total_answers']==34
        assert all(x['cost_sha256']==base_detail['cost_sha256'] for x in state['boundaries'].values())
        state.update(status='complete',stage='complete',probe_comparison={
            label:state['traces'][label] for label in ['baseline_probe','A_probe','B_probe','A_frozen_probe','B_frozen_probe','restored_B_probe']})
        ctl('restore')
    except InsufficientRefit as exc:
        state.update(status='stopped_insufficient_refit_exposure',stop_reason=str(exc))
    except BaseException as exc:
        state.update(status='failed',error=repr(exc));(out/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0)
        if stream is not None:stream.close()
        if llm is not None:
            try:llm.llm_engine.engine_core.shutdown()
            except Exception as exc:state['shutdown_note']=repr(exc)
        state['elapsed_seconds']=time.monotonic()-started
        completed=[]
        if (out/'answers.jsonl').exists():
            completed=[json.loads(l)['label'] for l in (out/'answers.jsonl').read_text().splitlines()]
        state['unexecuted_conditions']=[label for label in planned if label not in completed]
        state['started_not_completed']=[label for label in state['attempted_labels'] if label not in completed]
        save()
        dump(out/'manifest.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})
        print(json.dumps({k:v for k,v in state.items() if k not in ['rpc','boundaries','traces']},indent=2),flush=True)
    return 0 if state['status'] in ('complete','stopped_insufficient_refit_exposure') else 1


if __name__=='__main__':raise SystemExit(main())
