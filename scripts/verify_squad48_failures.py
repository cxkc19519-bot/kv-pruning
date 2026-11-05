"""Independent stdlib readback of posthoc taxonomy; no analyzer imports."""
import sys
sys.dont_write_bytecode = True
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import signal
import time
from verify_hf_DEV_acceptance import independent_score


def read(path): return json.loads(path.read_text())
def rows(path): return [json.loads(line) for line in path.read_text().splitlines()]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def label(row):
    # Deliberately implemented as a state table and an EM/format 2x2 lookup.
    special = {'infeasible_budget': 'budget_infeasible', 'error': 'execution_error', 'not_run': 'not_run', 'protocol_stopped': 'not_run'}
    if row['execution_state'] != 'ok': return special[row['execution_state']]
    if row['truncated'] is True: return 'truncated'
    if row['task_EM'] is None: return 'task_unavailable'
    return (('neither', 'format_only'), ('task_only', 'joint_success'))[int(row['task_EM'])][int(row['format'])]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--proposal-sha256', required=True); args = ap.parse_args()
    start = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *unused: (_ for _ in ()).throw(TimeoutError('independent60_second_cap'))); signal.alarm(60)
    root = Path(__file__).resolve().parent.parent
    assert str(root) == '/home/user/jhk/project/Directional Exploration/kv-pruning'
    proposal = root / 'configs/squad48-error-taxonomy-v1.json'; assert sha(proposal) == args.proposal_sha256
    cfg = read(proposal); out = root / cfg['run']
    for n, pin in read(out / 'manifest.json').items(): assert sha(out / n) == pin, n
    for n, pin in {**cfg['inputs'], **cfg['source_sha256']}.items(): assert sha(root / n) == pin, n
    parent = root / cfg['parent_run']
    for manifest in ('manifest.json', 'derived_manifest.json'):
        for n, pin in read(parent / manifest).items(): assert sha(parent / n) == pin, (manifest, n)
    summary = read(out / 'summary.json'); assert summary['status'] == 'complete' and summary['main_outputs'] == summary['engineering_outputs'] == 0
    assert not any(read(out / 'CPU_guard_observations.json').values())
    categories = ['joint_success', 'task_only', 'format_only', 'neither', 'task_unavailable', 'truncated', 'budget_infeasible', 'execution_error', 'not_run']
    software = read(out / 'software_acceptance.json')
    assert len(software) == 9 and [s['id'] for s in software] == ['E%02d' % i for i in range(1, 10)]
    for s, want in zip(software, categories): assert s['passed'] and s['expected'] == s['actual'] == want == label(s['input'])
    originals = rows(root / cfg['normalized']); normalized = {(r['case_id'], r['condition_id']): r for r in originals}
    original_scored = rows(root / cfg['scored']); scored = {(r['case_id'], r['condition_id']): r for r in original_scored}
    cases = rows(root / cfg['selected']); source = {c['case_id']: c for c in cases}; ids = [c['case_id'] for c in cases]
    names = ['full', 'adapted_snapkv', 'uniform_random']
    assert len(normalized) == len(originals) == 144 and len(scored) == len(original_scored) == 138
    assert len(ids) == len(set(ids)) == len({c['context_group_id'] for c in cases}) == 48
    assert set(normalized) == {(cid, name) for cid in ids for name in names}
    classified = rows(out / 'annotated_cells.jsonl'); report = read(out / 'taxonomy_report.json')
    assert [(r['case_id'], r['condition_id']) for r in classified] == [(cid, name) for cid in ids for name in names]
    reason_mapping = {'whole_plain_text': 'unstructured_plain_text', 'json_string': 'JSON_string_wrong_root',
                      'json_scalar_as_plain_text': 'JSON_scalar_wrong_root', 'unsupported_json_root': 'JSON_array_wrong_root',
                      'no_string_answer': 'object_without_string_answer', 'object_answer': 'object_extra_keys_or_empty_answer',
                      'structured_parse_failure': 'malformed_structured_output', 'bom': 'BOM_rejected', 'duplicate_key': 'duplicate_key',
                      'nonfinite_constant': 'nonfinite_constant', 'invalid_unicode': 'invalid_unicode'}
    reclassified = []
    for cell in classified:
        key = cell['case_id'], cell['condition_id']; original = normalized[key]; raw = scored.get(key)
        assert cell['context_group_id'] == original['context_group_id'] == source[key[0]]['context_group_id']
        assert cell['category'] == label(original) and cell['baseline_category'] == label(normalized[key[0], 'full'])
        for field in ('execution_state', 'budget_state', 'truncated', 'input_digest', 'gold_digest', 'comparison_digest'): assert cell[field] == original[field]
        assert cell['raw_EM'] == original['task_EM'] and cell['raw_F1'] == original['task_F1'] and cell['raw_format'] is original['format']
        assert cell['completed'] == (original['execution_state'] == 'ok' and original['truncated'] is False)
        if original['execution_state'] == 'ok':
            scores = independent_score(raw['text'], [a['text'] for a in source[key[0]]['answers']])
            assert scores == raw['scores'] and raw['normalized'] == original
            assert original['task_EM'] == (None if scores['em'] is None else int(scores['em']))
            assert original['task_F1'] == scores['f1'] and original['format'] is scores['format']
            assert cell['original_text_sha256'] == hashlib.sha256(raw['text'].encode('utf-8')).hexdigest()
            diagnostic = 'schema_valid' if scores['format'] else reason_mapping[scores['reason']]
            if scores['em'] is None: overlap = 'unavailable'
            elif scores['em'] is True: overlap = 'EM_match'
            elif scores['f1'] > 0: overlap = 'non_EM_positive_token_overlap'
            else: overlap = 'non_EM_zero_token_overlap'
            assert cell['raw_format_diagnostic'] == diagnostic and cell['raw_task_overlap_diagnostic'] == overlap
            assert cell['raw_score_reason'] == scores['reason']
        else:
            assert raw is None and all(cell[k] is None for k in ('original_text_sha256', 'raw_score_reason', 'raw_format_diagnostic', 'raw_task_overlap_diagnostic'))
        reclassified.append(cell)
    expected_conditions = {}
    for name in names:
        subset = [r for r in reclassified if r['condition_id'] == name]
        finished = [r for r in subset if r['completed']]
        counts = Counter(label(normalized[r['case_id'], name]) for r in subset)
        expected = dict(planned=48, categories={k: counts[k] for k in categories},
                        generated=sum(r['execution_state'] == 'ok' for r in subset), completed=len(finished),
                        raw_score_reasons=dict(Counter(r['raw_score_reason'] for r in subset if r['execution_state'] == 'ok')),
                        completed_format_failures=dict(Counter(r['raw_format_diagnostic'] for r in finished if r['raw_format'] is False)),
                        completed_task_overlap=dict(Counter(r['raw_task_overlap_diagnostic'] for r in finished)))
        assert report['conditions'][name] == expected and sum(counts.values()) == 48
        expected_conditions[name] = expected
    for name in names[1:]:
        pairs = [(label(normalized[cid, 'full']), label(normalized[cid, name])) for cid in ids]
        expected_flow = [dict(full_category=a, method_category=b, count=count) for (a, b), count in sorted(Counter(pairs).items())]
        loss = Counter(b for a, b in pairs if a == 'joint_success')
        assert report['paired'][name]['flow_matrix'] == expected_flow
        assert report['paired'][name]['Full_joint_followup'] == {k: loss[k] for k in categories}
        assert sum(loss.values()) == report['paired'][name]['Full_joint_groups'] == 31
        assert sum(x['count'] for x in expected_flow) == 48
    examples = read(out / 'server_only_examples.json'); index = read(out / 'example_index.json'); wanted = []
    for name in names:
        for category in categories:
            wanted += sorted([r for r in reclassified if r['condition_id'] == name and r['category'] == category], key=lambda r: r['case_id'])[:2]
    assert len(examples) == len(index) == len(wanted) <= 54
    for example, pointer, cell in zip(examples, index, wanted):
        assert example['annotation'] == cell
        src = source[cell['case_id']]; raw = scored.get((cell['case_id'], cell['condition_id']))
        assert example['question'] == src['question'] and example['gold_answers'] == src['answers']
        assert example['model_text'] == (raw['text'] if raw else None)
        assert pointer == dict(case_id=cell['case_id'], condition_id=cell['condition_id'], category=cell['category'], text_sha256=cell['original_text_sha256'])
    assert report['classification_is_exploratory'] is True and report['scoring_changed'] is False and report['primary_estimands_or_CI_changed'] is False
    assert not any(m.split('.')[0] in ('torch', 'transformers', 'tokenizers', 'analyze_squad48_failures', 'answer_format_task', 'reliability_group_statistics') for m in sys.modules)
    verification = dict(passed=True, method='Independent 2x2/state-table reclassification,138-text scoring,144 complete grid,all48 flows/31Full-joint followups and deterministic examples;no analyzer/model imports',
                        existing_answers_rechecked=138, cells=144, original_groups=48, synthetic_cases=9, examples=len(examples),
                        new_model_answers=0, tokenizer_encodes=0, GPU_queries=0, weight_bytes_read=0, network_requests=0,
                        source_inputs=len(cfg['inputs']), original_manifest_sha256=sha(out / 'manifest.json'),
                        parent_manifest_sha256=sha(parent / 'manifest.json'), pid=os.getpid(), elapsed_seconds=time.monotonic() - start)
    assert not (out / 'independent_verification.json').exists()
    signal.alarm(0); (out / 'independent_verification.json').write_text(json.dumps(verification, sort_keys=True, indent=2) + '\n')
    print(json.dumps(verification), flush=True)


if __name__ == '__main__': main()
