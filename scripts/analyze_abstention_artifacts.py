"""Independent descriptive checks of pinned released outputs; no upstream imports."""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import time
import traceback


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def counts(rows, key):
    return dict(Counter(row[key] for row in rows))


def kappa(pairs):
    n = len(pairs)
    a, b = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    agreement = sum(x == y for x, y in pairs) / n
    chance = sum(a[v] * b[v] for v in a.keys() | b.keys()) / n**2
    return dict(n=n, agreement=agreement, kappa=(agreement-chance)/(1-chance))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--artifacts', required=True)
    parser.add_argument('--sources', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (root / 'analysis_source.py').write_bytes(source)
    manifest = dict(status='running', start_unix=time.time(), args=vars(args),
                    source_sha256=sha(source), new_model_outputs=0, rows=0,
                    scope='Released-output descriptive audit, not a model reproduction or semantic gold reannotation')
    save(root / 'manifest.json', manifest)
    try:
        origin = Path(args.artifacts)
        fetched = json.loads((origin / 'manifest.json').read_text())
        assert fetched['status'] == 'complete'
        for f in fetched['files']:
            raw = (origin / 'upstream' / f['path']).read_bytes()
            assert sha(raw) == f['sha256'] and len(raw) == f['bytes']
        scoring = Path(args.sources) / 'upstream/src/eval/honest_accuracy.py'
        tree = ast.parse(scoring.read_text())
        markers = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ABSTENTION_MARKERS' for t in node.targets):
                markers = ast.literal_eval(node.value)
        assert isinstance(markers, list) and all(isinstance(m, str) for m in markers)
        broad = {'based on the information provided', 'based on the context provided'}
        data = origin / 'upstream/artifacts/eval'
        bases = read_rows(data / 'v1_eval_base_compressed_kvzip.jsonl')
        adapters = read_rows(data / 'v1_eval_mixture_cc_kvzip.jsonl')
        key = lambda r: (r['id'], r['ratio'])
        assert len(set(map(key, bases))) == len(bases) == len(adapters) == 463
        assert list(map(key, bases)) == list(map(key, adapters))
        for a, b in zip(bases, adapters):
            assert all(a[k] == b[k] for k in ['gold_label', 'gold_answer', 'n_kept', 'inference_mode'])
        summary = dict(paired_rows=463, unique_sources=len({r['id'] for r in bases}),
                       scoring_source_sha256=sha(scoring.read_bytes()),
                       inference_modes=counts(bases, 'inference_mode'), models={},
                       caveats=['Output aliases are not stored, so gold-only matching is diagnostic only.',
                                'A broad-marker flag is not an adjudicated scoring error.',
                                'Judge rows evaluate 1D text masks, not actual layered KV information.',
                                'Ratios from one source are correlated; no iid confidence interval reported.'])
        flagged = []
        for name, rows in [('base', bases), ('mixture', adapters)]:
            details = []
            for r in rows:
                head = r['response'].lower().strip()[:200]
                hits = [m for m in markers if m in head]
                assert bool(hits) == r['model_abstained']
                gold = r['gold_answer'].strip().lower()
                flag = dict(model=name, id=r['id'], ratio=r['ratio'],
                            classification=r['classification'], gold_label=r['gold_label'],
                            marker_hits=hits, broad_only=bool(hits) and not any(m not in broad for m in hits),
                            gold_string_present=bool(gold) and gold in r['response'].lower(),
                            response=r['response'], gold_answer=r['gold_answer'])
                details.append(flag)
                if hits:
                    flagged.append(flag)
            total = len(rows)
            per_ratio = {}
            for ratio in sorted({r['ratio'] for r in rows}):
                subset = [r for r in rows if r['ratio'] == ratio]
                per_ratio[str(ratio)] = dict(n=len(subset), counts=counts(subset, 'classification'))
            broad_only = [d for d in details if d['broad_only']]
            model = dict(n=total, classes=counts(rows, 'classification'), gold_labels=counts(rows, 'gold_label'),
                         honest_accuracy=sum(r['classification'] == 'correct' for r in rows)/total,
                         hallucination_rate=sum(r['classification'] in ['hallucinated', 'wrong_answer'] for r in rows)/total,
                         abstention_count=sum(r['model_abstained'] for r in rows),
                         any_broad_marker=sum(any(m in broad for m in d['marker_hits']) for d in details),
                         broad_only_count=len(broad_only),
                         broad_only_classes=counts(broad_only, 'classification'),
                         marker_and_gold_string=sum(bool(d['marker_hits']) and d['gold_string_present'] for d in details),
                         per_ratio=per_ratio)
            summary['models'][name] = model
        samples = read_rows(data / 'block4_sample.jsonl')
        judges = read_rows(data / 'block4_judge_log.jsonl')
        assert len(samples) == len(judges) == 400
        sample_keys = {(r['id'], r['ratio'], r['label_type']) for r in samples}
        assert len(sample_keys) == 400
        assert sample_keys == {(r['id'], r['ratio'], r['label_type']) for r in judges}
        verdict_pairs = [('YES' if r['label_type'] == 'confident_answer' else 'NO', r['verdict']) for r in judges]
        strict = [(a,b) for a,b in verdict_pairs if b != 'PARTIAL']
        cross = Counter((r['label_type'], r['verdict']) for r in judges)
        by_ratio = defaultdict(Counter)
        for r in judges:
            by_ratio[str(r['ratio'])][r['label_type']+'->'+r['verdict']] += 1
        span_lengths = Counter()
        for r in samples:
            mask = r['kept_mask']
            assert len(mask) == r['metadata']['ctx_len']
            assert sum(mask) == r['metadata']['n_kept']
            observed = []
            for s in r['metadata']['supporting_spans']:
                assert 0 <= s['start'] < s['end'] <= len(mask)
                span_lengths[s['end']-s['start']] += 1
                observed.append(sum(mask[s['start']:s['end']])/(s['end']-s['start']))
            expected = r['metadata']['span_retentions']
            # Released metadata serializes these diagnostic fractions to three decimals.
            # Compare at that published precision; keep the original mask exact.
            assert len(observed) == len(expected) and all(round(a, 3) == b for a,b in zip(observed, expected))
        summary['label_judge'] = dict(n=400, cross={a+'->'+b:c for (a,b),c in cross.items()},
                                     strict=kappa(strict), partial_count=400-len(strict),
                                     by_ratio={r:dict(c) for r,c in by_ratio.items()},
                                     annotated_span_token_lengths=dict(sorted(span_lengths.items())),
                                     interpretation='Author LLM judge judgments, already disclosed by author; not our semantic ground truth.')
        save(root / 'summary.json', summary)
        (root / 'flagged_outputs.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in flagged))
        manifest.update(status='complete', end_unix=time.time(), input_manifest_sha256=sha((origin/'manifest.json').read_bytes()),
                        input_file_sha256={f['path']:f['sha256'] for f in fetched['files']},
                        artifact_sha256={str(p.relative_to(root)):sha(p.read_bytes()) for p in root.iterdir() if p.is_file() and p.name != 'manifest.json'})
    except Exception as error:
        manifest.update(status='failed', end_unix=time.time(), error_type=type(error).__name__,
                        error_message=str(error), traceback=traceback.format_exc())
        raise
    finally:
        save(root / 'manifest.json', manifest)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
