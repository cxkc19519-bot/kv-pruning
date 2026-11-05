"""Bounded engineering-only GPU acceptance of the pinned lazy HF adapter."""
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
import subprocess
import time
import traceback
from collections import Counter
from reliability_system_core import require
from reliability_system_adapters import hash_json
from reliability_hf_orchestrator import HFOrchestrator, case_binding
from reliability_qwen_hf_backend import QwenHFBackend


def sha(data): return hashlib.sha256(data).hexdigest()
def save(path, value): path.write_text(json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2)+'\n')
def append(path, value):
    with path.open('a') as f: f.write(json.dumps(value, ensure_ascii=True, allow_nan=False)+'\n')


def check_trace(case, budget, ids, trace):
    require(isinstance(trace, list) and len(trace) == len(ids), 'trace_count')
    physical = budget['effective_slots']; n = case['prefix_tokens']; suffix = len(case['input_ids'])-n
    for step, row in enumerate(trace):
        width = suffix if step == 0 else 1
        logical = n if step == 0 else n+suffix+step-1
        require(row == dict(step=step, physical_start=physical, logical_start=logical, input_width=width), 'independent_trace_geometry')
        physical += width
    return physical


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--proposal', required=True); ap.add_argument('--execute-engineering', action='store_true'); a = ap.parse_args()
    r = Path(__file__).resolve().parent.parent
    require(a.execute_engineering and str(r) == '/home/user/jhk/project/Directional Exploration/kv-pruning', 'server_engineering_only')
    raw = (r/a.proposal).read_bytes(); cfg = json.loads(raw); out = r/cfg['run']
    require(out.resolve().parent == (r/'results').resolve(), 'output_boundary'); out.mkdir(exist_ok=False)
    started = time.monotonic(); engine = None; backend = None; active = None
    state = dict(status='running', stage='verify_inputs', pid=os.getpid(), main_outputs=0, engineering_outputs=0, raw_outputs=0, generated_tokens=0, failed_model_attempts=0)
    def timeout(*args): raise TimeoutError('engineering_wall_cap')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(cfg['wall_seconds'])
    try:
        save(out/'summary.json', state); (out/'proposal_snapshot.json').write_bytes(raw)
        require(cfg['execution_enabled'] is True and cfg['scope'] == 'engineering_only' and cfg['main_answers_max'] == 0 and cfg['engineering_answers_max'] == 14, 'registered_scope')
        require(os.environ.get('KV_ENGINEERING_OUTER_WATCHDOG') == 'registered_660_seconds', 'outer_watchdog_required')
        require(sha(Path(__file__).read_bytes()) == cfg['runner_sha256'], 'runner_pin')
        (out/'source_runner.py').write_bytes(Path(__file__).read_bytes())
        for path, expected in cfg['inputs'].items(): require(sha((r/path).read_bytes()) == expected, 'input_pin:'+path)
        save(out/'input_manifest.json', cfg['inputs'])
        descriptor = json.loads((r/cfg['descriptor']).read_text())
        for path, expected in descriptor['source_files'].items():
            data = (r/path).read_bytes(); require(sha(data) == expected, 'source_pin:'+path)
            (out/('source_'+Path(path).name)).write_bytes(data)
        oldscope = json.loads((r/cfg['dry_runtime_scope']).read_text())
        material = dict(version='hf_engineering_registered_v1', parent_dry_runtime=oldscope['runtime_digest'], proposal_sha256=sha(raw), runner_sha256=cfg['runner_sha256'])
        runtime = hash_json(material); save(out/'registered_runtime_scope.json', dict(runtime_digest=runtime, material=material))
        descriptor.update(execution_enabled=True, separate_GPU_execution_registered=True, outer_GPU_watchdog_registered=True, registered_runtime_digest=runtime)
        descriptor['source_files']['scripts/run_hf_backend_engineering.py'] = cfg['runner_sha256']
        save(out/'backend_execution_snapshot.json', descriptor)
        prepared = {x['case_id']: x for x in map(json.loads, (r/cfg['cases']).read_text().splitlines())}
        cases = []
        for x in json.loads((r/cfg['tokenized']).read_text()):
            c = dict(x); require(c['split_role'] in ['engineering', 'development'], 'sealed_input')
            c['context_group_id'] = prepared[c['case_id']]['context_group_id']; cases.append(c)
        eng = [c for c in cases if c['split_role'] == 'engineering']
        require(len(eng) == 2 and [c['case_id'] for c in eng] == cfg['engineering_case_ids'] and len(cases) == 14, 'engineering_selection')
        save(out/'prepared_bindings.json', [dict(case_id=c['case_id'], role=c['split_role'], case_input_digest=case_binding(c)) for c in cases])
        specs = json.loads((r/cfg['specs']).read_text())['specs']
        oldrefs = {}
        for path, full in [(cfg['old_full_engineering'], True), (cfg['old_compact_engineering'], False)]:
            for row in map(json.loads, (r/path).read_text().splitlines()):
                if row.get('status') != 'ok': continue
                name = row['condition']
                if full: condition, branch = 'full', name
                elif name.endswith('_native'): condition, branch = name[:-7], 'native'
                else: condition, branch = name, 'custom'
                key = (row['case_id'], condition, branch); require(key not in oldrefs, 'duplicate_old_reference'); oldrefs[key] = row
        require(len(oldrefs) == 14, 'old_reference_coverage')
        baseline_hashes = {}; prefill_checks = []; map_checks = []; raw_rows = []; old_comparisons = []

        class AuditedBackend(QwenHFBackend):
            def tensor_hash(self, cache):
                h = hashlib.sha256()
                for layer in cache.layers:
                    for t in (layer.keys, layer.values): h.update(t.contiguous().view(self.torch.uint8).cpu().numpy().tobytes())
                return h.hexdigest()

            def _load(self):
                first = self.model is None
                if first: save(out/'loading_attempt.json', dict(started=True, gpu_uuid=self.config['gpu_uuid']))
                super()._load()
                if not first: return
                mc = self.model.config
                require(mc.model_type == 'qwen2' and mc.num_hidden_layers == 28 and mc.num_key_value_heads == 4 and mc.num_attention_heads == 28 and mc.hidden_size//mc.num_attention_heads == 128, 'independent_actual_layout')
                require(self.model.config._attn_implementation == 'sdpa' and str(self.model.device) == 'cuda:0', 'actual_SDPA_device')
                save(out/'actual_runtime.json', dict(observed=self.actual_runtime, model_config=mc.to_dict(), generation_config=self.model.generation_config.to_dict(), python=sys.version, actual_attention_heads=mc.num_attention_heads, model_parameter_dtypes=sorted({str(p.dtype) for p in self.model.parameters()}), tf32_matmul=self.torch.backends.cuda.matmul.allow_tf32, tf32_cudnn=self.torch.backends.cudnn.allow_tf32, GPU=self.torch.cuda.get_device_properties(0).name))
                original_prefill = self.prefill; original_maps = self.build_maps
                def observed_prefill(model, ids):
                    ref, scores = original_prefill(model, ids)
                    from trec_context_gate import prefill
                    rawref = prefill(model, ids)
                    equal = len(rawref.layers) == len(ref.layers) and all(self.torch.equal(x.keys, y.keys) and self.torch.equal(x.values, y.values) for x, y in zip(rawref.layers, ref.layers))
                    require(equal, 'score_hook_changed_reference'); del rawref
                    cid = active['case_id']; digest = self.tensor_hash(ref); baseline_hashes[cid] = digest
                    payload = gzip.compress(json.dumps({str(k): v.tolist() for k, v in scores.items()}, separators=(',', ':'), allow_nan=False).encode(), mtime=0)
                    (out/(cid+'.scores.json.gz')).write_bytes(payload)
                    prefill_checks.append(dict(case_id=cid, prefix_ids_sha256=hash_json(ids), prefix_tokens=len(ids), unhooked_reference_equal=True, reference_sha256=digest, score_archive_sha256=sha(payload)))
                    save(out/'prefill_checks.json', prefill_checks)
                    return ref, scores
                def observed_maps(scores, group, n, metadata, conditions):
                    maps = original_maps(scores, group, n, metadata, conditions)
                    for condition, layers in maps.items():
                        key = active['case_id']+'.'+condition; data = {str(i): t.tolist() for i, t in layers.items()}
                        for rows in data.values():
                            require(len(rows) == 1 and len(rows[0]) == 4, 'map_head_shape')
                            for indices in rows[0]:
                                required = set(range(min(4, n))) | set(range(max(0, n-64), n))
                                require(len(indices) == n//2 and indices == sorted(set(indices)) and all(0 <= z < n for z in indices) and required <= set(indices), 'independent_map_invariants')
                        payload = gzip.compress(json.dumps(data, separators=(',', ':')).encode(), mtime=0)
                        path = out/(key+'.maps.json.gz')
                        if path.exists(): require(path.read_bytes() == payload, 'map_changed_between_paths')
                        else: path.write_bytes(payload)
                        map_checks.append(dict(case_id=active['case_id'], condition_id=condition, path=active['path'], layer_heads=112, map_archive_sha256=sha(payload)))
                        save(out/'map_checks.json', map_checks)
                    return maps
                self.prefill = observed_prefill; self.build_maps = observed_maps

            def execute(self, request, case, spec, budget):
                append(out/'model_attempts.jsonl', request)
                try: result = super().execute(request, case, spec, budget)
                except BaseException as exc:
                    state['failed_model_attempts'] += 1; append(out/'failed_attempts.jsonl', dict(request=request, error=repr(exc))); raise
                raw_rows.append(dict(request=request, result=result)); append(out/'raw_engineering.jsonl', raw_rows[-1])
                state['raw_outputs'] += 1; state['generated_tokens'] += len(result['ids']); save(out/'summary.json', state)
                require(state['raw_outputs'] <= 14 and state['generated_tokens'] <= 1792, 'output_cap')
                require(len(result['ids']) <= 128 and result['truncated'] == (result['ids'][-1] not in descriptor['decode']['eos_token_id']), 'independent_termination')
                prefix = result['actual_prefix_kv_bytes']; final = result['final_live_kv_bytes']
                if request['path'] == 'native_whole': require(prefix is None and final is None, 'whole_bytes_unknown')
                else:
                    require(prefix == budget['effective_slots']*57344, 'independent_prefix_bytes')
                    physical = budget['effective_slots']+len(case['input_ids'])-case['prefix_tokens']+len(result['ids'])-1
                    if result['trace'] is not None: require(check_trace(case, budget, result['ids'], result['trace']) == physical, 'independent_final_geometry')
                    require(final == physical*57344, 'independent_final_bytes')
                    require(self.tensor_hash(self.reference) == baseline_hashes[case['case_id']], 'reference_content_changed')
                prior = oldrefs[(case['case_id'], spec['condition_id'], request['path'])]
                comparison = dict(case_id=case['case_id'], condition_id=spec['condition_id'], path=request['path'], tokens_equal=prior['ids'] == result['ids'], termination_equal=prior['truncated'] == result['truncated'], trace_equal=prior.get('trace') == result['trace'])
                old_comparisons.append(comparison); save(out/'old_reference_comparisons.json', old_comparisons)
                require(all(comparison[k] for k in ('tokens_equal', 'termination_equal', 'trace_equal')), 'old_reference_changed')
                return result

        def factory():
            nonlocal backend
            backend = AuditedBackend(descriptor); return backend
        policy = dict(mode='registered_gpu', execution_enabled=True, bootstrap_generation_enabled=True, DEV_generation_enabled=False, runtime_digest=runtime, max_engineering_calls=14, max_DEV_calls=0, max_input_tokens=2048, wall_seconds=cfg['wall_seconds'])
        engine = HFOrchestrator(cases, specs, runtime, policy, factory)
        save(out/'execution_snapshot.json', dict(policy=policy, input_bindings=out.joinpath('prepared_bindings.json').name, protocol_sha256=sha(raw), runner_sha256=cfg['runner_sha256'], development_generation_enabled=False, sealed_inference=False))
        blocked = []; state['stage'] = 'GPU_engineering'; save(out/'summary.json', state)
        for c in eng:
            for spec in specs:
                name = spec['condition_id']; plan = engine._plan(c, name)
                if plan['budget']['state'] == 'infeasible_budget':
                    blocked.append(plan); save(out/'blocked_engineering.json', blocked); continue
                for branch in spec['required_paths']:
                    active = engine.request(c['case_id'], name, 'engineering', branch)
                    save(out/'active_request.json', active)
                    response = engine.dispatch(active); append(out/'accepted_engineering.jsonl', response)
                    state['engineering_outputs'] += 1
                    save(out/'engineering_evidence.json', [engine.evidence(s['condition_id']) for s in specs]); save(out/'summary.json', state)
                    active = None
        require(state['engineering_outputs'] == state['raw_outputs'] == 14 and len(blocked) == 4 and len(prefill_checks) == 2 and len(map_checks) == 8, 'engineering_output_coverage')
        evidence = [engine.evidence(s['condition_id']) for s in specs]
        require(sum(x['status'] == 'verified' for x in evidence) == 3 and sum(x['status'] == 'unverified_budget_infeasible' for x in evidence) == 2, 'engineering_condition_coverage')
        dev = []
        for c in cases:
            if c['split_role'] != 'development': continue
            for s in specs:
                branch = 'custom_split' if s['condition_id'] == 'full' else 'custom'
                dev.append(engine.decision(engine.request(c['case_id'], s['condition_id'], 'development', branch)))
        save(out/'DEV_admission_only.json', dev)
        require(Counter(x['decision']['admission_state'] for x in dev) == {'eligible_for_configured_run':36, 'blocked_budget':20, 'blocked_engineering_unverified':4}, 'post_engineering_DEV_decisions')
        require(engine.phase_calls == dict(engineering=14, development=0) and engine.loader_attempts == 1, 'stage_call_counts')
        for path, expected in cfg['inputs'].items(): require(sha((r/path).read_bytes()) == expected, 'input_changed:'+path)
        state.update(status='complete', stage='complete', verified_conditions=3, protected_conditions_unverified=2, protected_budget_blocked_case_conditions=4, sequence_verified_but_truncated_cases=sum(x['sequence_verified_but_truncated_cases'] for x in evidence), main_outputs=0, independent_scientific_confirmation=False, GPU_backend_scope='Only these2 engineering cases and3 feasible conditions;not task quality or protected/second-model validation')
    except BaseException as exc:
        state.update(status='failed', error=repr(exc), active_request=active)
        (out/'failure.txt').write_text(traceback.format_exc())
        if engine is not None: save(out/'engineering_evidence_at_stop.json', [engine.evidence(s['condition_id']) for s in engine.specs.values()])
    finally:
        signal.alarm(0)
        if backend is not None:
            backend.model = None; backend.reference = None; backend.scores = None
            if hasattr(backend, 'torch'):
                gc.collect(); backend.torch.cuda.empty_cache()
        state['elapsed_seconds'] = time.monotonic()-started
        if engine is not None: state['dispatch_counts'] = dict(factory_attempts=engine.loader_attempts, backend_calls=engine.backend_calls, phase_calls=engine.phase_calls)
        save(out/'summary.json', state)
        files = [p for p in out.iterdir() if p.is_file()]
        if len(files) >= cfg['archive_files_max'] or sum(p.stat().st_size for p in files) >= cfg['archive_bytes_max']:
            state.update(status='failed', archive_bounds_exceeded=True); save(out/'summary.json', state)
        save(out/'manifest.json', {p.name:sha(p.read_bytes()) for p in files})
        print(json.dumps(state), flush=True)
    return 0 if state['status'] == 'complete' else 1


if __name__ == '__main__': raise SystemExit(main())
