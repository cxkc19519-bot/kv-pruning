"""Bounded Qwen48 Full-first study. Engineering evidence is produced anew."""
import sys
sys.dont_write_bytecode = True
import argparse
import gc
import gzip
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback
from reliability_system_core import require
from reliability_system_adapters import hash_json
from reliability_hf_orchestrator import HFOrchestrator
from reliability_qwen_hf_backend import QwenHFBackend
from reliability_squad48_study import StudyDispatcher, ROLE, NAMES, scalar_report
from squad48_study_acceptance import run_acceptance


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2) + '\n')


def append(path, value):
    with path.open('a') as f:
        f.write(json.dumps(value, ensure_ascii=True, allow_nan=False) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--proposal-sha256', required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    require(args.execute and str(root) == '/home/user/jhk/project/Directional Exploration/kv-pruning', 'registered_server_only')
    raw = (root / 'configs/squad48-gpu-study-v1.json').read_bytes()
    require(sha(raw) == args.proposal_sha256, 'proposal_pin')
    cfg = json.loads(raw)
    out = root / cfg['run']
    require(out.resolve().parent == (root / 'results').resolve(), 'output_boundary')
    out.mkdir(exist_ok=False)
    start = time.monotonic()
    backend = engine = study = None
    state = dict(status='running', stage='pins', pid=os.getpid(), main_outputs=0, engineering_outputs=0,
                 generated_tokens=0, failed_model_attempts=0, Full_support=None)
    def timeout(*unused):
        raise TimeoutError('GPU900_second_cap')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(cfg['bounds']['wall_seconds'])
    try:
        save(out / 'summary.json', state)
        (out / 'proposal_snapshot.json').write_bytes(raw)
        require(cfg['execution_enabled'] is True and cfg['scope'] == 'Qwen_SQuAD_reserved48_descriptive_v1', 'GPU_scope')
        require(os.environ.get('KV_SQUAD48_WATCHDOG') == 'registered_960_seconds', 'outer_watchdog_required')
        for rel, pin in {**cfg['inputs'], **cfg['source_sha256']}.items():
            data = (root / rel).read_bytes()
            require(sha(data) == pin, 'pin:' + rel)
            if rel.startswith('scripts/') or rel == cfg['protocol']:
                (out / ('source_' + Path(rel).name)).write_bytes(data)
        save(out / 'input_manifest.json', cfg['inputs'])
        descriptor = json.loads((root / cfg['descriptor']).read_text())
        for rel, pin in descriptor['source_files'].items():
            data = (root / rel).read_bytes()
            require(sha(data) == pin, 'generator_source:' + rel)
            (out / ('source_' + Path(rel).name)).write_bytes(data)
        runtime_material = dict(version='squad48_registered_study_v1', proposal_sha256=sha(raw),
                                descriptor_sha256=cfg['inputs'][cfg['descriptor']], source_sha256=cfg['source_sha256'])
        runtime = hash_json(runtime_material)
        save(out / 'registered_runtime.json', dict(runtime_digest=runtime, material=runtime_material, old_engineering_imported=False))
        descriptor['registered_runtime_digest'] = runtime
        descriptor['source_files'].update(cfg['source_sha256'])
        descriptor.update(execution_enabled=True, separate_GPU_execution_registered=True)
        save(out / 'backend_execution_snapshot.json', descriptor)
        prepared = [json.loads(s) for s in (root / cfg['selected48']).read_text().splitlines()]
        source = {c['case_id']: c for c in prepared}
        cases = json.loads((root / cfg['native48']).read_text())
        plans = [json.loads(s) for s in (root / cfg['planned144']).read_text().splitlines()]
        require([c['case_id'] for c in prepared] == [c['case_id'] for c in cases] == cfg['case_ids'] and len(cases) == 48, 'original48_registry')
        for case in cases:
            original = source[case['case_id']]
            require(case['split_role'] == ROLE and all(case[k] == original[k] for k in ('prompt_sha256', 'gold_sha256', 'context_group_id')), 'source_identity')
        old_source = {c['case_id']: c for c in map(json.loads, (root / cfg['source64']).read_text().splitlines())}
        eng = [dict(c, context_group_id=old_source[c['case_id']]['context_group_id']) for c in json.loads((root / cfg['engineering_native']).read_text()) if c['split_role'] == 'engineering']
        require([c['case_id'] for c in eng] == cfg['engineering_case_ids'] and len(eng) == 2, 'original_engineering_pair')
        sources_all = dict(source, **{c['case_id']: old_source[c['case_id']] for c in eng})
        specs = [s for s in json.loads((root / cfg['condition_specs']).read_text())['specs'] if s['condition_id'] in NAMES]
        require([s['condition_id'] for s in specs] == list(NAMES), 'three_original_conditions')
        # Correctness checks finish before backend construction or heavy imports.
        require(not any(m.split('.')[0] in ('torch', 'transformers', 'tokenizers') for m in sys.modules), 'CPU_checks_before_model_imports')
        software = run_acceptance(specs)
        save(out / 'integration_software_acceptance.json', software)
        require(len(software) == 16 and all(t['passed'] and t['real_model_calls'] == 0 for t in software), 'software_acceptance')
        hashes = {}
        prefill_checks = []
        map_checks = []
        active = None

        class AuditedBackend(QwenHFBackend):
            def tensor_hash(self, cache):
                h = hashlib.sha256()
                for layer in cache.layers:
                    for t in (layer.keys, layer.values):
                        h.update(t.contiguous().view(self.torch.uint8).cpu().numpy().tobytes())
                return h.hexdigest()

            def _load(self):
                first = self.model is None
                if first:
                    save(out / 'loading_attempt.json', dict(gpu_uuid=self.config['gpu_uuid'], scope=ROLE))
                super()._load()
                if not first:
                    return
                mc = self.model.config
                require(mc.model_type == 'qwen2' and mc.num_hidden_layers == 28 and mc.num_key_value_heads == 4 and mc.num_attention_heads == 28 and mc.hidden_size // mc.num_attention_heads == 128, 'actual_layout')
                require(mc._attn_implementation == 'sdpa' and str(self.model.device) == 'cuda:0', 'actual_backend_device')
                from transformers import AutoTokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(self.config['model_path'], local_files_only=True, trust_remote_code=False, use_fast=True)
                for c in eng + cases:
                    prompt = sources_all[c['case_id']]['prompt']
                    ids = self.tokenizer.apply_chat_template([dict(role='system', content=prompt['system']), dict(role='user', content=prompt['user'])], tokenize=True, add_generation_prompt=True)
                    require(ids == c['input_ids'], 'native_input_retokenization')
                save(out / 'actual_runtime.json', dict(observed=self.actual_runtime, model_config=mc.to_dict(),
                     generation_config=self.model.generation_config.to_dict(), python=sys.version,
                     parameter_dtypes=sorted({str(p.dtype) for p in self.model.parameters()}), retokenized_inputs=50,
                     tf32_matmul=self.torch.backends.cuda.matmul.allow_tf32, tf32_cudnn=self.torch.backends.cudnn.allow_tf32,
                     weights_verified=4, weight_bytes=sum((Path(self.config['model_path']) / n).stat().st_size for n in self.config['weights'])))
                original_prefill, original_maps = self.prefill, self.build_maps
                def observed_prefill(model, ids):
                    ref, scores = original_prefill(model, ids)
                    from trec_context_gate import prefill
                    plain = prefill(model, ids)
                    equal = all(self.torch.equal(a.keys, b.keys) and self.torch.equal(a.values, b.values) for a, b in zip(plain.layers, ref.layers)) and len(plain.layers) == len(ref.layers) == 28
                    require(equal, 'score_hook_changed_cache')
                    del plain
                    cid = active['case_id']
                    fingerprint = self.tensor_hash(ref)
                    require(cid not in hashes or hashes[cid] == fingerprint, 'replayed_prefix_tensor_changed')
                    hashes[cid] = fingerprint
                    data = gzip.compress(json.dumps({str(k): v.tolist() for k, v in scores.items()}, separators=(',', ':'), allow_nan=False).encode(), mtime=0)
                    path = out / (cid + '.scores.json.gz')
                    require(not path.exists() or path.read_bytes() == data, 'replayed_prefix_scores_changed')
                    if not path.exists():
                        path.write_bytes(data)
                    prefill_checks.append(dict(case_id=cid, phase=active['phase'], prefix_ids_sha256=hash_json(ids), prefix_tokens=len(ids), reference_sha256=fingerprint, unhooked_reference_equal=True, score_sha256=sha(data)))
                    save(out / 'prefill_checks.json', prefill_checks)
                    return ref, scores
                def observed_maps(scores, group, n, metadata, conditions):
                    maps = original_maps(scores, group, n, metadata, conditions)
                    for name, layers in maps.items():
                        data = gzip.compress(json.dumps({str(k): v.tolist() for k, v in layers.items()}, separators=(',', ':')).encode(), mtime=0)
                        path = out / (active['case_id'] + '.' + name + '.maps.json.gz')
                        require(not path.exists() or path.read_bytes() == data, 'map_changed_between_paths')
                        if not path.exists():
                            path.write_bytes(data)
                        map_checks.append(dict(case_id=active['case_id'], condition_id=name, path=active['path'], map_sha256=sha(data)))
                    save(out / 'map_checks.json', map_checks)
                    return maps
                self.prefill, self.build_maps = observed_prefill, observed_maps

            def execute(self, request, case, spec, budget):
                nonlocal active
                active = request
                require(request['phase'] in ('engineering', ROLE) and not spec['protect_system'], 'generation_role_or_protection')
                save(out / 'active_request.json', request)
                append(out / 'model_attempts.jsonl', request)
                try:
                    result = super().execute(request, case, spec, budget)
                except BaseException as exc:
                    state['failed_model_attempts'] += 1
                    append(out / 'failed_attempts.jsonl', dict(request=request, error=repr(exc)))
                    raise
                main = request['phase'] == ROLE
                append(out / ('raw_main.jsonl' if main else 'raw_engineering.jsonl'), dict(request=request, result=result))
                state['main_outputs' if main else 'engineering_outputs'] += 1
                state['generated_tokens'] += len(result['ids'])
                save(out / 'summary.json', state)
                require(state['main_outputs'] <= 138 and state['engineering_outputs'] <= 14 and state['generated_tokens'] <= 19456, 'generation_caps')
                require(result['ids'] and result['truncated'] == (result['ids'][-1] not in descriptor['decode']['eos_token_id']), 'termination')
                if request['path'] != 'native_whole':
                    physical = budget['effective_slots']
                    for step, row in enumerate(result['trace'] or []):
                        width = len(case['input_ids']) - case['prefix_tokens'] if step == 0 else 1
                        logical = case['prefix_tokens'] if step == 0 else len(case['input_ids']) + step - 1
                        require(row == dict(step=step, physical_start=physical, logical_start=logical, input_width=width), 'position_trace')
                        physical += width
                    if result['trace'] is not None:
                        require(len(result['trace']) == len(result['ids']), 'trace_length')
                    expected = (budget['effective_slots'] + len(case['input_ids']) - case['prefix_tokens'] + len(result['ids']) - 1) * 57344
                    require(result['actual_prefix_kv_bytes'] == budget['effective_slots'] * 57344 and result['final_live_kv_bytes'] == expected, 'actual_bytes')
                    require(self.tensor_hash(self.reference) == hashes[case['case_id']], 'reference_content_mutation')
                return result

        backend = AuditedBackend(descriptor)
        policy = dict(mode='registered_gpu', execution_enabled=True, bootstrap_generation_enabled=True, DEV_generation_enabled=False,
                      runtime_digest=runtime, max_engineering_calls=14, max_DEV_calls=0, max_input_tokens=2048, wall_seconds=cfg['bounds']['wall_seconds'])
        engine = HFOrchestrator(eng, specs, runtime, policy, lambda: backend)
        study = StudyDispatcher(cases, plans, specs, runtime, engine, backend, cfg['case_ids'], cfg['scope'])
        save(out / 'execution_snapshot.json', dict(proposal_sha256=sha(raw), source_sha256=cfg['source_sha256'], runtime_digest=runtime,
             input48_bindings=study.bindings, engineering_policy=policy, reserved_role=ROLE, argv=sys.argv,
             old_evidence_imported=False, old_dispatcher_modified=False, token_limit=128, main_cap=138, engineering_cap=14))

        def engineering_phase(names):
            for case in eng:
                for name in names:
                    for path in engine.specs[name]['required_paths']:
                        request = engine.request(case['case_id'], name, 'engineering', path)
                        response = engine.dispatch(request)
                        require(response['state'] == 'executed', 'engineering_blocked')
                        append(out / 'accepted_engineering.jsonl', response)
                        save(out / 'engineering_evidence.json', [engine.evidence(n) for n in NAMES])
            require(all(engine.evidence(n)['status'] == 'verified' for n in names), 'engineering_not_verified')

        def main_cell(case, name):
            response = study.dispatch(case['case_id'], name)
            require(response['state'] == 'executed', 'unexpected_main_block')
            result = response['result']; ids = result['ids']
            text = backend.tokenizer.decode(ids[:-1] if ids[-1] in descriptor['decode']['eos_token_id'] else ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
            row, scores = study.accept(case['case_id'], name, result, text, source[case['case_id']]['answers'])
            append(out / 'scored_main.jsonl', dict(case_id=case['case_id'], condition_id=name, text=text, ids=ids, truncated=result['truncated'], scores=scores, normalized=row))

        state['stage'] = 'Full_engineering'; save(out / 'summary.json', state)
        engineering_phase(['full'])
        state['stage'] = 'Full48'; save(out / 'summary.json', state)
        for case in cases:
            main_cell(case, 'full')
        support = study.finalize_full(cfg['Full_support'])
        save(out / 'Full_support.json', support)
        state['Full_support'] = support['passed']
        if support['passed']:
            state['stage'] = 'compressed_engineering'; save(out / 'summary.json', state)
            engineering_phase(list(NAMES[1:]))
            state['stage'] = 'compressed48'; save(out / 'summary.json', state)
            for case in cases:
                for name in NAMES[1:]:
                    if study.plans[case['case_id'], name]['budget']['state'] == 'ok':
                        main_cell(case, name)
            require(state['main_outputs'] == 138 and state['engineering_outputs'] == 14, 'complete_output_coverage')
        else:
            require(state['main_outputs'] == 48 and state['engineering_outputs'] == 6, 'Full_stop_coverage')
        state.update(status='complete', stage='complete' if support['passed'] else 'stopped_Full_support',
                     compressed_phase_executed=support['passed'], independent48_model_outputs=state['main_outputs'])
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
        (out / 'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0)
        if study is not None:
            try:
                stopped = state['status'] != 'complete' or study.full_support is not True
                plan, rows, report = study.statistics(stopped=stopped)
                save(out / 'statistics_plan.json', plan)
                (out / 'normalized_outcomes.jsonl').write_text(''.join(json.dumps(row, allow_nan=False) + '\n' for row in rows))
                save(out / 'group_statistics.json', report)
                core_plan, normalized, core_report = scalar_report(study, rows)
                save(out / 'scalar_plan.json', core_plan)
                save(out / 'scalar_records.json', normalized)
                save(out / 'scalar_report.json', core_report)
            except BaseException as exc:
                state.update(status='failed', analysis_error=repr(exc))
                (out / 'analysis_failure.txt').write_text(traceback.format_exc())
        if engine is not None:
            save(out / 'engineering_evidence.json', [engine.evidence(n) for n in NAMES])
        if backend is not None:
            backend.model = backend.reference = backend.scores = None
            if hasattr(backend, 'torch'):
                gc.collect(); backend.torch.cuda.empty_cache()
        state['elapsed_seconds'] = time.monotonic() - start
        save(out / 'summary.json', state)
        files = [p for p in out.iterdir() if p.is_file()]
        if len(files) + 1 > cfg['bounds']['max_archive_files'] or sum(p.stat().st_size for p in files) > cfg['bounds']['max_archive_bytes']:
            state.update(status='failed', archive_bounds_exceeded=True); save(out / 'summary.json', state)
        save(out / 'manifest.json', {p.name: sha(p.read_bytes()) for p in files})
        print(json.dumps(state), flush=True)
    return 0 if state['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
