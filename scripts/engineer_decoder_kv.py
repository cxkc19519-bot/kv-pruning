"""Registered two-engineering-group GPU check, never the12 development groups."""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.metadata
import json
import random
from pathlib import Path


def save(out, name, value):
    (out / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    out = Path(sys.argv[1])
    cfg = json.loads((out / 'registration_snapshot.json').read_text())
    directory = Path(cfg['model_path'])
    weight_observations = {}
    for name, expected in cfg['weights'].items():
        h = hashlib.sha256()
        with (directory / name).open('rb') as f:
            for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
                h.update(b)
        assert h.hexdigest() == expected
        weight_observations[name] = dict(sha256=expected, bytes=(directory / name).stat().st_size)
    for name, v in cfg['versions'].items():
        assert importlib.metadata.version(name) == v
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from decoder_kv_backend import SamePrefixBackend, compare_vectors
    torch.set_num_threads(4)
    torch.manual_seed(cfg['torch_seed'])
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    model = AutoModelForCausalLM.from_pretrained(str(directory), torch_dtype=torch.bfloat16, attn_implementation='sdpa',
                                               local_files_only=True, trust_remote_code=False).eval().to('cuda:0')
    assert model.config.model_type == 'qwen2' and len(model.model.layers) == 28
    assert set(model.config.layer_types) == {'full_attention'} and model.config.use_sliding_window is False
    assert model.config._attn_implementation == 'sdpa' and all(p.dtype == torch.bfloat16 for p in model.parameters())
    assert all(getattr(x.self_attn, 'sliding_window', None) is None for x in model.model.layers)
    tokenizer = AutoTokenizer.from_pretrained(str(directory), local_files_only=True, trust_remote_code=False, use_fast=True)
    rows = json.loads((Path(cfg['root']) / cfg['native_inputs']).read_text())
    source = {c['case_id']: c for c in json.loads((Path(cfg['root']) / cfg['selected_cases']).read_text())}
    rows = [c for c in rows if c['role'] == 'engineering']
    assert [c['case_id'] for c in rows] == cfg['engineering_case_ids'] and len(rows) == 2
    allowed = json.loads((Path(cfg['root']) / cfg['grammar_contract']).read_text())['branch_allowed']
    assert allowed == [32, 33, 34, 35]
    for row in rows:
        c = source[row['case_id']]
        messages = [dict(role='system', content=c['system']), dict(role='user', content=c['user'])]
        rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        assert rendered == row['rendered']
        assert tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True) == row['full_input_ids']
        assert tokenizer(rendered + '{"answer":"', add_special_tokens=False)['input_ids'] == row['branch_input_ids']
    save(out, 'actual_runtime.json', dict(model_config=model.config.to_dict(), versions=cfg['versions'],
         parameter_dtypes=sorted({str(p.dtype) for p in model.parameters()}), attention='sdpa', device=str(model.device),
         Full_layers=28, KV_heads=4, head_dimension=128, bytes_per_slot=57344, tokenizer_encodes=4,
         weights=weight_observations, tf32=False, GPU_uuid=cfg['gpu_uuid']))
    save(out, 'engineering_inputs.json', rows)
    backend = SamePrefixBackend(model, out, cfg['compute_bounds'])
    comparisons, integrity, plans = [], [], []
    with torch.inference_mode():
        for row in rows:
            backend.case_id = row['case_id']
            prefix, suffix = row['prefix_ids'], row['suffix_ids']
            n, b = len(prefix), row['budget_slots']
            assert n == 373 and b == 186 and len(suffix) == 24
            backend.path = 'whole'
            whole_cache, whole = backend.forward(prefix + suffix, 0)
            backend.record_vector('whole', whole)
            del whole_cache
            backend.path = 'prefix'
            ref, unused = backend.forward(prefix, 0)
            backend.validate(ref, n)
            original = backend.fingerprint(ref)
            backend.snapshot(ref, 'reference', list(range(n)))
            backend.path = 'full_batch'
            full = backend.suffix(ref, suffix, n)
            backend.record_vector('full_batch', full)
            backend.path = 'split_prefix'
            split, unused = backend.forward(prefix[:128], 0)
            split, unused = backend.forward(prefix[128:], 128, split)
            backend.path = 'split_full_batch'
            split_logits = backend.suffix(split, suffix, n)
            backend.record_vector('split_full_batch', split_logits)
            del split
            pairs = [('whole_vs_full_batch', whole, full), ('whole_vs_split_full_batch', whole, split_logits)]
            anchors = row['anchors']
            free = [i for i in range(n) if i not in anchors]
            maps = dict(recency=sorted(anchors + sorted(free, reverse=True)[:b - len(anchors)]),
                        uniform_random=sorted(anchors + random.Random(cfg['random_seeds'][0]).sample(free, b - len(anchors))))
            for name, indices in maps.items():
                assert len(indices) == len(set(indices)) == b and set(anchors) <= set(indices)
                compact = backend.copy_cache(ref, indices)
                backend.validate(compact, b)
                backend.snapshot(compact, name, indices)
                before_compact = backend.fingerprint(compact)
                backend.path = name + '_batch'
                batch = backend.suffix(compact, suffix, n)
                backend.record_vector(name + '_batch', batch)
                backend.path = name + '_tokenwise'
                tokenwise = backend.suffix(compact, suffix, n, tokenwise=True)
                backend.record_vector(name + '_tokenwise', tokenwise)
                assert backend.fingerprint(compact) == before_compact
                plans.append(dict(case_id=row['case_id'], name=name, indices=indices, actual_prefix_bytes=backend.cache_bytes(compact)))
                pairs.append((name + '_batch_vs_tokenwise', batch, tokenwise))
                del compact
            assert backend.fingerprint(ref) == original
            integrity.append(dict(case_id=row['case_id'], reference_sha256_before=original, reference_sha256_after=backend.fingerprint(ref),
                                  clone_gather_and_suffix_prefix_values_exact=True))
            for name, p, q in pairs:
                value = compare_vectors(p, q, allowed)
                ok = (value['max_abs'] <= cfg['numeric']['max_abs_logit'] and value['global_KL'] <= cfg['numeric']['global_KL']
                      and value['allowed_KL'] <= cfg['numeric']['allowed_KL'] and value['global_argmax_equal'] and value['allowed_argmax_equal'])
                comparisons.append(dict(case_id=row['case_id'], name=name, passed=ok, metrics=value))
            save(out, 'comparisons.json', comparisons)
            save(out, 'reference_integrity.json', integrity)
            save(out, 'gather_plans.json', plans)
            save(out, 'vectors.json', backend.vectors)
            save(out, 'cache_snapshots.json', backend.cache_records)
            assert all(x['passed'] for x in comparisons), 'frozen_numerical_engineering_gate_failed'
            del ref
        assert backend.calls == 112 and backend.tokens == 2574 and backend.vector_count == 14
    save(out, 'engineering_summary.json', dict(passed=True, engineering_groups=2, archived_logit_vectors=14,
         forward_calls=backend.calls, teacher_forced_input_tokens=backend.tokens, generated_tokens=0, model_answers=0,
         development_model_calls=0, tokenizer_encodes=4, comparisons=len(comparisons), actual_physical_prefix_bytes_verified=True,
         Full_development_support_tested=False, H3_misranking_tested=False))
    print(json.dumps(dict(worker_status='complete', engineering_vectors=14, forward_calls=112)), flush=True)


if __name__ == '__main__':
    main()
