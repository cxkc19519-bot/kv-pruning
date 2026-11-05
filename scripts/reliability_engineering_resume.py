"""Resume pinned, same-generator engineering observations without inference."""
import copy
import hashlib
import json
from reliability_system_core import require
from reliability_system_adapters import hash_json
from reliability_execution_contract import engineering_evidence


def validate_observations(engine, raw, accepted, bindings, evidence):
    require(engine.backend is None and not engine.executed and all(not x for x in engine.obs.values()), 'resume_requires_fresh_engine')
    require(engine.phase_calls == dict(engineering=0, development=0), 'resume_after_execution')
    require(len(raw) == len(accepted) == 14, 'resume_path_count')
    require({x['case_id']:x['case_input_digest'] for x in bindings} == engine.bindings and len(bindings) == len(engine.cases), 'resume_input_bindings')
    observations = {k:[] for k in engine.specs}; seen = set()
    for archived, saved in zip(raw, accepted):
        req = archived['request']; result = archived['result']
        require(req['phase'] == 'engineering' and engine.cases[req['case_id']]['split_role'] == 'engineering', 'resume_non_engineering')
        engine._validate_request(req)
        require(saved['state'] == 'executed' and saved['model_called'] is True and saved['result'] == result and saved['decision']['request'] == req, 'resume_acceptance_mismatch')
        require(engine.decision(req) == saved['decision'], 'resume_budget_or_scope_changed')
        require(req['request_digest'] not in seen, 'resume_duplicate_path'); seen.add(req['request_digest'])
        require(result['request_digest'] == req['request_digest'] and result['execution_state'] == 'ok', 'resume_output_binding')
        require(isinstance(result['ids'], list) and 0 < len(result['ids']) <= 128 and all(type(x) is int and x >= 0 for x in result['ids']), 'resume_tokens')
        require(type(result['truncated']) is bool, 'resume_termination')
        observations[req['condition_id']].append(dict(case_id=req['case_id'], path=req['path'], condition_fingerprint=req['condition_fingerprint'], case_input_digest=req['case_input_digest'], execution_state='ok', ids=result['ids'], trace=result.get('trace'), truncated=result['truncated']))
    rebuilt = []
    for name, spec in engine.specs.items():
        plans = [engine._plan(c, name) for c in engine.cases.values() if c['split_role'] == 'engineering']
        ev = engineering_evidence(spec, engine.runtime, plans, observations[name]); rebuilt.append(ev)
    require(rebuilt == evidence, 'resume_evidence_recompute_mismatch')
    require(sum(x['status'] == 'verified' for x in rebuilt) == 3 and sum(x['status'] == 'unverified_budget_infeasible' for x in rebuilt) == 2, 'resume_condition_coverage')
    return observations


def restore_checkpoint(engine, root, cfg):
    checkpoint = root/cfg['engineering_checkpoint']
    read = lambda name:json.loads((checkpoint/name).read_text())
    for path, expected in cfg['inputs'].items():
        require(hashlib.sha256((root/path).read_bytes()).hexdigest() == expected, 'resume_input_pin:'+path)
    for manifest in ('manifest.json', 'derived_manifest.json'):
        for name, expected in read(manifest).items():
            require(hashlib.sha256((checkpoint/name).read_bytes()).hexdigest() == expected, 'resume_manifest:'+name)
    require(read('summary.json')['status'] == 'complete' and read('independent_verification.json')['status'] == 'passed', 'resume_checkpoint_not_verified')
    scope = read('registered_runtime_scope.json'); require(hash_json(scope['material']) == scope['runtime_digest'] == engine.runtime, 'resume_generator_scope')
    descriptor = read('backend_execution_snapshot.json')
    for path, expected in descriptor['source_files'].items():
        require(hashlib.sha256((root/path).read_bytes()).hexdigest() == expected, 'resume_generator_source_changed:'+path)
    raw = [json.loads(x) for x in (checkpoint/'raw_engineering.jsonl').read_text().splitlines()]
    accepted = [json.loads(x) for x in (checkpoint/'accepted_engineering.jsonl').read_text().splitlines()]
    observations = validate_observations(engine, raw, accepted, read('prepared_bindings.json'), read('engineering_evidence.json'))
    engine.obs = copy.deepcopy(observations)
    # These requests remain consumed but are not counted as new model calls.
    engine.executed.update(x['request']['request_digest'] for x in raw)
    return dict(restored_engineering_observations=len(raw), new_engineering_calls=0, generator_runtime_digest=engine.runtime, evidence_recomputed=True, pinned_checkpoint=str(checkpoint.relative_to(root)), numerical_generator_sources_unchanged=True)
