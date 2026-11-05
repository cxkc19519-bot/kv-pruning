"""Local-mask diagnostics; finite byte-vocabulary contract, not an HF tokenizer adapter.

No model dependencies. A local grammar mask does not implement sequence-conditional
sampling. Candidate masks here are index plans, not evidence of physical GPU gather.
"""
import math
import random


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def integers(values, size, nonempty=True):
    require(isinstance(values, (list, tuple)), 'indices_type')
    require((bool(values) or not nonempty) and all(type(i) is int and 0 <= i < size for i in values)
            and len(values) == len(set(values)), 'indices_range_unique')
    return sorted(values)


def logits_checked(values):
    require(isinstance(values, (list, tuple)) and bool(values), 'logits_empty')
    require(all(type(v) in (int, float) and not math.isnan(v) and v != math.inf for v in values), 'logits_number')
    require(any(v != -math.inf for v in values), 'zero_mass')
    return list(values)


def log_distribution(values, support):
    values = logits_checked(values)
    support = integers(support, len(values))
    maximum = max(values[i] for i in support)
    require(maximum != -math.inf, 'support_zero_mass')
    shifted = [values[i] - maximum for i in support]
    require(all(v != -math.inf or values[i] == -math.inf for i, v in zip(support, shifted)), 'numeric_overflow')
    denominator = math.log(math.fsum(math.exp(v) for v in shifted))
    logs = [v - denominator for v in shifted]
    return support, logs


def distribution_kl(p, q, support):
    p, q = logits_checked(p), logits_checked(q)
    require(len(p) == len(q), 'vocabulary_size')
    ids, lp = log_distribution(p, support)
    _, lq = log_distribution(q, ids)
    if any(a != -math.inf and b == -math.inf for a, b in zip(lp, lq)):
        return dict(status='infinite', kl=None)
    terms = [math.exp(a) * (a - b) for a, b in zip(lp, lq) if a != -math.inf]
    require(all(math.isfinite(v) for v in terms), 'numeric_overflow')
    value = math.fsum(terms)
    require(value >= -1e-12, 'negative_KL')
    return dict(status='finite', kl=max(0.0, value))


def support_summary(logits, support):
    ids, logs = log_distribution(logits, support)
    _, global_logs = log_distribution(logits, list(range(len(logits))))
    local_max = max(logits[i] for i in ids)
    # Subtract shifted log normalizers instead of taking log of an underflowed mass.
    reference = ids[max(range(len(ids)), key=lambda j: logits[ids[j]])]
    log_mass = global_logs[reference] - logs[ids.index(reference)]
    return dict(ids=ids, log_probabilities=[None if v == -math.inf else v for v in logs], log_mass=log_mass,
                mass=math.exp(log_mass), argmax_ids=[i for i in ids if logits[i] == local_max])


def top_support(logits, k):
    logits = logits_checked(logits)
    require(type(k) is int and 1 <= k <= len(logits), 'topk_range')
    return sorted(sorted(range(len(logits)), key=lambda i: (-logits[i], i))[:k])


def compare(p, q, allowed, topks):
    p, q = logits_checked(p), logits_checked(q)
    require(len(p) == len(q), 'vocabulary_size')
    all_ids = list(range(len(p)))
    supports = dict(global_vocab=all_ids, local_allowed=integers(allowed, len(p)))
    for k in topks:
        supports['top' + str(k)] = top_support(p, k)
    return {name: dict(support=ids, divergence=distribution_kl(p, q, ids),
                       P=support_summary(p, ids), Q=support_summary(q, ids)) for name, ids in supports.items()}


