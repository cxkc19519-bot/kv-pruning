"""Independent serialized-evidence audit using Decimal and exhaustive byte-prefix sets.

Does not import the diagnostic module or fixture runner. No tokenizer/model.
"""
import sys
sys.dont_write_bytecode = True
import json
import math
import random
from decimal import Decimal, localcontext
from pathlib import Path


def need(test, reason):
    if not test:
        raise AssertionError(reason)


def near(actual, expected):
    need(type(actual) in (int, float) and math.isfinite(actual) and abs(actual - float(expected)) <= 1e-10, 'numeric_readback')


def dist(values, ids):
    with localcontext() as ctx:
        ctx.prec = 80
        vals = [Decimal(str(values[i])) for i in ids]
        peak = max(vals)
        weights = [(v - peak).exp() for v in vals]
        total = sum(weights)
        return [w / total for w in weights]


def audit_compare(spec, values):
    p = spec['p']
    need(len(values) == len(spec['qs']), 'candidate_count')
    for q, actual in zip(spec['qs'], values):
        supports = dict(global_vocab=list(range(len(p))), local_allowed=sorted(spec['allowed']))
        for k in spec['topks']:
            supports['top' + str(k)] = sorted(sorted(range(len(p)), key=lambda i: (-p[i], i))[:k])
        need(set(actual) == set(supports), 'objectives')
        for name, ids in supports.items():
            row = actual[name]
            need(row['support'] == ids, 'support_must_be_selected_from_Full_only')
            with localcontext() as ctx:
                ctx.prec = 80
                dp, dq = dist(p, ids), dist(q, ids)
                want = sum(x * (x.ln() - y.ln()) for x, y in zip(dp, dq))
                need(row['divergence']['status'] == 'finite', 'KL_status')
                near(row['divergence']['kl'], want)
                for label, logits, d in [('P', p, dp), ('Q', q, dq)]:
                    r = row[label]
                    need(r['ids'] == ids and r['argmax_ids'] == [i for i in ids if logits[i] == max(logits[j] for j in ids)], 'support_argmax')
                    for got, prob in zip(r['log_probabilities'], d):
                        near(got, prob.ln())
                    global_d = dist(logits, list(range(len(logits))))
                    mass = sum(global_d[i] for i in ids)
                    near(r['log_mass'], mass.ln())
                    near(r['mass'], mass)


def audit_grammar(spec, actual):
    outputs = {s.encode('utf-8') for s in spec['outputs']}
    vocab = {int(i): bytes.fromhex(h) for i, h in spec['vocabulary'].items()}
    prefixes = {s[:i] for s in outputs for i in range(len(s) + 1)}
    seen, changed = {b''}, True
    while changed:
        changed = False
        for prefix in sorted(prefixes):
            if prefix not in seen:
                continue
            for token in vocab.values():
                nxt = prefix + token
                if nxt in prefixes and nxt not in seen:
                    seen.add(nxt)
                    changed = True
    edges = []
    for prefix in sorted(seen):
        for token, chunk in vocab.items():
            if prefix + chunk in prefixes:
                edges.append(dict(prefix_hex=prefix.hex(), token=token, next_hex=(prefix + chunk).hex()))
        if prefix in outputs:
            edges.append(dict(prefix_hex=prefix.hex(), token=spec['eos_id'], next_hex=None))
    need(actual == dict(states=sorted(p.hex() for p in seen), accepted=sorted(p.hex() for p in outputs & seen),
                        edges=sorted(edges, key=lambda e: (e['prefix_hex'], e['token']))), 'complete_finite_grammar_graph')
    need(outputs <= seen and any(bytes.fromhex(x).endswith(b'\xc3') for x in actual['states']), 'all_outputs_and_partial_UTF8')
    need(len(json.loads(spec['outputs'][0])) == 1, 'JSON_fixture')


def audit_masks(spec, actual):
    n, b = spec['prefix_length'], spec['budget']
    anchors = sorted(i for i in range(n) if i < 4 or i >= n - 64)
    need(actual['anchors'] == anchors and actual['bytes_per_slot'] == 57344
         and actual['candidate_bytes'] == 57344 * b and actual['physical_gather_validated'] is False, 'charged_layout')
    if b < len(anchors):
        need(actual['status'] == 'infeasible_anchor_capacity' and actual['candidates'] == [], 'infeasible_not_dropped')
        return
    free = [i for i in range(n) if i not in anchors]
    count = b - len(anchors)
    picks = [sorted(free, key=lambda i: (-spec['scores'][i], i))[:count], sorted(free, reverse=True)[:count]]
    picks += [random.Random(s).sample(free, count) for s in spec['seeds']]
    names = ['adapted_snapkv', 'recency'] + ['random_' + str(s) for s in spec['seeds']]
    need(actual['status'] == 'feasible_index_plan' and len(actual['candidates']) == 8, 'eight_plans')
    for row, name, picked in zip(actual['candidates'], names, picks):
        need(row['name'] == name and row['indices'] == sorted(anchors + picked), 'fixed_mask')
        need(len(row['indices']) == len(set(row['indices'])) == b and set(anchors) <= set(row['indices']), 'equal_budget_anchors')


