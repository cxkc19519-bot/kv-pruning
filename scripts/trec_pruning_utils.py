"""Selection and physical KV gather for the frozen TREC calibration.

Selectors accept prefix scores/metadata only. They never receive a user query,
gold answer, or any generated result. This is independent project code.
"""
import hashlib
import json

import torch
from transformers import DynamicCache


def mandatory_positions(n, header_ids=(), pin_header=False, sink=4, recent=64):
    if n < 1 or sink < 0 or recent < 0:
        raise ValueError("Invalid prefix/anchor lengths")
    header_ids = list(header_ids)
    if any(not isinstance(i, int) or i < 0 or i >= n for i in header_ids):
        raise ValueError("Header position outside original prefix")
    required = set(range(min(sink, n))) | set(range(max(0, n-recent), n))
    if pin_header:
        required.update(header_ids)
    return sorted(required)


def random_prefix_scores(n, source_key, layer_index, kv_heads, seed=20261028):
    """Independent reproducible IID float64 scores per layer/head/position."""
    if n < 1 or kv_heads < 1 or layer_index < 0:
        raise ValueError("Invalid score dimensions")
    result = torch.empty((1, kv_heads, n), dtype=torch.float64, device="cpu")
    for head in range(kv_heads):
        material = json.dumps([seed, source_key, layer_index, head], separators=(",", ":")).encode()
        local_seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "big") % (2**63)
        generator = torch.Generator(device="cpu").manual_seed(local_seed)
        result[0, head] = torch.rand(n, generator=generator, dtype=torch.float64)
    return result


def select_prefix_indices(scores, budget, header_ids=(), pin_header=False, sink=4, recent=64):
    """Fill the fixed budget after charging anchors/header; break ties by position."""
    if scores.ndim != 3 or scores.shape[0] != 1 or not scores.is_floating_point():
        raise ValueError("Expected floating [1, KV-head, original-position] scores")
    if not torch.isfinite(scores).all():
        raise ValueError("Nonfinite scores")
    n = scores.shape[-1]
    if not isinstance(budget, int) or not 1 <= budget <= n:
        raise ValueError("Invalid budget")
    required = mandatory_positions(n, header_ids, pin_header, sink, recent)
    if len(required) > budget:
        raise ValueError("Complete protected positions exceed fixed budget")
    if budget == n:
        return torch.arange(n, device=scores.device).expand(*scores.shape[:-1], n).clone()
    required_set = set(required)
    free = torch.tensor([i for i in range(n) if i not in required_set], device=scores.device, dtype=torch.long)
    count = budget-len(required)
    # Stable descending sort on ascending original positions makes ties explicit.
    order = scores.index_select(-1, free).argsort(dim=-1, descending=True, stable=True)[..., :count]
    extra = free[order]
    pinned = torch.tensor(required, device=scores.device, dtype=torch.long).expand(*scores.shape[:-1], len(required))
    return torch.cat([pinned, extra], dim=-1).sort(dim=-1).values


def validate_indices(indices, n, budget, kv_heads, header_ids=(), pin_header=False):
    if indices.dtype != torch.long or tuple(indices.shape) != (1, kv_heads, budget):
        raise ValueError("Invalid index shape/dtype")
    if not bool(((indices >= 0) & (indices < n)).all()):
        raise ValueError("Index outside original prefix")
    if budget > 1 and not bool((indices[..., 1:] > indices[..., :-1]).all()):
        raise ValueError("Indices must be unique and strictly sorted")
    required = torch.tensor(mandatory_positions(n, header_ids, pin_header), device=indices.device, dtype=torch.long)
    wanted = required.expand(*indices.shape[:-1], len(required)).contiguous()
    locations = torch.searchsorted(indices.contiguous(), wanted).clamp_max(budget-1)
    if not bool((indices.gather(-1, locations) == wanted).all()):
        raise ValueError("Missing protected position")


def gather_prefix_cache(reference, indices_by_layer, original_n, budget, header_ids=(), pin_header=False):
    """Physically gather K/V values unchanged; original indices define RoPE positions."""
    if set(indices_by_layer) != set(range(len(reference.layers))):
        raise ValueError("Layer map incomplete")
    result = DynamicCache()
    for layer_index, layer in enumerate(reference.layers):
        keys, values = layer.keys, layer.values
        if keys.shape != values.shape or keys.shape[0] != 1 or keys.shape[2] != original_n:
            raise ValueError("Reference shape/length mismatch")
        indices = indices_by_layer[layer_index]
        validate_indices(indices, original_n, budget, keys.shape[1], header_ids, pin_header)
        expanded = indices.to(keys.device).unsqueeze(-1).expand(-1, -1, -1, keys.shape[-1])
        compact_keys = keys.gather(2, expanded).contiguous()
        compact_values = values.gather(2, expanded).contiguous()
        result.update(compact_keys, compact_values, layer_index)
    return result


def kv_bytes(cache):
    return sum(t.numel()*t.element_size() for layer in cache.layers for t in (layer.keys, layer.values))


def native_header_metadata(tokenizer, messages, expected_input_ids, prefix_tokens, shared_header):
    """Map the exact native character span, including every boundary-overlap token."""
    system = messages[0]["content"]
    if [m["role"] for m in messages] != ["system", "user"] or not system.startswith(shared_header):
        raise ValueError("Unexpected frozen message roles/header")
    rendered = tokenizer.apply_chat_template(messages[:1], tokenize=False, add_generation_prompt=False)
    marker = "<|im_start|>system\n"
    if not rendered.startswith(marker) or not rendered.endswith("<|im_end|>\n"):
        raise ValueError("Unexpected Qwen native template")
    start, end = len(marker), len(marker)+len(shared_header)
    if rendered[start:end] != shared_header or rendered[start:start+len(system)] != system:
        raise ValueError("Native content span mismatch")
    encoded = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
    ids, offsets = encoded["input_ids"], encoded["offset_mapping"]
    if ids != expected_input_ids[:prefix_tokens] or len(ids) != prefix_tokens:
        raise ValueError("Native offset encoding differs from frozen prefix")
    if tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True) != expected_input_ids:
        raise ValueError("Frozen complete input differs")
    header_ids = [i for i, (a, b) in enumerate(offsets) if b > a and a < end and b > start]
    covered = set()
    overlaps = []
    for i in header_ids:
        a, b = offsets[i]
        covered.update(range(max(a, start), min(b, end)))
        if a < start or b > end:
            overlaps.append(dict(position=i, offset=[a, b], text=rendered[a:b],
                                 before_header_chars=max(0, start-a), demo_overlap_chars=max(0, b-end)))
    if covered != set(range(start, end)):
        raise ValueError("Header character coverage incomplete")
    required = mandatory_positions(prefix_tokens, header_ids, True)
    anchors = mandatory_positions(prefix_tokens)
    return dict(header_char_span=[start, end], header_ids=header_ids, header_count=len(header_ids),
                header_token_offsets=[list(offsets[i]) for i in header_ids], boundary_overlaps=overlaps,
                anchor_ids=anchors, anchor_count=len(anchors), required_pinned_ids=required,
                required_pinned_count=len(required), extra_header_slots=len(required)-len(anchors),
                header_sha256=hashlib.sha256(shared_header.encode()).hexdigest(),
                prefix_tokens=prefix_tokens, budget=prefix_tokens//2,
                all_header_characters_covered=True, complete_native_input_equal=True)
