"""Exploratory, exhaustive taxonomy of immutable Qwen48 outputs; stdlib only."""
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
import traceback
from reliability_group_statistics import validate

NAMES = ('full', 'adapted_snapkv', 'uniform_random')
CATEGORIES = ('joint_success', 'task_only', 'format_only', 'neither', 'task_unavailable',
              'truncated', 'budget_infeasible', 'execution_error', 'not_run')
FORMAT_TAGS = {'whole_plain_text': 'unstructured_plain_text', 'json_string': 'JSON_string_wrong_root',
               'json_scalar_as_plain_text': 'JSON_scalar_wrong_root', 'unsupported_json_root': 'JSON_array_wrong_root',
               'no_string_answer': 'object_without_string_answer', 'object_answer': 'object_extra_keys_or_empty_answer',
               'structured_parse_failure': 'malformed_structured_output', 'bom': 'BOM_rejected',
               'duplicate_key': 'duplicate_key', 'nonfinite_constant': 'nonfinite_constant', 'invalid_unicode': 'invalid_unicode'}


def check(test, message):
    if not test:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False, indent=2) + '\n')


def classify(row):
    state = row['execution_state']
    if state == 'infeasible_budget': return 'budget_infeasible'
    if state == 'error': return 'execution_error'
    if state in ('not_run', 'protocol_stopped'): return 'not_run'
    check(state == 'ok', 'unknown_state')
    if row['truncated']: return 'truncated'
    if row['task_EM'] is None: return 'task_unavailable'
    if row['task_EM'] == 1: return 'joint_success' if row['format'] else 'task_only'
    return 'format_only' if row['format'] else 'neither'


def software_cases():
    tests = []
    rows = [dict(execution_state='ok', truncated=False, task_EM=em, format=fmt) for em, fmt in [(1, True), (1, False), (0, True), (0, False), (None, False)]]
    rows += [dict(execution_state='ok', truncated=True, task_EM=1, format=True),
             dict(execution_state='infeasible_budget', truncated=None, task_EM=None, format=None),
             dict(execution_state='error', truncated=None, task_EM=None, format=None),
             dict(execution_state='protocol_stopped', truncated=None, task_EM=None, format=None)]
    for i, (row, want) in enumerate(zip(rows, CATEGORIES)):
        check(classify(row) == want, 'taxonomy_fixture:' + str(i))
        tests.append(dict(id='E%02d' % (i + 1), input=row, expected=want, actual=classify(row), passed=True))
    return tests


