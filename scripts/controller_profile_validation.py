"""One bounded default-graph profile validation; two engineering answers only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback

from analyze_controller_profile import analyze


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, x): p.write_text(json.dumps(x, indent=2, allow_nan=False)+'\n')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run-dir', required=True)
    a = ap.parse_args(); root = Path(__file__).resolve().parents[1]
    out = Path(a.run_dir).resolve(); assert out.parent == root/'results'
    out.mkdir(exist_ok=False); start = time.monotonic(); llm = None
    state = dict(status='running', pid=os.getpid(), start_unix=time.time(),
        stage='prepare', main_answers=0, engineering_answers=0, generated_tokens=0)
    save = lambda: dump(out/'summary.json', state)
    def timeout(*_): raise TimeoutError('600 second profile-validation bound')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(600); save()
    try:
        pp = root/'configs/controller-profile-validation-proposal-v1.json'
        assert sha(pp) == 'a0e57871f1588161b75c5b4e114262720405224c5c564a8642fd1699fb347f8e'
        p = json.loads(pp.read_text()); rp = root/p['base_runtime']
        assert sha(rp) == p['base_runtime_sha256']; cfg = json.loads(rp.read_text())
        prior = root/'results/20261030-controller-natural-history-v2'
        assert sha(prior/'manifest.json') == 'f802fb66a3e8f54f666af88bc534249dd4ac493ba80829778835b421ad73f7df'
        previous = [json.loads(x) for x in (prior/'answers.jsonl').read_text().splitlines()]
        baseline = next(x for x in previous if x['label'] == 'baseline_probe')
        assert baseline['text_input'] == cfg['probe'] == p['answers'][0]['prompt']
        assert sha(root/'scripts/controller_worker_state.py') == 'ae0edd47557034c168aa4287d4ba36e3f112252d008d2ad9388c476ccd52895e'
        pins = json.loads((root/'docs/CONTROLLER_COST_PROFILE_SOURCE_20261030.json').read_text())['installed_source_pins']
        site = root/'.venv-controller-history/lib/python3.11/site-packages'
        checks = {}
        for pin in pins:
            raw = (site/pin['path']).read_bytes()
            blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            assert blob == pin['git_blob_sha1']; checks[pin['path']] = blob
        dump(out/'native_source_checks.json', checks)
        for name in ['controller_profile_validation.py','controller_profile_observer.py',
                     'analyze_controller_profile.py','controller_worker_state.py']:
            (out/('source_'+name)).write_bytes((root/'scripts'/name).read_bytes())
        (out/'proposal_snapshot.json').write_bytes(pp.read_bytes())
        (out/'runtime_snapshot.json').write_bytes(rp.read_bytes())
        for name, value in cfg['environment_overrides'].items(): os.environ[name] = value
        os.environ['CONTROLLER_PROFILE_OUT'] = str(out)
        os.environ['VLLM_ADAPTIVE_VERIFICATION_PROFILE_CONTEXT_LEN'] = '8192'
        dump(out/'execution_snapshot.json', dict(proposal=p, execution_enabled=True,
            runner_implemented=True, main_execution_enabled=False,
            source_hashes={n:sha(root/'scripts'/n) for n in ['controller_profile_validation.py',
                'controller_profile_observer.py','analyze_controller_profile.py','controller_worker_state.py']}))
        from vllm import LLM, SamplingParams, EngineArgs
        from vllm.config import CompilationConfig
        from transformers import AutoTokenizer
        kwargs = dict(model=str(root/cfg['target']), tokenizer=str(root/cfg['target']),
            dtype='bfloat16', trust_remote_code=False, tensor_parallel_size=1,
            max_model_len=512, max_num_seqs=2, max_num_batched_tokens=512,
            gpu_memory_utilization=0.9, enforce_eager=False, enable_prefix_caching=False,
            async_scheduling=False, seed=42, generation_config='vllm', disable_log_stats=True,
            performance_mode='balanced',
            compilation_config=CompilationConfig(mode=0, cudagraph_mode='FULL_DECODE_ONLY'),
            attention_config=cfg['attention_config'],
            worker_extension_cls='controller_profile_observer.ControllerProfileWorkerExtension',
            speculative_config=dict(method='draft_model', model=str(root/cfg['draft']),
                num_speculative_tokens=4, enable_adaptive_verification=True,
                use_local_argmax_reduction=False, draft_sample_method='greedy'))
        state['stage'] = 'config_validation'; save()
        resolved = EngineArgs(**kwargs).create_engine_config()
        sizes = resolved.compilation_config.cudagraph_capture_sizes
        dump(out/'resolved_config.json', dict(capture_sizes=sizes,
            max_capture_size=resolved.compilation_config.max_cudagraph_capture_size,
            cudagraph_mode=str(resolved.compilation_config.cudagraph_mode),
            attention_backend=str(resolved.attention_config.backend)))
        assert sizes == [1,2,4,5,8,10,16], ('Default schedule drift', sizes)
        state['stage'] = 'engine_init'; save(); llm = LLM(**kwargs)
        def rpc(method, *args):
            assert not llm.llm_engine.has_unfinished_requests()
            value = llm.collective_rpc(method, timeout=45, args=args)
            assert len(value) == 1; return value[0]
        state['worker_inspect'] = rpc('controller_history_control', 'inspect')
        state['profile_detail'] = rpc('controller_profile_detail'); save()
        assert state['worker_inspect']['kv_types'] == ['FullAttentionSpec']
        assert state['profile_detail']['backend'] == 'TRITON_ATTN'
        assert state['profile_detail']['captured_token_counts'] == [1,2,4,5,8,10]
        state['stage'] = 'profile_reconstruction'; save()
        analysis = analyze(out); dump(out/'independent_profile_analysis.json', analysis)
        final = next(x for x in analysis['blocks'] if not x['profile_only'])
        assert final['cost_tables'] == state['profile_detail']['cost_tables']
        state['profile_gate_passed'] = True; save()
        tok = AutoTokenizer.from_pretrained(root/cfg['target'], local_files_only=True)
        with (out/'answers.jsonl').open('x') as stream:
            for item in p['answers']:
                assert state['engineering_answers'] < 2
                state['stage'] = item['kind']; save()
                prompt = tok.apply_chat_template([{'role':'user','content':item['prompt']}],
                    tokenize=False, add_generation_prompt=True, enable_thinking=False)
                assert tok.encode(prompt) == baseline['prompt_ids']
                result = llm.generate([prompt], SamplingParams(temperature=0, top_p=1,
                    seed=42, max_tokens=32, ignore_eos=True), use_tqdm=False)
                assert len(result) == 1 and len(result[0].outputs) == 1
                answer = result[0].outputs[0]
                row = dict(kind=item['kind'], prompt=prompt, prompt_ids=tok.encode(prompt),
                    token_ids=list(answer.token_ids), text=answer.text,
                    finish_reason=answer.finish_reason)
                stream.write(json.dumps(row)+'\n'); stream.flush()
                state['engineering_answers'] += 1
                state['generated_tokens'] += len(row['token_ids']); save()
                assert len(row['token_ids']) == 32 and state['generated_tokens'] <= 64
                assert row['token_ids'] == baseline['token_ids'], 'Baseline token mismatch'
        state['profile_after'] = rpc('controller_profile_detail')
        assert state['profile_after'] == state['profile_detail']
        state.update(status='complete', stage='complete', baseline_token_ids_exact=True,
            observed_blocks=len(analysis['blocks']), timing_samples=analysis['total_samples'],
            single_request_verify_1to5_flat=analysis['single_request_verify_1to5_flat'],
            no_latency_harm_claim=True)
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
        (out/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0)
        if llm is not None:
            try: llm.llm_engine.engine_core.shutdown()
            except Exception as exc: state['shutdown_note'] = repr(exc)
        state['elapsed_seconds'] = time.monotonic()-start; save()
        dump(out/'manifest.json', {p.name:sha(p) for p in out.iterdir() if p.is_file()})
        print(json.dumps({k:v for k,v in state.items() if k not in ['profile_detail','profile_after']}, indent=2), flush=True)
    return 0 if state['status'] == 'complete' else 1


if __name__ == '__main__': raise SystemExit(main())
