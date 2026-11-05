"""CPU audit of frozen guard outputs; no model forward or experiment selection."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import time
import traceback

from transformers import AutoTokenizer


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def judgment(text):
    # Independent implementation of the frozen unique-complete-tag contract.
    openings = list(re.finditer(r'<Judgment\b', text, re.I))
    complete = list(re.finditer(r'<Judgment>\s*(safe|unsafe)\s*</Judgment>', text, re.I))
    if len(openings) != 1 or len(complete) != 1:
        return None
    return int(complete[0].group(1).lower() == 'unsafe')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    args = parser.parse_args()
    root = Path(args.run)
    assert not (root/'analysis_manifest.json').exists()
    raw_source = Path(__file__).read_bytes()
    (root/'source_analyze_action_guard_full_gate.py').write_bytes(raw_source)
    manifest = dict(status='running', start_unix=time.time(), new_model_outputs=0,
                    source_sha256=digest(raw_source), args=vars(args))
    save(root/'analysis_manifest.json', manifest)
    try:
        run = json.loads((root/'manifest.json').read_text())
        assert run['status'] == 'complete'
        raw_proposal = (root/'proposal.json').read_bytes()
        assert digest(raw_proposal) == run['config_sha256']
        proposal = json.loads(raw_proposal)
        assert proposal['execution_enabled'] is False
        snapshot = json.loads((root/'execution_snapshot.json').read_text())
        assert snapshot['execution_enabled'] is True
        for key, value in proposal.items():
            if key != 'execution_enabled':
                assert snapshot[key] == value, key
        for name, expected in run['source_sha256'].items():
            assert digest((root/('source_'+name)).read_bytes()) == expected
        assert snapshot['source_sha256'] == run['source_sha256']
        native = Path(proposal['native_source_run'])/'upstream'
        for name, expected in snapshot['native_source_sha256'].items():
            assert digest((native/name).read_bytes()) == expected
        raw_cases = (root/'cases.jsonl').read_bytes()
        assert digest(raw_cases) == proposal['cases_sha256']
        assert raw_cases == (Path(proposal['overlap_run'])/'frozen_cases.jsonl').read_bytes()
        cases = [json.loads(line) for line in raw_cases.splitlines()]
        assert len(cases) == 32 and Counter(c['gold'] for c in cases) == {0: 16, 1: 16}
        modeldir = Path(proposal['model_dir'])
        tokenizer = AutoTokenizer.from_pretrained(modeldir, local_files_only=True, trust_remote_code=False)
        for case in cases:
            for condition in proposal['conditions']:
                messages = [dict(role='user', content=case['rendered'][condition]['prompt'])]
                ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
                assert ids == case['encoded'][condition]['input_ids']
        weights = json.loads((root/'weight_checks.json').read_text())
        expected_weights = json.loads(Path('configs/stepguard-model-artifacts-v1.json').read_text())
        assert len(weights) == len(expected_weights['files']) == 10
        by_weight = {r['path']: r for r in weights}
        assert len(by_weight) == 10
        for entry in expected_weights['files']:
            check = by_weight[entry['rfilename']]
            expected = entry['lfs']['sha256'] if entry.get('lfs') else entry['blobId']
            assert check['verified'] and check['digest'] == expected and check['size'] == entry['size']
            path = modeldir/entry['rfilename']
            assert path.stat().st_size == entry['size'] and path.stat().st_mtime_ns == check['mtime_ns']
        engineering = [json.loads(line) for line in (root/'engineering.jsonl').read_text().splitlines()]
        assert len(engineering) == run['engineering_outputs'] == 18
        engineering_by = {(r['key'], r['condition'], r['mode']): r for r in engineering}
        assert len(engineering_by) == 18
        eos = set(proposal['decoding']['eos_token_ids'])
        for case in cases[:3]:
            for condition in proposal['conditions']:
                outputs = [engineering_by[(case['key'], condition, mode)]['generated_ids']
                           for mode in ['native_whole', 'native_cached', 'custom_cached']]
                assert outputs[0] == outputs[1] == outputs[2]
                assert outputs[0][-1] in eos
        rows = [json.loads(line) for line in (root/'generations.jsonl').read_text().splitlines()]
        assert len(rows) == run['rows'] == run['new_model_outputs'] == 64
        by = {(r['key'], r['condition']): r for r in rows}
        assert len(by) == 64
        diagnostics = []
        for case in cases:
            for condition in proposal['conditions']:
                row = by[(case['key'], condition)]
                assert row['gold'] == case['gold']
                if row['status'] != 'ok':
                    assert row['strict_prediction'] is None and row['strict_correct'] is False
                    continue
                ids = row['generated_ids']
                assert 0 < len(ids) <= proposal['decoding']['max_new_tokens']
                assert row['output_tokens'] == len(ids)
                text = tokenizer.decode(ids, skip_special_tokens=True)
                assert text == row['response']
                pred = judgment(text)
                assert pred == row['strict_prediction']
                assert row['strict_correct'] == (pred == case['gold'])
                assert row['truncated'] == (ids[-1] not in eos)
                # Retain a lossless decode as a diagnostic, never re-score to improve the gate.
                diagnostics.append(dict(key=case['key'], condition=condition,
                                        raw_decode=tokenizer.decode(ids, skip_special_tokens=False),
                                        prediction=pred, native_prediction=row['native_compatibility_prediction']))
                if case in cases[:3]:
                    assert ids == engineering_by[(case['key'], condition, 'native_whole')]['generated_ids']
        result = {}
        for condition in proposal['conditions']:
            subset = [by[(c['key'], condition)] for c in cases]
            result[condition] = dict(
                n=len(subset), correct=sum(r['strict_correct'] for r in subset),
                valid_judgment=sum(r['strict_prediction'] is not None for r in subset),
                errors=sum(r['status'] != 'ok' for r in subset),
                truncated=sum(r['truncated'] for r in subset),
                by_class={str(g): dict(n=sum(r['gold'] == g for r in subset),
                                       correct=sum(r['gold'] == g and r['strict_correct'] for r in subset)) for g in [0, 1]},
                confusion={f'{gold}->{pred}': sum(r['gold'] == gold and r['strict_prediction'] == pred for r in subset)
                           for gold in [0, 1] for pred in [0, 1, None]},
                native_disagreements=sum(r['strict_prediction'] != r.get('native_compatibility_prediction') for r in subset))
        pairs = [(by[(c['key'], 'full')], by[(c['key'], 'no_history')]) for c in cases]
        result['paired'] = dict(
            n=32, transitions=dict(Counter(('C' if a['strict_correct'] else 'W')+'2'+('C' if b['strict_correct'] else 'W') for a, b in pairs)),
            full_correct_no_history_wrong=sum(a['strict_correct'] and not b['strict_correct'] for a, b in pairs),
            unsafe_full_correct_no_history_clear=sum(a['gold'] == 1 and a['strict_correct'] and b['strict_prediction'] == 0 for a, b in pairs))
        original = json.loads((root/'summary.json').read_text())
        for condition in proposal['conditions']:
            for name in ['n', 'correct', 'valid_judgment', 'errors', 'truncated', 'by_class']:
                assert result[condition][name] == original[condition][name], (condition, name)
        assert result['paired'] == original['paired']
        g = proposal['gate']; full = result['full']; paired = result['paired']
        criteria = dict(full_correct=full['correct'] >= g['full_correct_min'],
                        class_correct=all(full['by_class'][str(v)]['correct'] >= g['each_class_correct_min'] for v in [0, 1]),
                        unique_judgment=full['valid_judgment'] == g['full_unique_complete_judgment_required'],
                        full_errors=full['errors'] <= g['full_errors_allowed'],
                        truncation=sum(result[x]['truncated'] for x in proposal['conditions']) <= g['truncated_outputs_allowed'],
                        history_support=paired['full_correct_no_history_wrong'] >= g['full_correct_no_history_wrong_min'],
                        unsafe_false_clear=paired['unsafe_full_correct_no_history_clear'] >= g['unsafe_full_correct_no_history_clear_min'])
        result.update(criteria=criteria, task_support_gate=all(criteria.values()),
                      compression_executed=False, new_model_outputs=0,
                      limitations='Development cohort only; NoHistory changes text and positions. Not a KV-pruning effect or a novelty test.')
        assert result['task_support_gate'] == original['task_support_gate'] == run['task_support_gate']
        save(root/'independent_summary.json', result)
        save(root/'decode_diagnostics.json', diagnostics)
        manifest.update(status='complete', end_unix=time.time(), verified_rows=64, engineering_rows=18,
                        task_support_gate=result['task_support_gate'],
                        verified_artifact_sha256={name: digest((root/name).read_bytes()) for name in
                            ['proposal.json', 'execution_snapshot.json', 'cases.jsonl', 'engineering.jsonl', 'generations.jsonl', 'summary.json', 'independent_summary.json']})
        print(json.dumps(result, ensure_ascii=False))
    except Exception as error:
        manifest.update(status='failed', end_unix=time.time(), error_type=type(error).__name__,
                        error_message=str(error), traceback=traceback.format_exc())
        raise
    finally:
        save(root/'analysis_manifest.json', manifest)


if __name__ == '__main__':
    main()