def analyze(rows, scored, ids):
    by = {(r['case_id'], r['condition_id']): r for r in rows}
    raw = {(r['case_id'], r['condition_id']): r for r in scored}
    check(len(rows) == len(by) == 144 and len(scored) == len(raw) == 138, 'fixed_144_138')
    check(set(by) == {(cid, name) for cid in ids for name in NAMES}, 'fixed_plan_grid')
    annotated = []
    for cid in ids:
        for name in NAMES:
            row = by[cid, name]; item = raw.get((cid, name))
            if row['execution_state'] == 'ok':
                check(item is not None and item['normalized'] == row and item['truncated'] is row['truncated'], 'scored_binding')
                scores = item['scores']
                check(row['task_EM'] == (None if scores['em'] is None else int(scores['em'])) and row['task_F1'] == scores['f1'] and row['format'] is scores['format'], 'scored_metric_binding')
                tag = 'schema_valid' if scores['format'] else FORMAT_TAGS.get(scores['reason'])
                check(tag is not None, 'undeclared_format_reason:' + scores['reason'])
                overlap = 'unavailable' if scores['em'] is None else 'EM_match' if scores['em'] else 'non_EM_positive_token_overlap' if scores['f1'] > 0 else 'non_EM_zero_token_overlap'
            else:
                check(item is None, 'raw_for_unexecuted_cell'); tag = overlap = None
            annotated.append(dict(case_id=cid, condition_id=name, context_group_id=row['context_group_id'],
                category=classify(row), execution_state=row['execution_state'], budget_state=row['budget_state'],
                truncated=row['truncated'], raw_EM=row['task_EM'], raw_F1=row['task_F1'], raw_format=row['format'],
                raw_format_diagnostic=tag, raw_task_overlap_diagnostic=overlap,
                completed=row['execution_state'] == 'ok' and not row['truncated'],
                raw_score_reason=item['scores']['reason'] if item else None,
                input_digest=row['input_digest'], gold_digest=row['gold_digest'], comparison_digest=row['comparison_digest'],
                original_text_sha256=sha(item['text'].encode('utf-8')) if item else None,
                baseline_category=classify(by[cid, 'full'])))
    conditions = {}
    for name in NAMES:
        subset = [x for x in annotated if x['condition_id'] == name]
        categories = Counter(x['category'] for x in subset)
        completed = [x for x in subset if x['completed']]
        conditions[name] = dict(planned=48, categories={k: categories[k] for k in CATEGORIES},
            generated=sum(x['execution_state'] == 'ok' for x in subset), completed=len(completed),
            raw_score_reasons=dict(sorted(Counter(x['raw_score_reason'] for x in subset if x['execution_state'] == 'ok').items())),
            completed_format_failures=dict(sorted(Counter(x['raw_format_diagnostic'] for x in completed if not x['raw_format']).items())),
            completed_task_overlap=dict(sorted(Counter(x['raw_task_overlap_diagnostic'] for x in completed).items())))
        check(sum(categories.values()) == 48, 'complete_partition')
    paired = {}
    for name in NAMES[1:]:
        subset = [x for x in annotated if x['condition_id'] == name]
        flows = Counter((x['baseline_category'], x['category']) for x in subset)
        loss = Counter(x['category'] for x in subset if x['baseline_category'] == 'joint_success')
        paired[name] = dict(groups=48, flow_matrix=[dict(full_category=a, method_category=b, count=count) for (a, b), count in sorted(flows.items())],
            Full_joint_groups=31, Full_joint_followup={k: loss[k] for k in CATEGORIES},
            descriptive_subgroup_not_new_confirmatory_test=True)
        check(sum(loss.values()) == 31 and sum(flows.values()) == 48, 'paired_denominators')
    report = dict(schema='squad48_posthoc_error_taxonomy_v1', classification_is_exploratory=True,
                  scoring_changed=False, primary_estimands_or_CI_changed=False, independent_groups=48,
                  planned_cells=144, existing_generated_answers=138, new_model_answers=0,
                  conditions=conditions, paired=paired, categories=list(CATEGORIES),
                  ordering='execution/budget -> truncation -> task N/A -> taskEM x format',
                  EM_mismatch_is_not_human_semantic_error_annotation=True,
                  token_overlap_is_not_semantic_judgment=True)
    return annotated, report


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--execute', action='store_true'); ap.add_argument('--proposal-sha256', required=True); args = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    check(args.execute and str(root) == '/home/user/jhk/project/Directional Exploration/kv-pruning', 'server_CPU_only')
    cfgraw = (root / 'configs/squad48-error-taxonomy-v1.json').read_bytes()
    check(sha(cfgraw) == args.proposal_sha256, 'proposal_pin'); cfg = json.loads(cfgraw)
    out = root / cfg['run']; check(out.resolve().parent == (root / 'results').resolve(), 'output_boundary'); out.mkdir(exist_ok=False)
    start = time.monotonic(); state = dict(status='running', pid=os.getpid(), main_outputs=0, engineering_outputs=0, tokenizer_encodes=0, model_loads=0, GPU_queries=0, weight_bytes_read=0, network_requests=0)
    guard = dict(forbidden_imports=0, forbidden_file_attempts=0, network_attempts=0, subprocess_attempts=0)
    signal.signal(signal.SIGALRM, lambda *unused: (_ for _ in ()).throw(TimeoutError('CPU60_second_cap')))
    signal.alarm(60)
    try:
        save(out / 'summary.json', state); (out / 'proposal_snapshot.json').write_bytes(cfgraw)
        check(os.environ.get('KV_TAXONOMY48_WATCHDOG') == 'registered_90_seconds' and cfg['execution_enabled'] is True, 'registered_CPU_protocol')
        for rel, pin in {**cfg['inputs'], **cfg['source_sha256']}.items():
            data = (root / rel).read_bytes(); check(sha(data) == pin, 'pin:' + rel)
            if rel.startswith('scripts/') or rel == cfg['protocol']:
                (out / ('source_' + Path(rel).name)).write_bytes(data)
        save(out / 'input_manifest.json', dict(files=cfg['inputs'], bytes=sum((root / p).stat().st_size for p in cfg['inputs'])))
        def audit(event, values):
            if event == 'import' and values[0].split('.')[0] in ('torch', 'transformers', 'tokenizers', 'vllm', 'tensorflow', 'jax'):
                guard['forbidden_imports'] += 1; raise RuntimeError('model_tokenizer_import_forbidden')
            if event.startswith('socket.'):
                guard['network_attempts'] += 1; raise RuntimeError('socket_forbidden')
            if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork', 'os.forkpty'):
                guard['subprocess_attempts'] += 1; raise RuntimeError('subprocess_forbidden')
            if event == 'open' and isinstance(values[0], (str, bytes)):
                p = Path(os.fsdecode(values[0])).resolve(); mode = values[1]
                writing = isinstance(mode, str) and any(x in mode for x in 'wax+') or values[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
                if p.is_relative_to(root / 'models') or p.suffix in ('.safetensors', '.bin', '.pt', '.pth') or writing and not p.is_relative_to(out):
                    guard['forbidden_file_attempts'] += 1; raise RuntimeError('file_scope_forbidden')
        sys.addaudithook(audit)
        check(not any(m.split('.')[0] in ('torch', 'transformers', 'tokenizers') for m in sys.modules), 'stdlib_only')
        read = lambda rel: json.loads((root / rel).read_text())
        parent = root / cfg['parent_run']
        for n, pin in read(cfg['parent_run'] + '/manifest.json').items(): check(sha((parent / n).read_bytes()) == pin, 'parent_original:' + n)
        for n, pin in read(cfg['parent_run'] + '/derived_manifest.json').items(): check(sha((parent / n).read_bytes()) == pin, 'parent_derived:' + n)
        rows = [json.loads(s) for s in (root / cfg['normalized']).read_text().splitlines()]
        scored = [json.loads(s) for s in (root / cfg['scored']).read_text().splitlines()]
        validate(read(cfg['statistics_plan']), rows)
        cases = [json.loads(s) for s in (root / cfg['selected']).read_text().splitlines()]; ids = [c['case_id'] for c in cases]
        check(len(ids) == len(set(ids)) == 48 and len({c['context_group_id'] for c in cases}) == 48, 'original48_identity')
        tests = software_cases(); save(out / 'software_acceptance.json', tests)
        annotated, report = analyze(rows, scored, ids)
        (out / 'annotated_cells.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=True, allow_nan=False) + '\n' for x in annotated))
        save(out / 'taxonomy_report.json', report)
        # Deterministic illustrations: first2 IDs within every condition/category.
        examples = []
        by_raw = {(x['case_id'], x['condition_id']): x for x in scored}; by_source = {c['case_id']: c for c in cases}
        for name in NAMES:
            for category in CATEGORIES:
                selected = sorted([x for x in annotated if x['condition_id'] == name and x['category'] == category], key=lambda x: x['case_id'])[:2]
                for item in selected:
                    raw = by_raw.get((item['case_id'], name)); original = by_source[item['case_id']]
                    examples.append(dict(annotation=item, question=original['question'], gold_answers=original['answers'],
                        model_text=raw['text'] if raw else None,
                        selection='posthoc illustration,lexicographic first2 within condition/category;not a new sample or performance estimate'))
        check(len(examples) <= 54, 'example_cap'); save(out / 'server_only_examples.json', examples)
        save(out / 'example_index.json', [dict(case_id=e['annotation']['case_id'], condition_id=e['annotation']['condition_id'], category=e['annotation']['category'], text_sha256=e['annotation']['original_text_sha256']) for e in examples])
        save(out / 'execution_snapshot.json', dict(proposal_sha256=args.proposal_sha256, argv=sys.argv, python=sys.version,
             source_sha256=cfg['source_sha256'], primary_study_unchanged=True, exploratory_taxonomy=True,
             no_new_model_answers=True, examples_server_only=True))
        check(not any(guard.values()), 'guard_violation')
        state.update(status='complete', classified_cells=144, existing_answers=138, software_cases=9, examples=len(examples))
    except BaseException as exc:
        state.update(status='failed', error=repr(exc)); (out / 'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0); state['elapsed_seconds'] = time.monotonic() - start
        save(out / 'CPU_guard_observations.json', guard); save(out / 'summary.json', state)
        files = [p for p in out.iterdir() if p.is_file()]
        check(len(files) + 1 <= 32 and sum(p.stat().st_size for p in files) <= 16777216, 'archive_bounds')
        save(out / 'manifest.json', {p.name: sha(p.read_bytes()) for p in files})
        print(json.dumps(state), flush=True)
    return 0 if state['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
