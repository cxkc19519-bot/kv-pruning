"""Registered CPU-only acceptance with synthetic fixtures, not new model data."""
import sys
sys.dont_write_bytecode = True
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(ok, message):
    if not ok:
        raise ValueError(message)


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def fixture(full=(1, 0), snap=(0, 1), random=(0, 0)):
    cases = [dict(cohort_id='software_only', case_id='case' + str(i), context_group_id='group' + str(i),
                  role='software_fixture', input_digest=sha(('input' + str(i)).encode()),
                  gold_digest=sha(('gold' + str(i)).encode()), comparison_digest=sha(('runtime' + str(i)).encode())) for i in range(len(full))]
    plan = dict(schema='kv_group_plan_v1', cohort_id='software_only', role='software_fixture',
                conditions=['full', 'adapted_snapkv', 'uniform_random'], cases=cases)
    rows = []
    for name, values in [('full', full), ('adapted_snapkv', snap), ('uniform_random', random)]:
        for case, value in zip(cases, values):
            rows.append(dict(case, schema='kv_group_outcome_v1', condition_id=name, execution_state='ok',
                             budget_state='ok', task_EM=value, task_F1=float(value), format=True, truncated=False))
    return dict(plan=plan, records=rows, phase='complete', full_support=True)


def changed(base, name, **fields):
    item = deepcopy(base)
    next(r for r in item['records'] if r['condition_id'] == name).update(fields)
    return item


def build_fixtures():
    base = fixture()
    # All intentional invalid values are represented as JSON-safe mutation specs.
    specs = [dict(id='G01', action='summary', input=base),
             dict(id='G02', action='exact_bootstrap', vectors={'adapted_snapkv': [-1, 1]},
                  groups=['group0', 'group1'], draws=[[0, 0], [0, 1], [1, 0], [1, 1]]),
             dict(id='G03', action='summary', input=fixture(snap=(1, 0), random=(1, 0))),
             dict(id='G04', action='summary', input=fixture(full=(0, 0), snap=(1, 1), random=(1, 1))),
             dict(id='G05', action='summary', input=fixture(full=(1, 1), snap=(0, 0), random=(0, 0)))]
    blocked = changed(base, 'adapted_snapkv', execution_state='infeasible_budget', budget_state='infeasible_budget',
                      task_EM=None, task_F1=None, format=None, truncated=None, reason='anchor_capacity')
    specs += [dict(id='G06', action='summary', input=blocked),
              dict(id='G07', action='summary', input=changed(fixture(snap=(1, 1)), 'adapted_snapkv', truncated=True)),
              dict(id='G08', action='summary', input=changed(base, 'adapted_snapkv', task_EM=None, task_F1=None,
                   task_EM_reason='candidate_NA', task_F1_reason='candidate_NA')),
              dict(id='G09', action='reject', input=base, mutations=['duplicate_cell'], expected=['duplicate_cell']),
              dict(id='G10', action='reject', input=base, mutations=['missing_cell'], expected=['missing_planned_cell']),
              dict(id='G11', action='reject', input=base, mutations=['input_digest', 'gold_digest', 'comparison_digest'], expected=['pair_identity_mismatch'] * 3),
              dict(id='G12', action='reject', input=base, mutations=['duplicate_group', 'cross_role', 'excluded_group', 'duplicate_case'],
                   expected=['duplicate_or_cross_role_group', 'case_cohort_or_role', 'duplicate_or_cross_role_group', 'duplicate_case']),
              dict(id='G13', action='reject', input=base, mutations=['bool_EM', 'bool_F1', 'nan_F1', 'inf_F1'], expected=['metric_number'] * 4),
              dict(id='G14', action='reproducibility', input=base)]
    stopped = changed(base, 'adapted_snapkv', execution_state='protocol_stopped', task_EM=None, task_F1=None,
                      truncated=None, format=None, reason='Full_support_failed')
    pending = changed(base, 'adapted_snapkv', execution_state='not_run', task_EM=None, task_F1=None,
                      truncated=None, format=None, reason='technical_phase_incomplete')
    specs += [dict(id='G15', action='incomplete', inputs=[dict(base, full_support=False), dict(stopped, phase='protocol_stopped'), pending]),
              dict(id='G16', action='summary', input=fixture(full=(0, 0), snap=(0, 1), random=(1, 0))),
              dict(id='G17', action='quantiles', values=[0, 1], probabilities=[0, 1, .25]),
              dict(id='G18', action='native_pending_only')]
    return specs


