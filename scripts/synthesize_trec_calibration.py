"""Summarize frozen development and holdout separately, without model inference."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = Path('results/20261028-trec-holdout-v1')
    target = out / 'calibration_synthesis.json'
    assert not target.exists()
    inputs = {}
    cohorts = {}
    for name, run, expected in [
        ('development', '20261028-trec-pruning-v1', 32),
        ('holdout_questions', '20261028-trec-holdout-v1', 10),
    ]:
        root = Path('results') / run
        for filename in ['manifest.json', 'analysis_manifest.json', 'generations.jsonl', 'paired_analysis.json']:
            p = root / filename
            inputs[str(p)] = digest(p)
        assert json.loads((root / 'manifest.json').read_text())['status'] == 'complete'
        assert json.loads((root / 'analysis_manifest.json').read_text())['status'] == 'complete'
        rows = [json.loads(s) for s in (root / 'generations.jsonl').read_text().splitlines()]
        if name == 'development':
            baseline = Path('results/20261028-trec-context-full-v1/generations.jsonl')
            inputs[str(baseline)] = digest(baseline)
            full_rows = [r for r in map(json.loads, baseline.read_text().splitlines()) if r.get('condition') == 'with_demos']
        else:
            full_rows = [r for r in rows if r['method'] == 'full']
        assert len(full_rows) == expected
        full = {r['source_key']: r for r in full_rows}
        assert len(full) == expected
        by = {(r['source_key'], r['method']): r for r in rows}
        methods = sorted({r['method'] for r in rows} - {'full'})
        result = {'n': expected, 'source_keys': sorted(full), 'methods': {}, 'header_interventions': {}}
        result['full'] = {'exact': sum(r['metrics']['exact_correct'] for r in full_rows),
                          'format': sum(r['metrics']['whole_response_label_format'] for r in full_rows)}
        for method in methods:
            selected = [by[(key, method)] for key in full]
            transitions = Counter(('C' if full[r['source_key']]['metrics']['exact_correct'] else 'W') + '2' +
                                  ('C' if r['metrics']['exact_correct'] else 'W') for r in selected)
            result['methods'][method] = {'exact': sum(r['metrics']['exact_correct'] for r in selected),
                'format': sum(r['metrics']['whole_response_label_format'] for r in selected),
                'full_to_compressed': {s: transitions[s] for s in ['C2C', 'C2W', 'W2C', 'W2W']},
                'loss_denominator': result['full']['exact']}
        for method in methods:
            if method.endswith('_header_pinned'):
                continue
            pairs = [(by[(key, method)], by[(key, method + '_header_pinned')]) for key in full]
            changes = {}
            for metric in ['exact_correct', 'whole_response_label_format']:
                count = Counter(('C' if a['metrics'][metric] else 'W') + '2' +
                                ('C' if b['metrics'][metric] else 'W') for a, b in pairs)
                changes[metric] = {s: count[s] for s in ['C2C', 'C2W', 'W2C', 'W2W']}
            result['header_interventions'][method] = changes
        cohorts[name] = result
    assert not set(cohorts['development']['source_keys']) & set(cohorts['holdout_questions']['source_keys'])
    result = {'status': 'complete', 'created_unix': time.time(), 'new_model_outputs': 0,
              'source_sha256': digest(Path(__file__)), 'input_sha256': inputs, 'cohorts': cohorts,
              'decision': 'Close this calibration round; no automatic expansion of cases, seeds, budgets, models or prompts.',
              'limitations': ['Shared demonstrations; question holdout is not an independent dataset.',
                              'Single fixed seed, one model and one budget; no stable method ranking.',
                              'Classification and exact label-format evidence do not establish general safety effects or novelty.']}
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / ('source_' + Path(__file__).name)).write_bytes(Path(__file__).read_bytes())
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
