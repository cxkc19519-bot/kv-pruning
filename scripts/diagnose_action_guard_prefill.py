"""Teacher-force the existing failing engineering trace; never generate new answers."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import torch
from transformers import AutoModelForCausalLM, DynamicCache


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    args = parser.parse_args()
    root = Path(args.run)
    assert not (root/'prefill_diagnostic.json').exists()
    proposal = json.loads((root/'proposal.json').read_text())
    engineering = [json.loads(line) for line in (root/'engineering.jsonl').read_text().splitlines()]
    assert len(engineering) == 3
    by = {r['mode']: r['generated_ids'] for r in engineering}
    assert by['native_cached'] == by['custom_cached']
    whole, cached = by['native_whole'], by['native_cached']
    divergence = next(i for i, (a, b) in enumerate(zip(whole, cached)) if a != b)
    assert divergence < 64, 'This diagnostic is bounded to the first known divergence.'
    case = json.loads((root/'cases.jsonl').read_text().splitlines()[0])
    condition = engineering[0]['condition']
    assert all(r['key'] == case['key'] and r['condition'] == condition for r in engineering)
    ids = case['encoded'][condition]['input_ids']
    boundary = case['encoded'][condition]['prefix_length']
    source = Path(__file__).read_bytes()
    (root/'source_diagnose_action_guard_prefill.py').write_bytes(source)
    started = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        proposal['model_dir'], local_files_only=True, trust_remote_code=False,
        torch_dtype=torch.bfloat16, attn_implementation='sdpa').to('cuda:0').eval()
    def forward(tokens, cache, backbone=False, mask=True):
        length = cache.get_seq_length()
        x = torch.tensor([tokens], device=model.device)
        pos = torch.arange(length, length+len(tokens), device=model.device)
        kwargs = dict(input_ids=x, past_key_values=cache, use_cache=True,
                      position_ids=pos[None, :], cache_position=pos)
        if mask:
            kwargs['attention_mask'] = torch.ones((1, length+len(tokens)), device=model.device, dtype=torch.long)
        if backbone:
            return model.model(**kwargs)
        return model(**kwargs, logits_to_keep=1).logits[0, -1]
    with torch.inference_mode():
        full_cache, split_cache = DynamicCache(), DynamicCache()
        full_logits = forward(ids, full_cache)
        forward(ids[:boundary], split_cache, backbone=True, mask=False)
        prefix_errors = []
        for layer, (full, split) in enumerate(zip(full_cache.layers, split_cache.layers)):
            for name in ['keys', 'values']:
                a, b = getattr(full, name)[:, :, :boundary, :], getattr(split, name)
                assert a.shape == b.shape
                prefix_errors.append(dict(layer=layer, tensor=name, elements=a.numel(),
                                          unequal=int((a != b).sum()),
                                          max_abs=float((a.float()-b.float()).abs().max())))
        split_logits = forward(ids[boundary:], split_cache)
        traces = []
        for step in range(divergence+1):
            assert full_cache.get_seq_length() == split_cache.get_seq_length() == len(ids)+step
            full_top = full_logits.float().topk(5)
            split_top = split_logits.float().topk(5)
            full_token, split_token = int(full_top.indices[0]), int(split_top.indices[0])
            traces.append(dict(step=step, logical_length=len(ids)+step,
                               full_argmax=full_token, cached_argmax=split_token,
                               full_top_ids=full_top.indices.tolist(), full_top_logits=full_top.values.tolist(),
                               cached_top_ids=split_top.indices.tolist(), cached_top_logits=split_top.values.tolist(),
                               logits_max_abs=float((full_logits.float()-split_logits.float()).abs().max()),
                               matches_saved_full=full_token == whole[step],
                               matches_saved_cached=split_token == cached[step]))
            if step < divergence:
                # Replay existing shared tokens, regardless of this diagnostic's argmax.
                token = [whole[step]]
                assert token[0] == cached[step]
                full_logits = forward(token, full_cache)
                split_logits = forward(token, split_cache)
    result = dict(source_sha256=hashlib.sha256(source).hexdigest(), start_unix=started,
                  end_unix=time.time(), key=case['key'], condition=condition, known_divergence=divergence,
                  prefix_tokens=boundary, prompt_tokens=len(ids), prefix_kv=prefix_errors, teacher_forced_trace=traces,
                  all_saved_argmax_reproduced=all(r['matches_saved_full'] and r['matches_saved_cached'] for r in traces),
                  new_model_outputs=0, generated_tokens=0, prior_gate_remains_failed=True,
                  interpretation='A bounded diagnosis of the already observed failure, not a new decoding or attention configuration.')
    (root/'prefill_diagnostic.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ['prefix_kv', 'teacher_forced_trace']}))
    print('PREFIX_UNEQUAL', sum(r['unequal'] for r in prefix_errors), 'FINAL_STEP', json.dumps(traces[-1]))


if __name__ == '__main__':
    main()
