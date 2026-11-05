"""Bounded server CPU validation of archived-result adapters and pairing.

Pinned JSON input only, no model/tokenizer/tensor/scorer execution. Historical
artifact SHA references are carried as references, not rerun or promoted.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

from reliability_report import PROFILES, TRANSITIONS, normalize, report, require
from reliability_report_fixtures import validate_fixture

PROPOSAL_SHA = '0e98ebcd56a5f69a7af60161f73a296f043325d59864d83f05da36af4999bc33'
SOURCES = ('reliability_report.py', 'reliability_report_fixtures.py', 'replay_reliability_report.py')


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')


class Inputs:
    def __init__(self, root, config):
        self.root = root
        self.bounds = config['bounds']
        self.files = {}
        self.data = {}
        self.bytes = 0
        self.lines = 0
        for cohort in config['cohorts']:
            for entry in cohort['inputs']:
                name = entry['path']
                if name in self.files:
                    require(self.files[name]['sha256'] == entry['sha256'], 'Conflicting input pins')
                    continue
                p = root/name
                require(not p.is_symlink() and p.resolve().is_relative_to(root/'results'), 'Unsafe input path')
                require(p.suffix in ('.json','.jsonl'), 'Only JSON inputs supported')
                size = p.stat().st_size
                require(len(self.files)+1 <= self.bounds['max_input_files'], 'Input file bound')
                require(self.bytes+size <= self.bounds['max_input_bytes'], 'Input byte bound')
                raw = p.read_bytes()
                require(sha_bytes(raw) == entry['sha256'], 'Input SHA mismatch: '+name)
                self.bytes += len(raw)
                if p.suffix == '.jsonl':
                    chunks = raw.splitlines()
                    self.lines += len(chunks)
                    require(self.lines <= self.bounds['max_jsonl_rows'], 'JSONL row bound')
                    data = [json.loads(x) for x in chunks]
                else:
                    data = json.loads(raw)
                self.files[name] = dict(sha256=entry['sha256'], bytes=len(raw))
                self.data[name] = data

    def unchanged(self):
        return {n:sha_bytes((self.root/n).read_bytes()) == meta['sha256'] for n,meta in self.files.items()}


def runtime_identity(manifest):
    return {k:manifest[k] for k in ['versions','tokenizer_sha256','actual_generation_config']} | {
        'model':manifest['args']['model']}


def adapt(cohort, inputs):
    root = cohort['source_run']
    selection = cohort['baseline_selection']
    baseline = [(i+1,r) for i,r in enumerate(inputs.data[selection['path']])
                if all(r.get(k) == v for k,v in selection['filter'].items())]
    require(len(baseline) == selection['expected_rows'] == cohort['n_cases'], 'Baseline count mismatch')
    keys = [row['source_key'] for _,row in baseline]
    require(len(set(keys)) == len(keys), 'Duplicate baseline case')
    main = inputs.data[root+'/generations.jsonl']
    names = list(cohort['expected']['methods'])
    # These are declared legacy condition identities, never inferred from outputs.
    protected = {'adapted_snapkv_shared_anchors':False,
        'uniform_random_shared_anchors':False,
        'adapted_snapkv_shared_anchors_header_pinned':True,
        'uniform_random_shared_anchors_header_pinned':True}
    require(set(names) == set(protected), 'Unknown legacy condition mapping')
    specs = [dict(condition_id='full', protection=False)] + [
        dict(condition_id=n, budget_group='same_legacy_prefix_bytes', protection=protected[n]) for n in names]
    baseline_manifest_name = selection['path'].removesuffix('/generations.jsonl')+'/manifest.json'
    source_manifest = inputs.data[root+'/manifest.json']
    baseline_manifest = inputs.data[baseline_manifest_name]
    require(source_manifest['status'] == baseline_manifest['status'] == 'complete', 'Incomplete source run')
    require(runtime_identity(source_manifest) == runtime_identity(baseline_manifest), 'Runtime/decode identity mismatch')
    if 'copy_path' in selection:
        copy = inputs.data[selection['copy_path']]
        require(len(copy) == len(baseline), 'Baseline copy count mismatch')
        copies = {r['source_key']:r for r in copy}
        require(len(copies) == len(copy) and set(copies) == set(keys), 'Baseline copy identities mismatch')
        for _,row in baseline:
            require(all(copies[row['source_key']][k] == row[k]
                for k in selection['baseline_copy_must_match_fields']), 'Baseline copy content mismatch')
    records = [normalize(row, cohort['cohort_id'], 'full',
        dict(path=selection['path'], line=line, sha256=inputs.files[selection['path']]['sha256']))
        for line,row in baseline]
    for i,row in enumerate(main):
        if row.get('method') == 'full' and selection['path'] == root+'/generations.jsonl':
            continue  # Already consumed exactly once through baseline selection.
        require(row.get('method') in names, 'Unexpected method row')
        records.append(normalize(row, cohort['cohort_id'], row['method'],
            dict(path=root+'/generations.jsonl', line=i+1,
                 sha256=inputs.files[root+'/generations.jsonl']['sha256'])))
    require(len(records) == len(keys)*len(specs), 'Archived schedule incomplete')
    evidence = dict(source_run=root, manifest_sha256=inputs.files[root+'/manifest.json']['sha256'],
        runtime_identity=runtime_identity(source_manifest), scientific_role=cohort['scientific_role'],
        archived_gate_flags={k:source_manifest[k] for k in
            ['engineering_gate_passed','full_support_gate_passed'] if k in source_manifest},
        referenced_checks={n:h for n,h in source_manifest.get('artifact_sha256',{}).items()
            if n in ['engineering_checks.json','full_engineering_checks.json',
                     'compressed_engineering_checks.json','full_support_gate.json']},
        referenced_check_scope='Historical artifact SHA references only; not reexecuted or reread by this report')
    return keys, specs, records, evidence


def validate_counts(cohort, reports, inputs):
    expected = cohort['expected']
    old = inputs.data[cohort['source_run']+'/summary.json']
    for generated in reports:
        full = generated['methods']['full']['metrics']
        require(full['task']['pass_count'] == expected['full']['task_correct'] and
                full['constraint']['pass_count'] == expected['full']['constraint_pass'], 'Full expected values mismatch')
        for name, target in expected['methods'].items():
            rec = generated['methods'][name]
            t, c = rec['metrics']['task'], rec['metrics']['constraint']
            require(t['pass_count'] == target['task_correct'] and c['pass_count'] == target['constraint_pass'], 'Metric count mismatch')
            require([t['transitions'][x] for x in TRANSITIONS] == target['transitions'], 'Transition mismatch')
            require(t['unassessed_full_pass_count'] == 0 and t['paired_count'] == cohort['n_cases'], 'Unexpected missing pairs')
            archived = old['methods'][name]
            require(t['pass_count'] == archived['exact_correct'] and
                    c['pass_count'] == archived['label_format'], 'Archived summary metric mismatch')
            require(all(t['transitions'][x] == archived['full_to_compressed'][x] for x in TRANSITIONS), 'Archived summary transitions mismatch')
        if 'full' in old['methods']:
            old_full = old['methods']['full']
            require(full['task']['pass_count'] == old_full['exact_correct'] and
                    full['constraint']['pass_count'] == old_full['label_format'], 'Archived Full summary mismatch')
        else:
            require(full['task']['pass_count'] == old['baseline']['exact_correct'] and
                    full['constraint']['pass_count'] == old['baseline']['label_format'], 'Archived Full baseline mismatch')
    return dict(frozen_expected_counts_match=True, archived_summary_counts_match=True,
        actual_full_correct=reports[0]['methods']['full']['metrics']['task']['pass_count'],
        historical_scores_recomputed=False, rows_aggregated_independently=True)


def markdown(cohorts):
    lines = ['# Archived KV result report', '',
        'Two previously used cohorts remain separate. This is software regression, not independent confirmation.', '',
        'Archived scores were aggregated, not redecoded or rescored. Peak memory and request latency are unknown.', '']
    for cohort in cohorts:
        lines += ['## '+cohort['cohort_id'], '', 'Role: '+cohort['scientific_role'], '']
        for profile, rec in cohort['profiles'].items():
            lines += ['### '+profile, '',
                '| Condition | Task pass/evaluated | Constraint pass/evaluated | Task C2W / W2C | Eligible Full-pass pairs | Unassessed Full pass |',
                '| --- | --- | --- | --- | --- | --- |']
            for name, method in rec['methods'].items():
                t,c = method['metrics']['task'],method['metrics']['constraint']
                change = '-' if name == 'full' else str(t['transitions']['C2W'])+' / '+str(t['transitions']['W2C'])
                den = '-' if name == 'full' else str(t['eligible_full_pass_pair_count'])
                unseen = '-' if name == 'full' else str(t['unassessed_full_pass_count'])
                lines.append(f"| {name} | {t['pass_count']}/{t['evaluated_count']} | {c['pass_count']}/{c['evaluated_count']} | {change} | {den} | {unseen} |")
            lines += ['', 'Execution-state and unavailable-pair counts are retained in report.json.', '']
    return '\n'.join(lines)+'\n'


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--run-dir', required=True)
    parser.add_argument('--correction')
    args = parser.parse_args(); root = Path(__file__).resolve().parents[1]
    out = Path(args.run_dir).resolve()
    require(out.parent == root/'results', 'Output must be a new direct results child')
    out.mkdir(exist_ok=False)
    start = time.monotonic(); inputs = None
    state = dict(status='running', pid=os.getpid(), stage='prepare', main_outputs=0,
        engineering_answers=0, model_loaded=False, gpu_queried=False, author_code_executed=False,
        cohorts_completed=0, fixtures_passed=0)
    def timeout(*_):
        raise TimeoutError('60 second CPU report bound')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(60)
    try:
        proposal = root/'configs/reliability-report-replay-proposal-v1.json'
        raw = proposal.read_bytes(); require(sha_bytes(raw) == PROPOSAL_SHA, 'Proposal SHA mismatch')
        config = json.loads(raw)
        require(not config['execution_enabled'] and not config['runner_implemented'], 'Frozen proposal changed')
        (out/'proposal_snapshot.json').write_bytes(raw)
        correction_hash = None
        if args.correction:
            path = (root/args.correction).resolve()
            require(path.parent == root/'configs', 'Invalid correction path')
            correction_raw = path.read_bytes(); correction = json.loads(correction_raw)
            require(correction['base_proposal_sha256'] == PROPOSAL_SHA, 'Correction base mismatch')
            prior = (root/correction['prior_run']).resolve()
            require(prior.parent == root/'results' and prior != out, 'Invalid prior run')
            require(sha_bytes((prior/'manifest.json').read_bytes()) == correction['prior_manifest_sha256'], 'Prior manifest changed')
            require(sha_bytes((prior/'post_review.json').read_bytes()) == correction['prior_post_review_sha256'], 'Prior review changed')
            (out/'correction_snapshot.json').write_bytes(correction_raw)
            correction_hash = sha_bytes(correction_raw)
        source_hashes = {}
        allowed = {'argparse','ast','hashlib','json','os','pathlib','signal','sys','time','traceback',
                   'collections','copy','reliability_report','reliability_report_fixtures'}
        for name in SOURCES:
            raw = (root/'scripts'/name).read_bytes()
            tree = ast.parse(raw)
            for node in ast.walk(tree):
                mods = [x.name.split('.')[0] for x in node.names] if isinstance(node, ast.Import) else (
                    [node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) else [])
                require(set(mods) <= allowed, 'Unexpected module import')
            source_hashes[name] = sha_bytes(raw)
            (out/('source_'+name)).write_bytes(raw)
        save(out/'execution_snapshot.json', dict(proposal_sha256=PROPOSAL_SHA,
            execution_enabled=True, runner_implemented=True, main_execution_enabled=False,
            bounds=config['bounds'], source_hashes=source_hashes,
            correction_sha256=correction_hash,
            python_version=sys.version, source_import_allowlist=sorted(allowed)))
        state['stage'] = 'input_verification'; save(out/'summary.json', state)
        inputs = Inputs(root, config)
        save(out/'input_manifest.json', dict(files=inputs.files, input_bytes=inputs.bytes,
            jsonl_rows=inputs.lines, all_input_hashes_match=True))
        cohorts = []
        with (out/'normalized_records.jsonl').open('x', encoding='utf-8') as stream:
            for cohort in config['cohorts']:
                keys, specs, rows, evidence = adapt(cohort, inputs)
                generated = [report(cohort['cohort_id'], keys, specs, rows, p) for p in PROFILES]
                counts = validate_counts(cohort, generated, inputs)
                for row in rows:
                    stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n')
                for result in generated:
                    result.pop('cells')
                cohorts.append(dict(cohort_id=cohort['cohort_id'], scientific_role=cohort['scientific_role'],
                    evidence=evidence, count_validation=counts,
                    conditions=specs, profiles={r['profile']:r for r in generated}))
                state['cohorts_completed'] += 1
                save(out/'summary.json', state)
        save(out/'report.json', dict(schema_version='0.1', cohorts=cohorts,
            role='Software regression on archived results, no independent scientific confirmation'))
        (out/'report.md').write_text(markdown(cohorts), encoding='utf-8')
        state['stage'] = 'software_boundary_fixtures'; save(out/'summary.json', state)
        require(len(config['planned_fixtures']) == config['bounds']['max_synthetic_fixtures'] == 12, 'Fixture bound')
        with (out/'software_fixtures.jsonl').open('x', encoding='utf-8') as stream:
            for index, description in enumerate(config['planned_fixtures']):
                result = validate_fixture(index, description)
                stream.write(json.dumps(result, allow_nan=False)+'\n'); stream.flush()
                state['fixtures_passed'] += 1; save(out/'summary.json', state)
        unchanged = inputs.unchanged(); require(all(unchanged.values()), 'Source artifact changed during report')
        require(not any(x.split('.')[0] in {'torch','transformers','vllm'} for x in sys.modules), 'Forbidden model library loaded')
        save(out/'validation.json', dict(status='pass', all_pinned_inputs_unchanged=unchanged,
            model_libraries_loaded=False, text_rescored=False, tensor_maps_revalidated=False,
            historical_checks_reference_only=True, synthetic_software_fixtures=12,
            independent_confirmation=False, new_GPU_queue=False))
        state.update(status='complete', stage='complete', input_files=len(inputs.files),
            input_bytes=inputs.bytes, jsonl_rows=inputs.lines,
            normalized_records=sum(c['profiles'][PROFILES[0]]['case_count']*len(c['conditions']) for c in cohorts),
            model_libraries_loaded=False, report_profiles=list(PROFILES))
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
        (out/'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        signal.alarm(0)
        state['elapsed_seconds'] = time.monotonic()-start
        save(out/'summary.json', state)
        save(out/'manifest.json', {p.name:sha_bytes(p.read_bytes()) for p in out.iterdir() if p.is_file()})
        print(json.dumps(state, indent=2), flush=True)
    return 0 if state['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
