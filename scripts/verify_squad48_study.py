"""Independent scoring, positions, maps and statistics audit of Qwen48 outputs."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1')
import sys
sys.dont_write_bytecode = True
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import signal
import time
from verify_hf_DEV_acceptance import independent_score


def read(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8388608), b''):
            h.update(block)
    return h.hexdigest()


def canon(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def near(a, b):
    assert type(a) in (int, float) and math.isfinite(a) and abs(a - b) < 1e-12, (a, b)


def quantile(values, p):
    values = sorted(values)
    h = Fraction((len(values) - 1) * p, 1000)
    i = h.numerator // h.denominator
    return float(Fraction(values[i]) + (Fraction(values[min(i + 1, len(values) - 1)]) - Fraction(values[i])) * (h - i))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--proposal-sha256', required=True); args = ap.parse_args()
    start = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *unused: (_ for _ in ()).throw(TimeoutError('independent180_second_cap')))
    signal.alarm(180)
    root = Path(__file__).resolve().parent.parent
    assert str(root) == '/home/user/jhk/project/Directional Exploration/kv-pruning'
    proposal = root / 'configs/squad48-gpu-study-v1.json'
    assert sha(proposal) == args.proposal_sha256
    cfg = read(proposal); out = root / cfg['run']
    summary = read(out / 'summary.json'); assert summary['status'] == 'complete'
    for n, pin in read(out / 'manifest.json').items(): assert sha(out / n) == pin, n
    for n, pin in {**cfg['inputs'], **cfg['source_sha256']}.items(): assert sha(root / n) == pin, n
    descriptor = read(out / 'backend_execution_snapshot.json')
    for n, pin in descriptor['source_files'].items(): assert sha(root / n) == pin and sha(out / ('source_' + Path(n).name)) == pin, n
    scope = read(out / 'registered_runtime.json'); runtime = scope['runtime_digest']; assert canon(scope['material']) == runtime
    assert scope['material']['proposal_sha256'] == args.proposal_sha256 and scope['old_engineering_imported'] is False
    actual = read(out / 'actual_runtime.json')
    assert actual['observed']['runtime_Full_layers'] == 28 and actual['observed']['KV_heads'] == 4 and actual['observed']['bytes_per_slot'] == 57344
    assert actual['retokenized_inputs'] == 50 and actual['parameter_dtypes'] == ['torch.bfloat16'] and actual['tf32_matmul'] is actual['tf32_cudnn'] is False
    assert actual['observed']['versions'] == descriptor['versions'] and actual['generation_config'] == actual['observed']['decode']
    assert all(actual['generation_config'][k] == v for k, v in descriptor['decode'].items())
    assert actual['model_config']['layer_types'] == ['full_attention'] * 28 and actual['model_config']['num_key_value_heads'] == 4
    for name, pin in descriptor['model_metadata_files'].items(): assert sha(Path(descriptor['model_path']) / name) == pin
    for name, pin in descriptor['weights'].items(): assert sha(Path(descriptor['model_path']) / name) == pin
    software = read(out / 'integration_software_acceptance.json')
    assert [x['id'] for x in software] == ['S%02d' % i for i in range(1, 17)] and all(x['passed'] and x['real_model_calls'] == 0 for x in software)
    source = {c['case_id']: c for c in lines(root / cfg['source64'])}
    selected = lines(root / cfg['selected48']); assert [c['case_id'] for c in selected] == cfg['case_ids']
    main = read(root / cfg['native48'])
    eng = [c for c in read(root / cfg['engineering_native']) if c['split_role'] == 'engineering']
    cases = {c['case_id']: dict(c, context_group_id=source[c['case_id']]['context_group_id']) for c in eng + main}
    assert set(c['context_group_id'] for c in main).isdisjoint(c['context_group_id'] for c in cases.values() if c['split_role'] == 'engineering')
    specs = {s['condition_id']: s for s in read(root / cfg['condition_specs'])['specs'] if s['condition_id'] in ('full', 'adapted_snapkv', 'uniform_random')}
    raw_eng = lines(out / 'raw_engineering.jsonl'); raw_main = lines(out / 'raw_main.jsonl')
    accepted = lines(out / 'accepted_engineering.jsonl'); scored = lines(out / 'scored_main.jsonl')
    assert len(raw_main) == summary['main_outputs'] == len(scored) and len(raw_eng) == summary['engineering_outputs'] == len(accepted)
    assert len(lines(out / 'model_attempts.jsonl')) == len(raw_eng) + len(raw_main)
    assert len({r['request']['request_digest'] for r in raw_eng + raw_main}) == len(raw_eng) + len(raw_main)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(descriptor['model_path'], local_files_only=True, trust_remote_code=False, use_fast=True)
    trace_steps = 0
    for item in raw_eng + raw_main:
        request, result = item['request'], item['result']; case = cases[request['case_id']]
        body = {k: v for k, v in request.items() if k != 'request_digest'}
        assert canon(body) == request['request_digest'] == result['request_digest'] and request['runtime_digest'] == runtime
        material = {k: case[k] for k in ('case_id', 'split_role', 'input_ids', 'prefix_tokens', 'header_ids', 'prompt_sha256', 'context_group_id')}
        assert request['case_input_digest'] == canon(material)
        spec = specs[request['condition_id']]
        assert request['condition_fingerprint'] == canon(dict(version='condition_admission_v1', runtime_digest=runtime, condition=spec))
        assert result['execution_state'] == 'ok' and 0 < len(result['ids']) <= 128
        assert result['runtime_metadata'] == actual['observed']
        assert result['truncated'] == (result['ids'][-1] not in descriptor['decode']['eos_token_id'])
        if request['path'] == 'native_whole':
            assert request['phase'] == 'engineering' and result['actual_prefix_kv_bytes'] is result['final_live_kv_bytes'] is None
        else:
            n = case['prefix_tokens']; slots = n if request['condition_id'] == 'full' else n // 2
            assert result['actual_prefix_kv_bytes'] == slots * 57344
            expected_final = slots + len(case['input_ids']) - n + len(result['ids']) - 1
            assert result['final_live_kv_bytes'] == expected_final * 57344
            if result['trace'] is not None:
                assert len(result['trace']) == len(result['ids']); physical = slots
                for i, row in enumerate(result['trace']):
                    width = len(case['input_ids']) - n if i == 0 else 1
                    logical = n if i == 0 else len(case['input_ids']) + i - 1
                    assert row == dict(step=i, physical_start=physical, logical_start=logical, input_width=width)
                    physical += width; trace_steps += 1
                assert physical == expected_final
    for raw, ack in zip(raw_eng, accepted): assert ack['result'] == raw['result'] and ack['decision']['request'] == raw['request']
    for cid in cfg['engineering_case_ids']:
        for name in specs:
            values = [r for r in raw_eng if r['request']['case_id'] == cid and r['request']['condition_id'] == name]
            if not values: continue
            assert {r['request']['path'] for r in values} == set(specs[name]['required_paths'])
            assert all(r['result']['ids'] == values[0]['result']['ids'] and r['result']['truncated'] == values[0]['result']['truncated'] for r in values)
            if name != 'full': assert values[0]['result']['trace'] == values[1]['result']['trace']
    outcomes = lines(out / 'normalized_outcomes.jsonl'); by = {(r['case_id'], r['condition_id']): r for r in outcomes}
    assert len(by) == len(outcomes) == 144
    main_by = {(r['request']['case_id'], r['request']['condition_id']): r for r in raw_main}
    assert len(main_by) == len(raw_main)
    for row in scored:
        key = row['case_id'], row['condition_id']; result = main_by[key]['result']; ids = result['ids']
        text = tokenizer.decode(ids[:-1] if ids[-1] in descriptor['decode']['eos_token_id'] else ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        assert text == row['text'] and ids == row['ids']
        scores = independent_score(text, [a['text'] for a in source[key[0]]['answers']]); assert scores == row['scores']
        normalized = by[key]; assert normalized == row['normalized']
        assert normalized['task_EM'] == (None if scores['em'] is None else int(scores['em'])) and normalized['task_F1'] == scores['f1']
        assert normalized['format'] is scores['format'] and normalized['truncated'] is result['truncated']
    for case in main:
        for name in specs:
            row = by[case['case_id'], name]; n = case['prefix_tokens']; budget = 'ok' if name == 'full' or n // 2 >= 68 else 'infeasible_budget'
            assert row['budget_state'] == budget and row['role'] == 'sealed_descriptive_evaluation'
            material = {k: case[k] for k in ('case_id', 'split_role', 'input_ids', 'prefix_tokens', 'header_ids', 'prompt_sha256', 'context_group_id')}
            assert row['input_digest'] == canon(case['input_ids']) and row['gold_digest'] == source[case['case_id']]['gold_sha256']
            assert row['comparison_digest'] == canon(dict(runtime=runtime, cohort=cfg['scope'], case_binding=canon(material)))
            if budget != 'ok': assert row['execution_state'] == 'infeasible_budget' and all(row[k] is None for k in ('task_EM', 'task_F1', 'format', 'truncated'))
    full = [by[c['case_id'], 'full'] for c in main]; good = [r for r in full if not r['truncated']]
    counts = dict(scheduled=48, generated=48, errors=0, task=sum(r['task_EM'] == 1 for r in good), format=sum(r['format'] for r in good),
                  joint=sum(r['format'] and r['task_EM'] == 1 for r in good), truncated=sum(r['truncated'] for r in full), candidates=sum(r['task_EM'] is not None for r in good))
    gate = cfg['Full_support']; passed = counts['task'] >= gate['task_min'] and counts['format'] >= gate['format_min'] and counts['truncated'] <= gate['truncated_max'] and counts['errors'] <= gate['errors_max']
    support = read(out / 'Full_support.json'); assert support['counts'] == counts and support['passed'] is passed and summary['Full_support'] is passed
    assert len(raw_main) == (138 if passed else 48) and len(raw_eng) == (14 if passed else 6)
    stats = read(out / 'group_statistics.json'); assert stats['groups'] == 48 and stats['planned_cells'] == 144
    if not passed:
        assert not any(r['request']['condition_id'] != 'full' for r in raw_main)
        assert stats['comparisons'] is stats['bootstrap'] is None and stats['status'] == 'descriptive_only'
        assert sum(r['execution_state'] == 'protocol_stopped' for r in outcomes) == 90
    group_order = sorted(main, key=lambda c: c['context_group_id'])
    joint = {name: [int(r['execution_state'] == 'ok' and not r['truncated'] and r['format'] and r['task_EM'] == 1)
                    for r in [by[c['case_id'], name] for c in group_order]] for name in specs}
    if passed:
        assert stats['status'] == 'complete'
        vectors = {name: [b - a for a, b in zip(joint['full'], joint[name])] for name in specs if name != 'full'}
        rng = random.Random(20261030); draws_hash = hashlib.sha256(); distributions = {name: [] for name in vectors}
        for unused in range(10000):
            indices = [rng.randrange(48) for i in range(48)]; draws_hash.update((json.dumps(indices, separators=(',', ':')) + '\n').encode())
            for name, values in vectors.items(): distributions[name].append(sum(values[i] for i in indices) / 48)
        assert stats['bootstrap']['draw_sha256'] == draws_hash.hexdigest() and stats['bootstrap']['group_order'] == [c['context_group_id'] for c in group_order]
        for name, values in vectors.items():
            rec = stats['comparisons'][name]; near(rec['joint_delta'], sum(values) / 48)
            for a, b in zip(rec['joint_delta_ci95'], (quantile(distributions[name], 25), quantile(distributions[name], 975))): near(a, b)
    scalar = read(out / 'scalar_report.json'); records = read(out / 'scalar_records.json')
    assert len(records) == 144 and scalar['case_count'] == scalar['group_count'] == 48
    strict_pairs = {}
    for name in specs:
        selected_rows = [by[c['case_id'], name] for c in main]
        report = scalar['conditions'][name]
        assert report['execution']['scheduled'] == 48
        for state in ('ok', 'error', 'not_run', 'infeasible_budget'):
            expected = sum(('not_run' if r['execution_state'] == 'protocol_stopped' else r['execution_state']) == state for r in selected_rows)
            assert report['execution'][state] == expected
        for metric_name, source_key in [('task', 'task_EM'), ('f1', 'task_F1'), ('constraint', 'format')]:
            available = [r[source_key] for r in selected_rows if r['execution_state'] == 'ok' and not r['truncated'] and r[source_key] is not None]
            metric = report['metrics'][metric_name]; assert metric['evaluated_count'] == len(available)
            if available: near(metric['mean'], sum(available) / len(available))
            else: assert metric['mean'] is None
            if name != 'full':
                paired = [(a[source_key], b[source_key]) for a, b in zip(full, selected_rows) if a['execution_state'] == b['execution_state'] == 'ok' and not a['truncated'] and not b['truncated'] and a[source_key] is not None and b[source_key] is not None]
                assert metric['paired_count'] == len(paired)
                if paired: near(metric['mean_paired_delta'], sum(b - a for a, b in paired) / len(paired))
                else: assert metric['mean_paired_delta'] is None
                if metric_name != 'f1':
                    transitions = {t: sum((('C' if a else 'W') + '2' + ('C' if b else 'W')) == t for a, b in paired) for t in ('C2C', 'C2W', 'W2C', 'W2W')}
                    assert metric['transitions'] == transitions
                strict_pairs[name + ':' + metric_name] = len(paired)
        actual_prefix = [r['actual_prefix_kv_bytes'] for r in selected_rows if r['execution_state'] == 'ok']
        prefix = report['costs']['prefix_kv_bytes']; assert prefix['observed_count'] == len(actual_prefix)
        if actual_prefix: assert prefix['minimum'] == min(actual_prefix) and prefix['maximum'] == max(actual_prefix)
    # Independently replay every archived selector from prefix-only scores.
    map_files = sorted(out.glob('*.maps.json.gz'))
    checked_heads = 0
    if map_files:
        import torch  # CPU generator only; CUDA visibility is empty in this process.
        assert not torch.cuda.is_initialized()
        for path in map_files:
            cid, name = path.name.split('.')[:2]; case = cases[cid]; n = case['prefix_tokens']; budget = n // 2
            maps = json.loads(gzip.decompress(path.read_bytes())); scores = json.loads(gzip.decompress((out / (cid + '.scores.json.gz')).read_bytes()))
            assert set(maps) == set(scores) == {str(i) for i in range(28)}
            mandatory = set(range(4)) | set(range(n - 64, n)); free = sorted(set(range(n)) - mandatory)
            for layer in range(28):
                assert len(maps[str(layer)]) == 1 and len(maps[str(layer)][0]) == 4
                for head, indices in enumerate(maps[str(layer)][0]):
                    assert all(type(i) is int for i in indices) and indices == sorted(set(indices)) and len(indices) == budget and mandatory <= set(indices)
                    if name == 'uniform_random':
                        material = json.dumps([20261028, case['context_group_id'], layer, head], separators=(',', ':')).encode()
                        seed = int.from_bytes(hashlib.sha256(material).digest()[:8], 'big') % (2**63)
                        values = torch.rand(n, generator=torch.Generator(device='cpu').manual_seed(seed), dtype=torch.float64).tolist()
                    else: values = scores[str(layer)][0][head]
                    expected = sorted(mandatory | set(sorted(free, key=lambda i: (-values[i], i))[:budget - len(mandatory)]))
                    assert indices == expected; checked_heads += 1
        assert not torch.cuda.is_initialized()
    assert len(map_files) == (94 if passed else 0)
    assert len(read(out / 'prefill_checks.json')) == (97 if passed else 50)
    assert all(x['unhooked_reference_equal'] for x in read(out / 'prefill_checks.json'))
    evidence = read(out / 'engineering_evidence.json')
    assert all(e['status'] == ('verified' if passed or e['condition_id'] == 'full' else 'insufficient_coverage') for e in evidence)
    assert not any(m in sys.modules for m in ('reliability_squad48_study', 'run_squad48_study', 'reliability_group_statistics', 'answer_format_task'))
    result = dict(passed=True, method='Independent text scoring/decoded IDs, budget/position geometry, prefix-only selectors and paired all48 bootstrap; no study/core/statistics/scorer imports',
                  software_cases=16, source_inputs=len(cfg['inputs']), weights_rehashed=4, metadata_rehashed=6,
                  groups=48, planned_cells=144, main_outputs=len(raw_main), engineering_outputs=len(raw_eng),
                  Full_support=passed, Full_counts=counts, trace_steps=trace_steps, map_files=len(map_files), layer_head_maps_checked=checked_heads,
                  strict_pairs=strict_pairs, joint_successes={name: sum(v) for name, v in joint.items()},
                  effects_independently_verified=passed, model_inference=False, independent_tokenizer_input_encodes=0,
                  original_manifest_sha256=sha(out / 'manifest.json'), pid=os.getpid(), elapsed_seconds=time.monotonic() - start)
    signal.alarm(0)
    assert not (out / 'independent_verification.json').exists()
    (out / 'independent_verification.json').write_text(json.dumps(result, ensure_ascii=True, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
