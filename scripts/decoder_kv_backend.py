"""Direct same-prefix next-logit backend. No model action at module import."""
import hashlib
import json
from pathlib import Path


def need(ok, message):
    if not ok:
        raise ValueError(message)


class SamePrefixBackend:
    def __init__(self, model, out, limits):
        import torch
        from transformers import DynamicCache
        self.torch, self.DynamicCache = torch, DynamicCache
        self.model, self.out, self.limits = model, Path(out), limits
        self.calls, self.tokens, self.vector_count = 0, 0, 0
        self.case_id = self.path = None
        self.vectors, self.cache_records = [], []

    def cache_bytes(self, cache):
        return sum(t.numel() * t.element_size() for layer in cache.layers for t in (layer.keys, layer.values))

    def raw(self, t):
        return t.detach().contiguous().view(self.torch.uint8).cpu().numpy().tobytes()

    def fingerprint(self, cache):
        h = hashlib.sha256()
        for layer in cache.layers:
            for t in (layer.keys, layer.values):
                h.update(self.raw(t))
        return h.hexdigest()

    def validate(self, cache, slots):
        need(len(cache.layers) == 28 and self.cache_bytes(cache) == slots * 57344, 'actual_cache_bytes')
        for layer in cache.layers:
            for t in (layer.keys, layer.values):
                need(tuple(t.shape) == (1, 4, slots, 128) and t.dtype == self.torch.bfloat16, 'actual_cache_shape_dtype')

    def copy_cache(self, reference, indices=None):
        result = self.DynamicCache()
        for i, layer in enumerate(reference.layers):
            values = []
            for t in (layer.keys, layer.values):
                c = t.clone() if indices is None else t.index_select(2, self.torch.tensor(indices, dtype=self.torch.long, device=t.device))
                expected = t if indices is None else t[:, :, indices, :]
                need(self.torch.equal(c, expected) and c.data_ptr() != t.data_ptr(), 'independent_exact_clone_or_gather')
                values.append(c)
            result.update(*values, i)
        return result

    def snapshot(self, cache, name, indices):
        path = self.out / (self.case_id + '.' + name + '.bf16')
        layout, offset = [], 0
        with path.open('xb') as f:
            for li, layer in enumerate(cache.layers):
                for kind, t in [('K', layer.keys), ('V', layer.values)]:
                    b = self.raw(t)
                    f.write(b)
                    layout.append(dict(layer=li, kind=kind, shape=list(t.shape), offset=offset, bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
                    offset += len(b)
        self.cache_records.append(dict(case_id=self.case_id, name=name, file=path.name, indices=indices,
                                       bytes=offset, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), tensors=layout))

    def forward(self, ids, logical_start, cache=None):
        physical = 0 if cache is None else int(cache.get_seq_length())
        length = len(ids)
        need(length > 0 and self.calls + 1 <= self.limits['forward_calls'] and self.tokens + length <= self.limits['input_tokens'], 'forward_resource_cap')
        self.calls += 1
        self.tokens += length
        torch = self.torch
        positions = list(range(logical_start, logical_start + length))
        cache_positions = list(range(physical, physical + length))
        row = dict(call=self.calls, case_id=self.case_id, path=self.path, input_ids=ids, logical_positions=positions,
                   cache_positions=cache_positions, physical_before=physical, physical_after_expected=physical + length,
                   attention_shape=[1, physical + length], attempted=True)
        with (self.out / 'forward_trace.jsonl').open('a') as f:
            f.write(json.dumps(row) + '\n')
        result = self.model(input_ids=torch.tensor([ids], device=self.model.device),
                            attention_mask=torch.ones((1, physical + length), dtype=torch.long, device=self.model.device),
                            position_ids=torch.tensor([positions], device=self.model.device),
                            cache_position=torch.tensor(cache_positions, device=self.model.device), past_key_values=cache,
                            use_cache=True, logits_to_keep=1)
        cache = result.past_key_values
        self.validate(cache, physical + length)
        need(tuple(result.logits.shape) == (1, 1, 152064) and bool(torch.isfinite(result.logits).all()), 'logit_shape_finite')
        return cache, result.logits[0, -1].float().cpu()

    def suffix(self, reference, ids, original_start, tokenwise=False):
        cache = self.copy_cache(reference)
        if tokenwise:
            for i, token in enumerate(ids):
                cache, logits = self.forward([token], original_start + i, cache)
        else:
            cache, logits = self.forward(ids, original_start, cache)
        # Appending suffix must preserve every cached-prefix value exactly.
        for a, b in zip(reference.layers, cache.layers):
            n = a.keys.shape[2]
            need(self.torch.equal(a.keys, b.keys[:, :, :n, :]) and self.torch.equal(a.values, b.values[:, :, :n, :]), 'suffix_changed_prefix_values')
        return logits

    def record_vector(self, name, logits):
        self.vector_count += 1
        need(self.vector_count <= self.limits['archived_vectors'], 'vector_cap')
        filename = self.case_id + '.' + name + '.f32'
        raw = self.raw(logits)
        (self.out / filename).write_bytes(raw)
        self.vectors.append(dict(case_id=self.case_id, name=name, file=filename, entries=len(logits), bytes=len(raw),
                                 sha256=hashlib.sha256(raw).hexdigest()))


def compare_vectors(p, q, allowed):
    # Float64 CPU diagnostic; independent verifier uses stdlib math from binary vectors.
    import torch
    p, q = p.double(), q.double()
    def kl(a, b):
        lp, lq = a.log_softmax(0), b.log_softmax(0)
        return max(0.0, float((lp.exp() * (lp - lq)).sum()))
    def maxima(a):
        return torch.where(a == a.max())[0].tolist()
    return dict(max_abs=float((p - q).abs().max()), global_KL=kl(p, q), allowed_KL=kl(p[allowed], q[allowed]),
                global_argmax_equal=maxima(p) == maxima(q), allowed_argmax_equal=maxima(p[allowed]) == maxima(q[allowed]))