def mutate(spec, mutation):
    data = deepcopy(spec)
    row = next(r for r in data['records'] if r['condition_id'] == 'adapted_snapkv')
    cases = data['plan']['cases']
    if mutation == 'duplicate_cell':
        data['records'].append(deepcopy(row))
    elif mutation == 'missing_cell':
        data['records'].remove(row)
    elif mutation in ('input_digest', 'gold_digest', 'comparison_digest'):
        row[mutation] = 'f' * 64
    elif mutation == 'duplicate_group':
        cases[1]['context_group_id'] = cases[0]['context_group_id']
    elif mutation == 'cross_role':
        cases[1]['role'] = 'DEV'
    elif mutation == 'excluded_group':
        data['plan']['excluded_group_ids'] = [cases[0]['context_group_id']]
    elif mutation == 'duplicate_case':
        cases[1]['case_id'] = cases[0]['case_id']
    elif mutation == 'bool_EM':
        row['task_EM'] = True
    elif mutation == 'bool_F1':
        row['task_F1'] = False
    elif mutation == 'nan_F1':
        row['task_F1'] = float('nan')
    elif mutation == 'inf_F1':
        row['task_F1'] = float('inf')
    else:
        raise ValueError('unknown_mutation')
    return data


def run_fixture(module, spec, native_cells):
    action = spec['action']
    if action == 'summary':
        return module.summarize(**spec['input'])
    if action == 'exact_bootstrap':
        return module.paired_bootstrap(spec['vectors'], spec['groups'], resamples=4, draws=spec['draws'])
    if action == 'reject':
        errors = []
        for mutation, want in zip(spec['mutations'], spec['expected']):
            try:
                module.summarize(**mutate(spec['input'], mutation))
            except module.StatisticsContractError as error:
                check(str(error) == want, spec['id'] + ':' + str(error))
                errors.append(dict(mutation=mutation, error=str(error)))
            else:
                raise ValueError(spec['id'] + ':invalid_input_accepted')
        return errors
    if action == 'reproducibility':
        permuted = deepcopy(spec['input'])
        permuted['plan']['conditions'].reverse()
        permuted['plan']['cases'].reverse()
        permuted['records'].reverse()
        outputs = [module.summarize(**spec['input']), module.summarize(**spec['input']), module.summarize(**permuted)]
        check(outputs[0] == outputs[1] == outputs[2], 'seed_or_permutation_reproducibility')
        return outputs
    if action == 'incomplete':
        outputs = [module.summarize(**item) for item in spec['inputs']]
        check(all(o['comparisons'] is None and o['bootstrap'] is None for o in outputs), 'incomplete_CI')
        return outputs
    if action == 'quantiles':
        return [module.quantile_type7(spec['values'], p) for p in spec['probabilities']]
    if action == 'native_pending_only':
        plan, rows = module.pending_native_plan(native_cells)
        output = module.summarize(plan, rows, phase='pending', full_support=None)
        check(output['groups'] == 48 and output['planned_cells'] == 144 and output['comparisons'] is None and output['bootstrap'] is None, 'actual48_must_not_be_scored')
        return output
    raise ValueError('unknown_action')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--registration-sha256', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    check(args.execute and str(root) == '/home/user/jhk/project/Directional Exploration/kv-pruning', 'registered_server_only')
    registration_path = root / 'configs/group-statistics-execution-v1.json'
    registration_raw = registration_path.read_bytes()
    check(sha(registration_raw) == args.registration_sha256, 'registration_pin')
    reg = json.loads(registration_raw)
    proposal_raw = (root / reg['proposal']).read_bytes()
    check(sha(proposal_raw) == reg['proposal_sha256'], 'proposal_pin')
    cfg = json.loads(proposal_raw)
    out = root / cfg['run']
    check(out.resolve().parent == (root / 'results').resolve(), 'run_boundary')
    out.mkdir(exist_ok=False)
    start = time.monotonic()
    summary = dict(status='running', stage='pins', pid=os.getpid(), main_outputs=0, engineering_outputs=0,
                   tokenizer_encodes=0, model_loads=0, weight_bytes_read=0, GPU_queries=0, network_requests=0)
    guard = dict(forbidden_imports=0, forbidden_file_attempts=0, network_attempts=0, subprocess_attempts=0)

    def timeout(*unused):
        raise TimeoutError('CPU60_second_cap')

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(cfg['bounds']['wall_seconds'])
    try:
        save(out / 'summary.json', summary)
        check(reg['execution_enabled'] is True and reg['mode'] == cfg['mode'] and reg['model_inference_enabled'] is False, 'execution_scope')
        check(os.environ.get('KV_GROUP_STATS_WATCHDOG') == 'registered_90_seconds', 'outer_watchdog_required')
        (out / 'proposal_snapshot.json').write_bytes(proposal_raw)
        (out / 'execution_registration.json').write_bytes(registration_raw)
        for rel, pin in reg['source_sha256'].items():
            data = (root / rel).read_bytes()
            check(sha(data) == pin, 'source_pin:' + rel)
            (out / ('source_' + Path(rel).name)).write_bytes(data)
        check(reg['source_sha256'].get('scripts/accept_group_statistics.py') == sha(Path(__file__).read_bytes()), 'runner_registered')
        total = 0
        for rel, pin in cfg['inputs'].items():
            data = (root / rel).read_bytes()
            check(sha(data) == pin, 'input_pin:' + rel)
            total += len(data)
        save(out / 'input_manifest.json', dict(files=cfg['inputs'], bytes=total))

        def audit(event, event_args):
            if event == 'import' and event_args[0].split('.')[0] in ('torch', 'transformers', 'tokenizers', 'vllm', 'tensorflow', 'jax'):
                guard['forbidden_imports'] += 1
                raise RuntimeError('model_or_tokenizer_import_forbidden')
            if event.startswith('socket.'):
                guard['network_attempts'] += 1
                raise RuntimeError('all_socket_operations_forbidden')
            if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork', 'os.forkpty'):
                guard['subprocess_attempts'] += 1
                raise RuntimeError('subprocess_forbidden')
            if event == 'open' and isinstance(event_args[0], (str, bytes)):
                p = Path(os.fsdecode(event_args[0])).resolve()
                mode = event_args[1]
                writing = isinstance(mode, str) and any(c in mode for c in 'wax+') or event_args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
                if (p.is_relative_to(root / 'models') or p.suffix in ('.safetensors', '.bin', '.pt', '.pth')
                        or writing and not p.is_relative_to(out)):
                    guard['forbidden_file_attempts'] += 1
                    raise RuntimeError('file_scope_forbidden')

        sys.addaudithook(audit)
        import reliability_group_statistics as module
        save(out / 'execution_snapshot.json', dict(registration_sha256=args.registration_sha256, argv=sys.argv,
             python=sys.version, executable=sys.executable, pid=os.getpid(), mode=cfg['mode'],
             original_proposal_false_flags_unchanged=True, bounds=cfg['bounds'], source_sha256=reg['source_sha256'],
             module_loaded_sha256=sha(Path(module.__file__).read_bytes())))
        native_rel = next(p for p in cfg['inputs'] if p.endswith('planned_cells_with_budgets.jsonl'))
        native = [json.loads(line) for line in (root / native_rel).read_text().splitlines()]
        fixtures = build_fixtures()
        check([s['id'] for s in fixtures] == [s['id'] for s in cfg['acceptance_cases']], 'fixed18_fixtures')
        save(out / 'software_fixtures.json', fixtures)
        outputs = []
        for spec in fixtures:
            summary['stage'] = spec['id']
            value = run_fixture(module, spec, native)
            outputs.append(dict(id=spec['id'], action=spec['action'], passed=True, output=value))
            save(out / 'software_results.json', outputs)
        # Pin-point numerical assertions supplement the independent audit.
        by = {o['id']: o['output'] for o in outputs}
        check(by['G01']['comparisons']['adapted_snapkv']['joint_delta'] == 0 and by['G01']['comparisons']['uniform_random']['joint_delta'] == -.5, 'G01_expected')
        check(all(abs(a - b) < 1e-12 for a, b in zip(by['G02']['methods']['adapted_snapkv']['ci95'], [-.925, .925])), 'G02_expected')
        for gid, delta in [('G03', 0), ('G04', 1), ('G05', -1)]:
            check(all(m['joint_delta'] == delta and m['joint_delta_ci95'] == [delta, delta] for m in by[gid]['comparisons'].values()), gid + '_expected')
        check(by['G06']['comparisons']['adapted_snapkv']['unavailable_task_pairs'] == 1, 'G06_semantic_NA')
        check(by['G07']['conditions']['adapted_snapkv']['raw_task_sum'] == 2 and by['G07']['conditions']['adapted_snapkv']['strict_task_count'] == 1, 'G07_truncation')
        check(by['G08']['conditions']['adapted_snapkv']['task_NA'] == 1, 'G08_NA')
        check(all(m['strict_conditional_damage'] is None for m in by['G16']['comparisons'].values()), 'G16_denominator_zero')
        check(by['G17'] == [0, 1, .25], 'G17_expected')
        save(out / 'native48_pending_coverage.json', by['G18'])
        check(not any(guard.values()), 'guard_violation')
        summary.update(status='complete', stage='complete', unique_software_cases=18,
                       actual48_effects_computed=False, elapsed_seconds=time.monotonic() - start)
    except BaseException as error:
        summary.update(status='failed', error=type(error).__name__ + ':' + str(error), elapsed_seconds=time.monotonic() - start)
        (out / 'failure_traceback.txt').write_text(traceback.format_exc())
        raise
    finally:
        signal.alarm(0)
        save(out / 'CPU_guard_observations.json', guard)
        save(out / 'summary.json', summary)
        manifest = {p.name: sha(p.read_bytes()) for p in out.iterdir() if p.is_file() and p.name != 'manifest.json'}
        save(out / 'manifest.json', manifest)
        check(len(manifest) + 1 <= cfg['bounds']['max_archive_files'] and sum(p.stat().st_size for p in out.iterdir() if p.is_file()) <= cfg['bounds']['max_archive_bytes'], 'archive_cap')
        print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
