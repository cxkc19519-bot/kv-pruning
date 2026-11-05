"""At most36 same-generator DEV cells, dual scoring and scalar report acceptance."""
import sys
sys.dont_write_bytecode = True
import argparse
import copy
import gc
import gzip
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback
from collections import Counter
from reliability_system_core import SCHEMA, require, metric, measure, summarize, ContractError
from reliability_system_adapters import hash_json
from reliability_hf_orchestrator import HFOrchestrator, case_binding
from reliability_qwen_hf_backend import QwenHFBackend
from reliability_engineering_resume import restore_checkpoint, validate_observations
from answer_format_task import score_response


def sha(data): return hashlib.sha256(data).hexdigest()
def save(path, value): path.write_text(json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2)+'\n')
def append(path, value):
    with path.open('a') as f: f.write(json.dumps(value, ensure_ascii=True, allow_nan=False)+'\n')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--proposal', required=True); ap.add_argument('--execute-DEV', action='store_true'); a = ap.parse_args()
    r = Path(__file__).resolve().parent.parent
    require(a.execute_DEV and str(r) == '/home/user/jhk/project/Directional Exploration/kv-pruning', 'server_DEV_only')
    raw = (r/a.proposal).read_bytes(); cfg = json.loads(raw); out = r/cfg['run']
    require(out.resolve().parent == (r/'results').resolve(), 'output_boundary'); out.mkdir(exist_ok=False)
    started = time.monotonic(); engine = backend = active = None
    state = dict(status='running', stage='verify_inputs', pid=os.getpid(), main_outputs=0, engineering_outputs=0, raw_outputs=0, generated_tokens=0, blocked_cells=0)
    def timeout(*args): raise TimeoutError('DEV_wall_cap')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(cfg['wall_seconds'])
    try:
        save(out/'summary.json', state); (out/'proposal_snapshot.json').write_bytes(raw)
        require(cfg['scope'] == 'DEV_system_acceptance' and cfg['execution_enabled'] is True and cfg['main_answers_max'] == 36 and cfg['engineering_answers_max'] == 0, 'registered_DEV_scope')
        require(os.environ.get('KV_DEV_OUTER_WATCHDOG') == 'registered_660_seconds', 'outer_watchdog_required')
        for path, expected in {**cfg['inputs'], **cfg['execution_sources']}.items():
            b = (r/path).read_bytes(); require(sha(b) == expected, 'pin:'+path)
            if path.startswith('scripts/'): (out/('source_'+Path(path).name)).write_bytes(b)
        save(out/'input_manifest.json', cfg['inputs'])
        checkpoint = r/cfg['engineering_checkpoint']; read = lambda name:json.loads((checkpoint/name).read_text())
        descriptor = read('backend_execution_snapshot.json'); runtime = read('registered_runtime_scope.json')['runtime_digest']
        # Generator identity remains exactly the validated checkpoint; the new control/scoring protocol has its own digest.
        execution_scope = dict(proposal_sha256=sha(raw), execution_sources=cfg['execution_sources'], generator_runtime_digest=runtime)
        save(out/'execution_scope.json', dict(execution_protocol_digest=hash_json(execution_scope), material=execution_scope, generator_identity_unchanged=True))
        for path, expected in descriptor['source_files'].items():
            b = (r/path).read_bytes(); require(sha(b) == expected, 'generator_source:'+path)
            (out/('source_'+Path(path).name)).write_bytes(b)
        descriptor['source_files'].update(cfg['execution_sources']); save(out/'backend_execution_snapshot.json', descriptor)
        source = {x['case_id']:x for x in map(json.loads, (r/cfg['cases']).read_text().splitlines())}
        cases = [dict(x, context_group_id=source[x['case_id']]['context_group_id']) for x in json.loads((r/cfg['tokenized']).read_text())]
        dev = [c for c in cases if c['split_role'] == 'development']; require(len(cases) == 14 and len(dev) == 12 and not any(c['split_role'] not in ['engineering','development'] for c in cases), 'case_roles')
        specs = json.loads((r/cfg['specs']).read_text())['specs']
        policy = dict(mode='registered_gpu', execution_enabled=True, bootstrap_generation_enabled=False, DEV_generation_enabled=True, runtime_digest=runtime, max_engineering_calls=0, max_DEV_calls=36, max_input_tokens=2048, wall_seconds=cfg['wall_seconds'])
        oldrows = {}
        for path in cfg['old_DEV_generations']:
            for row in map(json.loads, (r/path).read_text().splitlines()):
                if row['status'] == 'ok' and not row['condition'].endswith('_system_pinned'):
                    key = (row['case_id'], row['condition']); require(key not in oldrows, 'duplicate_old_DEV'); oldrows[key] = row
        require(len(oldrows) == 36, 'old_DEV_coverage')
        refs = {}; prefill_checks = []; map_checks = []; comparisons = []; records = []; cells = []

        class DEVBackend(QwenHFBackend):
            def tensor_hash(self, cache):
                h = hashlib.sha256()
                for layer in cache.layers:
                    for t in (layer.keys, layer.values): h.update(t.contiguous().view(self.torch.uint8).cpu().numpy().tobytes())
                return h.hexdigest()

            def _load(self):
                first = self.model is None
                if first: save(out/'loading_attempt.json', dict(started=True, GPU=self.config['gpu_uuid']))
                super()._load()
                if not first: return
                require(self.actual_runtime == read('actual_runtime.json')['observed'], 'actual_generator_runtime_changed')
                actual_config = json.loads(json.dumps(self.model.config.to_dict()))
                save(out/'config_JSON_comparison.json', dict(entire_config_JSON_equal=actual_config == read('actual_runtime.json')['model_config'], comparison='whole-config JSON roundtrip, no fields dropped'))
                require(actual_config == read('actual_runtime.json')['model_config'], 'actual_model_config_changed')
                from transformers import AutoTokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(self.config['model_path'], local_files_only=True, trust_remote_code=False, use_fast=True)
                for c in dev:
                    prompt = source[c['case_id']]['prompt']
                    ids = self.tokenizer.apply_chat_template([dict(role='system',content=prompt['system']),dict(role='user',content=prompt['user'])], tokenize=True, add_generation_prompt=True)
                    require(ids == c['input_ids'], 'DEV_retokenization_changed')
                save(out/'actual_runtime.json', dict(observed=self.actual_runtime, model_config=self.model.config.to_dict(), generator_runtime_equal_checkpoint=True, retokenized_DEV_cases=12, model_parameter_dtypes=sorted({str(p.dtype) for p in self.model.parameters()}), tf32_matmul=self.torch.backends.cuda.matmul.allow_tf32, tf32_cudnn=self.torch.backends.cudnn.allow_tf32, python=sys.version))
                original_prefill, original_maps = self.prefill, self.build_maps
                def observed_prefill(model, ids):
                    ref, scores = original_prefill(model, ids); cid = active['case_id']; refs[cid] = self.tensor_hash(ref)
                    payload = gzip.compress(json.dumps({str(k):v.tolist() for k,v in scores.items()},separators=(',',':'),allow_nan=False).encode(),mtime=0)
                    (out/(cid+'.scores.json.gz')).write_bytes(payload)
                    prefill_checks.append(dict(case_id=cid, reference_sha256=refs[cid], score_archive_sha256=sha(payload)))
                    save(out/'prefill_checks.json', prefill_checks); return ref, scores
                def observed_maps(scores, group, n, metadata, conditions):
                    maps = original_maps(scores, group, n, metadata, conditions)
                    for name, layers in maps.items():
                        payload = gzip.compress(json.dumps({str(k):v.tolist() for k,v in layers.items()},separators=(',',':')).encode(),mtime=0)
                        (out/(active['case_id']+'.'+name+'.maps.json.gz')).write_bytes(payload)
                        map_checks.append(dict(case_id=active['case_id'], condition_id=name, map_archive_sha256=sha(payload)))
                        save(out/'map_checks.json', map_checks)
                    return maps
                self.prefill, self.build_maps = observed_prefill, observed_maps

            def execute(self, request, case, spec, budget):
                require(case['split_role'] == 'development' and not spec['protect_system'] and request['phase'] == 'development', 'non_DEV_or_protected_model_call')
                append(out/'model_attempts.jsonl', request)
                result = super().execute(request, case, spec, budget)
                append(out/'raw_generations.jsonl', dict(request=request, result=result))
                state['raw_outputs'] += 1; state['generated_tokens'] += len(result['ids']); save(out/'summary.json', state)
                require(state['raw_outputs'] <= 36 and state['generated_tokens'] <= 4608 and 0 < len(result['ids']) <= 128, 'output_cap')
                require(result['truncated'] == (result['ids'][-1] not in self.config['decode']['eos_token_id']), 'termination')
                physical = budget['effective_slots']; n = case['prefix_tokens']; suffix = len(case['input_ids'])-n
                require(result['actual_prefix_kv_bytes'] == physical*57344 and len(result['trace']) == len(result['ids']), 'KV_trace_count')
                for step, trace in enumerate(result['trace']):
                    width = suffix if step == 0 else 1; logical = n if step == 0 else n+suffix+step-1
                    require(trace == dict(step=step, physical_start=physical, logical_start=logical, input_width=width), 'trace_geometry'); physical += width
                require(result['final_live_kv_bytes'] == physical*57344 and self.tensor_hash(self.reference) == refs[case['case_id']], 'KV_final_or_reference_changed')
                prior = oldrows[(case['case_id'],spec['condition_id'])]
                check = dict(case_id=case['case_id'],condition_id=spec['condition_id'],tokens_equal=result['ids']==prior['ids'],termination_equal=result['truncated']==prior['truncated'],trace_equal=result['trace']==prior['trace'])
                comparisons.append(check); save(out/'old_DEV_comparisons.json', comparisons)
                require(all(check[k] for k in ['tokens_equal','termination_equal','trace_equal']), 'old_DEV_changed')
                return result

        def factory():
            nonlocal backend
            backend = DEVBackend(descriptor); return backend
        engine = HFOrchestrator(cases, specs, runtime, policy, factory)
        # Negative payload tests never touch the live engine or construct a backend.
        checkpoint_raw = list(map(json.loads,(checkpoint/'raw_engineering.jsonl').read_text().splitlines()))
        checkpoint_accepted = list(map(json.loads,(checkpoint/'accepted_engineering.jsonl').read_text().splitlines()))
        bindings = read('prepared_bindings.json'); evidence = read('engineering_evidence.json'); tests = []
        for i in range(8):
            e = HFOrchestrator(cases,specs,runtime,dict(policy,mode='dry_run'),None)
            rr, aa, bb, ev = map(copy.deepcopy,[checkpoint_raw,checkpoint_accepted,bindings,evidence])
            if i == 1: rr[0]['result']['ids'][0] += 1
            if i == 2: rr[0]['request']['runtime_digest'] = '0'*64
            if i == 3: e.cases[cases[0]['case_id']]['context_group_id'] = '0'*64
            if i == 4: rr[-1] = copy.deepcopy(rr[0]); aa[-1] = copy.deepcopy(aa[0])
            if i == 5: aa[0]['result']['truncated'] = not aa[0]['result']['truncated']
            if i == 6: ev[0]['verified_engineering_cases'] = 0
            if i == 7: bb.pop()
            rejected = False
            try: validate_observations(e,rr,aa,bb,ev)
            except ContractError: rejected = True
            require(rejected == (i != 0) and e.loader_attempts == e.backend_calls == 0, 'resume_negative_case:'+str(i))
            tests.append(dict(id='R'+str(i+1).zfill(2),passed=True,invalid_payload_rejected=rejected,model_calls=0))
        save(out/'resume_software_acceptance.json', tests)
        resume = restore_checkpoint(engine,r,cfg); save(out/'resume_provenance.json',resume)
        save(out/'restored_engineering_evidence.json',[engine.evidence(s['condition_id']) for s in specs])
        save(out/'execution_snapshot.json',dict(policy=policy,generator_runtime_digest=runtime,execution_protocol_digest=hash_json(execution_scope),restored_engineering_observations=14,new_engineering_calls=0,DEV_answers_max=36,sealed_inference=False))
        plans = []
        for c in dev:
            for spec in specs:
                name = spec['condition_id']; req = engine.request(c['case_id'],name,'development','custom_split' if name == 'full' else 'custom')
                plans.append(engine.decision(req))
        require(Counter(x['decision']['admission_state'] for x in plans) == {'eligible_for_configured_run':36,'blocked_budget':20,'blocked_engineering_unverified':4}, 'DEV_admission_plan')
        save(out/'admission_plan.json',plans); state['stage'] = 'DEV_generation'; save(out/'summary.json',state)
        comparison_digest = hash_json(dict(generator_runtime_digest=runtime,protocol_role='same12DEV_system_integration'))
        for item in plans:
            req = item['request']; c = engine.cases[req['case_id']]; original = source[c['case_id']]; active = req
            response = engine.dispatch(req)
            if response['state'] == 'blocked':
                require(not response['model_called'], 'blocked_model_call'); state['blocked_cells'] += 1
                execution = 'infeasible_budget' if item['decision']['admission_state'] == 'blocked_budget' else 'not_run'
                result_row = dict(case_id=c['case_id'],condition=req['condition_id'],status=execution,reason=item['decision']['reason'],truncated=None,metrics=None)
                raw_metrics = {}; prefix_bytes = final_bytes = None; reason = result_row['reason']
            else:
                require(response['state'] == 'executed', 'unexpected_dispatch_state')
                result = response['result']; ids = result['ids']; eos = set(descriptor['decode']['eos_token_id'])
                text = backend.tokenizer.decode(ids[:-1] if ids[-1] in eos else ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
                raw_metrics = score_response(text,[x['text'] for x in original['answers']])
                append(out/'scored_generations.jsonl',dict(case_id=c['case_id'],condition=req['condition_id'],text=text,ids=ids,truncated=result['truncated'],metrics=raw_metrics,prompt_sha256=c['prompt_sha256'],gold_sha256=original['gold_sha256']))
                require(raw_metrics == oldrows[(c['case_id'],req['condition_id'])]['metrics'], 'old_DEV_scoring_changed')
                execution = 'ok'; reason = None; prefix_bytes = result['actual_prefix_kv_bytes']; final_bytes = result['final_live_kv_bytes']
                result_row = dict(case_id=c['case_id'],condition=req['condition_id'],status='ok',truncated=result['truncated'],metrics=raw_metrics)
                state['main_outputs'] += 1
            append(out/'dispatch_log.jsonl',response); cells.append(result_row); append(out/'cell_results.jsonl',result_row)
            metrics = dict(task=metric(raw_metrics.get('em'),'squad_v11_bidaf_pinned_em_v1',reason=raw_metrics.get('reason',reason or 'not_executed')),constraint=metric(raw_metrics.get('format'),'json_answer_format_v1',reason=reason or 'not_executed'),f1=metric(raw_metrics.get('f1'),'squad_v11_bidaf_pinned_f1_v1','unit_interval',raw_metrics.get('reason',reason or 'not_executed')))
            record = dict(schema=SCHEMA,cohort_id='HF_system_acceptance_squad_DEV12',case_id=c['case_id'],condition_id=req['condition_id'],execution_state=execution,truncated=result_row['truncated'],reason=reason,input_digest=c['prompt_sha256'],gold_digest=original['gold_sha256'],comparison_digest=comparison_digest,metrics=metrics,costs=dict(prefix_kv_bytes=measure(prefix_bytes,'no_output'),final_live_kv_bytes=measure(final_bytes,'no_output'),peak_gpu_bytes=measure(None,'not_benchmarked'),latency_ms=measure(None,'not_benchmarked'),extra_buffer_peak_bytes=measure(None,'not_benchmarked')),origin=dict(raw_run=cfg['run'],generator_runtime_digest=runtime))
            records.append(record); append(out/'normalized_records.jsonl',record); active = None; save(out/'summary.json',state)
        require(state['main_outputs'] == state['raw_outputs'] == 36 and state['blocked_cells'] == 24 and engine.phase_calls == dict(engineering=0,development=36), 'final_call_coverage')
        require(len(prefill_checks) == 12 and len(map_checks) == 24, 'score_map_coverage')
        plan = dict(cohort_id='HF_system_acceptance_squad_DEV12',case_ids=[c['case_id'] for c in dev],conditions=[dict(condition_id=s['condition_id'],budget_group='half_prefix' if s['condition_id']!='full' else None) for s in specs],metrics={k:dict(kind=v['kind'],metric_id=v['metric_id']) for k,v in records[0]['metrics'].items()},scientific_role='system_end_to_end_acceptance_existing12DEV_not_independent_confirmation',context_group_ids=[c['context_group_id'] for c in dev])
        report = summarize(plan,records); report.update(inference_performed=True,task_text_rescored=True)
        delivery = {s['condition_id']:dict(scheduled=12,generated=sum(x['status']=='ok' for x in cells if x['condition']==s['condition_id']),joint_delivered=sum(x['status']=='ok' and not x['truncated'] and x['metrics']['joint_success'] for x in cells if x['condition']==s['condition_id'])) for s in specs}
        save(out/'plan.json',plan); save(out/'report.json',dict(paired=report,delivery=delivery,execution_scope='36newDEVanswers/24blockedcells;14engineering observations restored,0newengineering',independent_confirmation=False))
        lines=['# HF DEV end-to-end acceptance','','| Condition | Generated | Budget blocked | Not run | Task pass/evaluated | Format pass/evaluated | Joint/12 |','| --- | --- | --- | --- | --- | --- | --- |']
        for name, row in report['conditions'].items():
            e=row['execution'];t=row['metrics']['task'];f=row['metrics']['constraint'];lines.append(f"| {name} | {e['ok']} | {e['infeasible_budget']} | {e['not_run']} | {t['pass_count']}/{t['evaluated_count']} | {f['pass_count']}/{f['evaluated_count']} | {delivery[name]['joint_delivered']}/12 |")
        lines+=['','Existing12DEV integration acceptance only,not independent scientific confirmation. Protected conditions have0newoutputs;20budget blocks and4unverified-engineering blocks remain. Truncated/metric-N/A excluded explicitly;performance unknown.']
        (out/'report.md').write_text('\n'.join(lines)+'\n')
        for path, expected in {**cfg['inputs'],**cfg['execution_sources']}.items(): require(sha((r/path).read_bytes())==expected,'input_changed:'+path)
        state.update(status='complete',stage='complete',resume_software_cases_passed=8,restored_engineering_observations=14,planned_cells=60,normalized_records=60,independent_confirmation=False)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc),active_request=active); (out/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0)
        if backend is not None:
            backend.model=None;backend.reference=None;backend.scores=None
            if hasattr(backend,'torch'):gc.collect();backend.torch.cuda.empty_cache()
        state['elapsed_seconds']=time.monotonic()-started
        if engine is not None:state['dispatch_counts']=dict(factory_attempts=engine.loader_attempts,backend_calls=engine.backend_calls,phase_calls=engine.phase_calls)
        save(out/'summary.json',state);files=[p for p in out.iterdir() if p.is_file()]
        if len(files)>=cfg['archive_files_max'] or sum(p.stat().st_size for p in files)>=cfg['archive_bytes_max']:state.update(status='failed',archive_bounds_exceeded=True);save(out/'summary.json',state)
        save(out/'manifest.json',{p.name:sha(p.read_bytes()) for p in files});print(json.dumps(state),flush=True)
    return 0 if state['status']=='complete' else 1


if __name__ == '__main__':raise SystemExit(main())
