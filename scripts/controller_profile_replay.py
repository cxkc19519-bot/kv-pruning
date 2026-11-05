"""Posthoc N1 replay of existing features with the new native profile table.

This is a CPU counterfactual, not observed budgets in the new engine, not a
normal-workload distribution estimate, and not a history/latency experiment.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path

from analyze_controller_natural_history import choose_budget


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run-dir', required=True)
    args = ap.parse_args(); out = Path(args.run_dir).resolve()
    root = Path(__file__).resolve().parents[1]
    prior = root/'results/20261030-controller-natural-history-v2'
    assert sha(prior/'manifest.json') == 'f802fb66a3e8f54f666af88bc534249dd4ac493ba80829778835b421ad73f7df'
    raw = prior/'real_feature_selector_replay.json'
    data = json.loads(raw.read_text()); assert len(data['rows']) == 397
    summary = json.loads((prior/'summary.json').read_text())
    analysis = json.loads((out/'independent_profile_analysis.json').read_text())
    final = next(x for x in analysis['blocks'] if not x['profile_only'])
    cost = final['cost_tables']; b = summary['boundaries']
    states = {name:b[key]['status'] for name,key in [
        ('common','common'),('A','A_history_after'),('B','B_history_after')]}
    rows = []
    for original in data['rows']:
        x = original['features']; choices = {}; margins = {}
        for name,state in states.items():
            p = [1/(1+math.exp(-(state['slope']*f+v))) for f,v in zip(x,state['intercepts'])]
            budget, scores = choose_budget([p], *cost)
            ordered = sorted(scores, reverse=True)
            choices[name] = budget; margins[name] = ordered[0]-ordered[1]
        rows.append(dict(label=original['label'], event_index=original['event_index'],
            choices=choices, objective_margins=margins))
    result = dict(kind='posthoc_N1_CPU_counterfactual', status='complete',
        old_feature_file_sha256=sha(raw), new_profile_analysis_sha256=sha(out/'independent_profile_analysis.json'),
        vectors=len(rows), unique_vectors=data['unique_vectors'],
        choices={n:dict(collections.Counter(str(x['choices'][n]) for x in rows)) for n in states},
        differences_from_common={n:sum(x['choices'][n] != x['choices']['common'] for x in rows) for n in ['A','B']},
        min_objective_margin={n:min(x['objective_margins'][n] for x in rows) for n in states},
        qualification='Saved features with substituted cost table and fixed old coefficients; no new-engine budgets or outputs inferred; no latency or normal coverage evidence', rows=rows)
    p = out/'existing_feature_replay.json'; assert not p.exists()
    p.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    (out/'source_controller_profile_replay.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__': main()