class FiniteByteGrammar:
    """Every accepted UTF-8 byte string, every possible vocabulary segmentation.

    Tokens must have immutable context-independent bytes. Real-tokenizer conversion
    needs a separately validated adapter; token.encode/decode is not assumed equal.
    EOS is accepted only at a complete string and ends the grammar state.
    """
    def __init__(self, outputs, vocabulary, eos_id):
        require(isinstance(outputs, list) and bool(outputs) and all(isinstance(x, str) and x for x in outputs), 'grammar_outputs')
        require(len(outputs) == len(set(outputs)), 'grammar_duplicates')
        self.outputs = tuple(x.encode('utf-8') for x in outputs)
        require(isinstance(vocabulary, dict) and bool(vocabulary) and type(eos_id) is int and eos_id >= 0, 'vocabulary_type')
        require(all(type(i) is int and i >= 0 and isinstance(b, bytes) and bool(b) for i, b in vocabulary.items())
                and eos_id not in vocabulary, 'vocabulary_tokens')
        self.vocabulary, self.eos_id = dict(vocabulary), eos_id

    def allowed(self, prefix):
        require(isinstance(prefix, bytes) and any(o.startswith(prefix) for o in self.outputs), 'invalid_grammar_prefix')
        ids = [i for i, b in self.vocabulary.items() if any(o.startswith(prefix + b) for o in self.outputs)]
        if prefix in self.outputs:
            ids.append(self.eos_id)
        return sorted(ids)

    def advance(self, prefix, token):
        require(type(token) is int and token in self.allowed(prefix), 'illegal_token')
        return None if token == self.eos_id else prefix + self.vocabulary[token]

    def reachable(self):
        pending, seen, accepted, edges = [b''], set(), set(), []
        while pending:
            prefix = pending.pop()
            if prefix in seen:
                continue
            seen.add(prefix)
            for token in self.allowed(prefix):
                nxt = self.advance(prefix, token)
                edges.append(dict(prefix_hex=prefix.hex(), token=token, next_hex=None if nxt is None else nxt.hex()))
                if nxt is None:
                    accepted.add(prefix)
                else:
                    pending.append(nxt)
        require(accepted == set(self.outputs), 'unreachable_output')
        return dict(states=sorted(p.hex() for p in seen), accepted=sorted(p.hex() for p in accepted),
                    edges=sorted(edges, key=lambda e: (e['prefix_hex'], e['token'])))


def candidate_masks(prefix_length, budget, scores, seeds, layout):
    require(type(prefix_length) is int and prefix_length > 0 and type(budget) is int and 0 <= budget <= prefix_length, 'budget_range')
    require(isinstance(scores, list) and len(scores) == prefix_length
            and all(type(v) in (int, float) and math.isfinite(v) for v in scores), 'scores')
    require(isinstance(seeds, list) and len(seeds) == 6 and all(type(s) is int for s in seeds) and len(set(seeds)) == 6, 'six_unique_seeds')
    require(isinstance(layout, list) and len(layout) == 4 and all(type(x) is int and x > 0 for x in layout), 'layout')
    # Layout = [Full layers, KV heads, head dimension, bytes per scalar]; K and V.
    bytes_per_slot = 2 * math.prod(layout)
    anchors = sorted(set(range(min(4, prefix_length))) | set(range(max(0, prefix_length - 64), prefix_length)))
    base = dict(prefix_length=prefix_length, budget=budget, anchors=anchors, bytes_per_slot=bytes_per_slot,
                candidate_bytes=budget * bytes_per_slot, physical_gather_validated=False)
    if len(anchors) > budget:
        return dict(base, status='infeasible_anchor_capacity', candidates=[])
    eligible = sorted(set(range(prefix_length)) - set(anchors))
    remaining = budget - len(anchors)
    plans = [('adapted_snapkv', sorted(eligible, key=lambda i: (-scores[i], i))[:remaining]),
             ('recency', sorted(eligible, reverse=True)[:remaining])]
    plans += [('random_' + str(seed), random.Random(seed).sample(eligible, remaining)) for seed in seeds]
    return dict(base, status='feasible_index_plan', candidates=[dict(name=name, indices=sorted(anchors + picked)) for name, picked in plans])
