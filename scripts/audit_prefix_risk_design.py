"""Exact finite toy checks for a research-design gate; no model/data imports."""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import platform
import time
import traceback


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def binomial_cdf(n, k, p):
    return sum(Fraction(math.comb(n, i)) * p**i * (1-p)**(n-i) for i in range(k+1))


def compositions(total, parts):
    if parts == 1:
        yield (total,)
        return
    for first in range(total+1):
        for rest in compositions(total-first, parts-1):
            yield (first,) + rest


def multinomial_probability(counts, probabilities):
    coefficient = math.factorial(sum(counts))
    for count in counts:
        coefficient //= math.factorial(count)
    probability = Fraction(coefficient)
    for count, atom in zip(counts, probabilities):
        probability *= atom**count
    return probability


def fixed_sequence(pvalues, alpha):
    accepted = []
    for index, value in enumerate(pvalues):
        if value > alpha:
            break
        accepted.append(index)
    return accepted


def exact_multi_risk_checks(cfg, deadline):
    """Enumerate joint two-risk laws, preserving arbitrary within-prefix dependence.

    n iid prefixes each emit a pair of binary losses. Under the union null (one
    risk at or above its target), the max component p-value must reject no more
    often than the chosen test level. Enumerating outcomes is a numerical audit
    of examples; the general argument remains the LTT intersection-union proof.
    """
    denominator = cfg['probability_denominator']
    laws = [tuple(Fraction(x, denominator) for x in counts)
            for counts in compositions(denominator, 4)]
    rows = []
    total_outcomes = 0
    for n in cfg['sample_sizes']:
        distributions = []
        for atoms in laws:
            items = []
            for counts in compositions(n, 4):
                mass = multinomial_probability(counts, atoms)
                if mass:
                    items.append((counts[2]+counts[3], counts[1]+counts[3], mass))
                total_outcomes += 1
            assert sum(item[2] for item in items) == 1
            distributions.append((atoms, items))
        for target in map(lambda x: Fraction(str(x)), cfg['risk_targets']):
            pvalues = [binomial_cdf(n, k, target) for k in range(n+1)]
            for alpha in map(lambda x: Fraction(str(x)), cfg['test_levels']):
                for atoms, items in distributions:
                    q1, q2 = atoms[2]+atoms[3], atoms[1]+atoms[3]
                    if max(q1, q2) < target:
                        continue
                    chance = sum(mass for k1, k2, mass in items
                                 if max(pvalues[k1], pvalues[k2]) <= alpha)
                    assert chance <= alpha, (n, target, alpha, atoms, chance)
                    rows.append({'n': n, 'target': float(target), 'alpha': float(alpha),
                                 'atom_probabilities': list(map(float, atoms)),
                                 'null_risks': [float(q1), float(q2)],
                                 'false_joint_certification_probability': float(chance)})
                    if time.monotonic() > deadline:
                        raise TimeoutError('Design audit exceeded its frozen CPU wall-time ceiling')
    return rows, total_outcomes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=False)
    config_path = Path(args.config)
    cfg = json.loads(config_path.read_text(encoding='utf-8'))
    source = Path(__file__)
    (root / 'source_audit_prefix_risk_design.py').write_bytes(source.read_bytes())
    (root / 'proposal.json').write_bytes(config_path.read_bytes())
    manifest = {'status': 'running', 'start_unix': time.time(), 'pid': os.getpid(),
                'rows': 0, 'new_model_outputs': 0, 'args': vars(args),
                'source_sha256': sha(source), 'config_sha256': sha(config_path),
                'python': platform.python_version(),
                'scope': 'CPU exact probability/design audit; no models or empirical LLM outcomes'}
    write(root / 'manifest.json', manifest)
    try:
        assert cfg['execution_enabled'] is False and cfg['model_outputs_authorized_by_this_config'] == 0
        deadline = time.monotonic() + cfg['limits']['max_runtime_seconds']
        rows, outcome_count = exact_multi_risk_checks(cfg['exact_enumeration'], deadline)
        with (root / 'exact_probability_checks.jsonl').open('w', encoding='utf-8') as stream:
            for row in rows:
                stream.write(json.dumps(row) + '\n')
        epsilon = Fraction(str(cfg['statistical_example']['epsilon']))
        delta = Fraction(str(cfg['statistical_example']['delta']))
        minimum = next(n for n in range(1, 10000) if (1-epsilon)**n <= delta)
        grouped = next(n for n in range(1, 10000)
                       if (1-epsilon)**n <= delta/cfg['statistical_example']['risks'])
        assert minimum == 59 and grouped == 86
        true_clusters, queries = 8, 8
        pseudo_p = (1-epsilon)**(true_clusters*queries)
        correct_p = (1-epsilon)**true_clusters
        assert pseudo_p <= delta < correct_p
        single_false = binomial_cdf(60, 0, epsilon)
        adaptive_false = 1-(1-single_false)**16
        assert single_false <= delta < adaptive_false
        assert fixed_sequence([.01, .2, .001], .05) == [0]
        assert fixed_sequence([.2, .001], .05) == []
        # FullKV has zero degradation relative to itself, but may fail absolute safety.
        fallback = {'relative_degradation_risk': 0.0, 'absolute_violation_risk': .2,
                    'relative_contract_passes': True, 'absolute_contract_passes': False,
                    'valid_action_if_absolute_contract_required': 'reject_or_use_independently_verified_external_control'}
        # Toy allocation is a direct finite policy search, not a new optimization method.
        budgets = [Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1)]
        feasible = [pair for pair in itertools.product(budgets, repeat=2)
                    if pair[0] >= Fraction(1, 4) and pair[1] >= Fraction(3, 4)]
        best = min(feasible, key=sum)
        assert best == (Fraction(1, 4), Fraction(3, 4))
        summary = {'status': 'complete', 'new_model_outputs': 0,
                   'exact_joint_null_checks': len(rows), 'multinomial_outcomes_enumerated': outcome_count,
                   'all_checks_passed': True,
                   'zero_failure_sample_cost': {
                       'single_fixed_policy_all_components_must_pass_same_level': minimum,
                       'conservative_bonferroni_separately_reported_components': grouped,
                       'note': '59 per component under iid units for a single joint all-pass contract; not 59 total across groups, and no universal sample-size guarantee.'},
                   'cluster_pseudoreplication_example': {
                       'independent_prefixes': true_clusters, 'perfectly_correlated_queries_per_prefix': queries,
                       'wrong_iid_pvalue': float(pseudo_p), 'correct_prefix_pvalue': float(correct_p),
                       'actual_null_false_certification_probability_for_wrong_zero_failure_rule': float(correct_p)},
                   'sixteen_candidate_peeking_example': {'single_null_false_cert_probability': float(single_false),
                       'independent_candidates_unadjusted_any_pass_false_cert_probability': float(adaptive_false)},
                   'nonmonotone_risk_example': {'pvalues': [.01, .2, .001], 'fixed_sequence_accepts': [0],
                       'interpretation': 'Later passing candidates do not override a predeclared stop.'},
                   'absolute_safety_full_fallback_counterexample': fallback,
                   'toy_finite_budget_search': {'known_required_fractions': [.25, .75],
                       'optimal_mean_retention': float(sum(best)/2), 'uniform_feasible_retention': .75,
                       'interpretation': 'Illustration only; ordinary finite policy search, no measured model saving.'},
                   'methodological_novelty_gate': False,
                   'novelty_gate_provenance': 'Research judgment from the cited method reduction, not a consequence of the numerical checks or an automated novelty detector.',
                   'model_dev_execution_enabled': False,
                   'decision': 'NO-GO for the presently advertised generic method: multi-risk testing, prefix bundling and adaptive budget policies reduce to existing frameworks. Do not run the 256-output model DEV solely to repeat known degradation.',
                   'scope_limit': 'The gate rejects this specific claim, not every future KV-safety research direction.'}
        write(root / 'summary.json', summary)
        manifest.update(status='complete', end_unix=time.time(),
                        artifact_sha256={str(p.relative_to(root)): sha(p) for p in root.rglob('*')
                                         if p.is_file() and p.name != 'manifest.json'})
        write(root / 'manifest.json', manifest)
        print(json.dumps(summary, ensure_ascii=False))
    except Exception as error:
        manifest.update(status='failed', end_unix=time.time(), error_type=type(error).__name__,
                        error_message=str(error), traceback=traceback.format_exc())
        write(root / 'manifest.json', manifest)
        raise


if __name__ == '__main__':
    main()