def main():
    out = Path(sys.argv[1])
    specs = json.loads((out / 'software_fixtures.json').read_text())
    results = json.loads((out / 'software_results.json').read_text())
    known = ['C01', 'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09', 'G01', 'G02', 'G03', 'G04', 'M01', 'M02', 'M03', 'M04', 'M05']
    need([s['id'] for s in specs] == [r['id'] for r in results] == known and all(r['passed'] is True for r in results), 'fixed18')
    rejections, edges, decimal_vectors = 0, 0, 0
    for spec, result in zip(specs, results):
        action, value = spec['action'], result['output']
        if action == 'compare':
            audit_compare(spec, value)
            decimal_vectors += len(value)
        elif action == 'kl':
            if spec['id'] == 'C06':
                need(value == dict(status='infinite', kl=None), 'infinite_KL_not_zero_or_JSON_Inf')
            else:
                need(value['status'] == 'finite', 'zero_P_ignored')
                near(value['kl'], Decimal(2).ln())
        elif action == 'reject_kl':
            need(value == ['indices_range_unique'] * 4 + ['logits_number'] * 3 + ['vocabulary_size']
                 + ['support_zero_mass'] * 2, 'reject_invalid_KL')
            rejections += len(value)
        elif action == 'grammar':
            audit_grammar(spec, value)
            edges = len(value['edges'])
        elif action == 'path':
            outputs = [s.encode() for s in spec['outputs']]
            vocab = {int(i): bytes.fromhex(v) for i, v in spec['vocabulary'].items()}
            prefix = b''
            need(len(value) == len(spec['tokens']), 'path_length')
            for row, chosen in zip(value, spec['tokens']):
                ids = sorted([i for i, chunk in vocab.items() if any(o.startswith(prefix + chunk) for o in outputs)]
                             + ([spec['eos_id']] if prefix in outputs else []))
                need(row == dict(prefix_hex=prefix.hex(), allowed=ids, chosen=chosen) and chosen in ids, 'all_legal_paths')
                if chosen == spec['eos_id']:
                    need(prefix in outputs, 'EOS_only_complete')
                else:
                    prefix += vocab[chosen]
            need(spec['tokens'][-1] == spec['eos_id'], 'terminal_path')
        elif action == 'reject_grammar':
            need(value == ['illegal_token', 'illegal_token', 'invalid_grammar_prefix', 'illegal_token',
                           'grammar_duplicates', 'vocabulary_tokens', 'vocabulary_tokens', 'unreachable_output'], 'reject_grammar')
            rejections += len(value)
        elif action == 'masks':
            audit_masks(spec, value)
        elif action == 'reject_masks':
            need(value == ['budget_range', 'budget_range', 'scores', 'six_unique_seeds', 'layout'], 'reject_masks')
            rejections += len(value)
    by = {r['id']: r['output'] for r in results}
    a, b = by['C01']
    need(a['global_vocab']['divergence']['kl'] < b['global_vocab']['divergence']['kl']
         and a['local_allowed']['divergence']['kl'] > b['local_allowed']['divergence']['kl'], 'synthetic_rank_reversal')
    need(a['local_allowed']['P']['argmax_ids'] == b['local_allowed']['Q']['argmax_ids'] == [0]
         and a['local_allowed']['Q']['argmax_ids'] == [1], 'synthetic_argmax')
    need(by['C02'][0]['global_vocab'] == by['C02'][0]['local_allowed'], 'all_allowed_control')
    need(by['C03'][0]['local_allowed']['divergence']['kl'] == 0, 'singleton_control')
    need(by['C04'][0]['local_allowed']['P']['mass'] == 0 and math.isfinite(by['C04'][0]['local_allowed']['P']['log_mass']), 'underflow_log_mass_preserved')
    need(len({tuple(c['indices']) for c in by['M03']['candidates']}) == 1, 'identical_candidate_ties_not_diversity')
    need(not any(n.startswith(('decoder_objective', 'accept_decoder_objective', 'torch', 'transformers', 'tokenizers')) for n in sys.modules), 'independent_no_project_import')
    summary = dict(passed=True, cases=18, invalid_variants_rejected=rejections, grammar_edges_recomputed=edges,
                   high_precision_candidate_vectors=decimal_vectors, method='80-digit Decimal and exhaustive byte-prefix graph; no diagnostic imports',
                   real_tokenizer_validated=False, physical_GPU_KV_validated=False, real_KV_signal_observed=False, model_answers=0)
    (out / 'independent_verification.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
