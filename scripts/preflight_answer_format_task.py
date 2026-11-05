"""Bounded server-only CPU preflight. Never imports/executes author scripts."""
import sys
sys.dont_write_bytecode = True
import argparse
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback
import urllib.request
from datetime import datetime, timezone

from answer_format_task import (TaskError, article_components, require, score_response,
                                select_cases, sha256, strict_json, validate_dataset)


PROPOSAL_SHA = 'a106a9eae2f0b67f4d6e16e33447c8097adc53e735ac8ee50e449ee0191ad14e'
SERVER_ROOT = '/home/user/jhk/project/Directional Exploration/kv-pruning'
ALLOWED_IMPORTS = {'argparse','ast','copy','hashlib','json','os','pathlib','signal','sys',
                   'time','traceback','urllib','datetime','answer_format_task',
                   're','string','unicodedata','collections','decimal'}


class Archive:
    def __init__(self, out, limits):
        self.out, self.limits = out, limits

    def check_size(self, target, size, final=False):
        files = [p for p in self.out.rglob('*') if p.is_file()]
        total = sum(p.stat().st_size for p in files if p != target)+size
        count = len(files)+(not target.exists())
        reserve = 0 if final else 65536
        require(total <= self.limits['archive_total_bytes_max']-reserve, 'archive_byte_cap')
        require(count <= self.limits['archive_files_max']-(0 if final else 3), 'archive_file_cap')

    def write(self, name, raw, replace=False, final=False):
        p = self.out/name
        require(p.resolve().is_relative_to(self.out), 'archive_path_boundary')
        require(not p.exists() or replace, 'archive_would_overwrite:'+name)
        self.check_size(p, len(raw), final)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)

    def save(self, name, value, replace=False, final=False):
        self.write(name, (json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2)+'\n').encode(), replace, final)


def toy_dataset(n):
    return dict(version='1.1', data=[dict(title=f'article{i}', paragraphs=[dict(
        context=f'sample passage {i}', qas=[dict(id=f'question{i}', question=f'Which sample {i}?',
        answers=[dict(text='sample', answer_start=0)])])]) for i in range(n)])


def data_fixture(index, config):
    data = toy_dataset(2)
    if index == 0:
        data['data'][1]['paragraphs'][0]['qas'][0]['id'] = 'question0'
        expected = 'duplicate_question_id'
    elif index == 1:
        data['data'][0]['paragraphs'][0]['qas'][0]['answers'][0]['answer_start'] = 1
        expected = 'source_slice_mismatch'
    elif index == 2:
        data['data'][0]['paragraphs'][0]['qas'][0]['answers'] = []
        expected = 'missing_answers'
    elif index == 3:
        data['version'] = '2.0'
        expected = 'wrong_version'
    elif index == 4:
        data = toy_dataset(4)
        def paragraph(text, ident):
            return dict(context=text, qas=[dict(id=ident, question='Which?',
                        answers=[dict(text=text[0], answer_start=0)])])
        data['data'][0]['paragraphs'] = [paragraph('shared alpha', 'chain0')]
        data['data'][1]['paragraphs'] = [paragraph('shared  alpha', 'chain1a'), paragraph('shared beta', 'chain1b')]
        data['data'][2]['paragraphs'] = [paragraph('shared beta', 'chain2')]
        data['data'][3]['title'] = ' ARTICLE0 '
        before = copy.deepcopy(data)
        validate_dataset(data)
        groups, links = article_components(data['data'])
        require(len(groups)==1 and groups[0]['article_indices']==[0,1,2,3], 'D05_transitive_grouping')
        require(links==dict(title_link_events=1,paragraph_link_events=2), 'D05_link_counts')
        require(data==before, 'D05_raw_mutated')
        return dict(id=config['data_fixtures'][index]['id'], status='pass', components=1)
    elif index == 5:
        data = toy_dataset(34)
        validate_dataset(data)
        before = copy.deepcopy(data)
        a, am = select_cases(data, config)
        b, bm = select_cases(data, config, list(reversed(range(34))))
        require(a==b and am==bm and data==before, 'D06_order_or_source_mutation')
        # Independent explicit one-node component/rank construction as oracle.
        def direct_rank(i):
            cid = hashlib.sha256(('['+str(i)+']').encode()).hexdigest()
            rank = hashlib.sha256(b'kv-pruning/squad-v1.1/article-split/v1\0'+cid.encode()).hexdigest()
            return rank, cid
        indices = sorted(range(34), key=direct_rank)
        require([x['source_article_index'] for x in a]==indices, 'D06_canonical_ranking')
        require(am['roles']==dict(engineering=2,development=16,sealed_holdout=16), 'D06_roles')
        try:
            select_cases(toy_dataset(33), config)
        except TaskError as exc:
            require(str(exc)=='insufficient_article_components', 'D06_wrong_failure')
        else:
            raise TaskError('D06_missing_insufficiency_rejection')
        return dict(id=config['data_fixtures'][index]['id'], status='pass', roles=am['roles'])
    else:
        raise TaskError('unknown_data_fixture')
    try:
        validate_dataset(data)
    except TaskError as exc:
        require(expected in str(exc), 'wrong_data_fixture_error:'+str(exc))
        return dict(id=config['data_fixtures'][index]['id'], status='pass', observed_error=str(exc))
    raise TaskError('missing_data_fixture_rejection:'+expected)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TaskError('redirect_not_allowed')


def fetch_sources(config, archive, events):
    opener = urllib.request.build_opener(NoRedirect())
    downloaded, bodies = 0, []
    require(len(config['downloads'])==config['limits']['network_requests_max']==4, 'network_request_cap')
    for index, item in enumerate(config['downloads']):
        require(item['url'].startswith('https://raw.githubusercontent.com/'), 'source_host')
        target = archive.out/f'downloads/{index:02d}.source'
        target.parent.mkdir(exist_ok=True)
        event = dict(index=index, url=item['url'], bytes_received=0, status='started')
        events.append(event)
        archive.save('network_log.json', events, replace=True)
        try:
            req = urllib.request.Request(item['url'], headers={'User-Agent':'kv-pruning-cpu-preflight/1'})
            with opener.open(req, timeout=config['limits']['network_timeout_per_request_seconds']) as response:
                require(response.status==200 and response.geturl()==item['url'], 'source_response_identity')
                with target.open('xb') as stream:
                    while True:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        new_size = stream.tell()+len(chunk)
                        require(new_size <= config['limits']['single_file_bytes_max'], 'single_download_cap')
                        require(downloaded+len(chunk) <= config['limits']['download_total_bytes_max'], 'total_download_cap')
                        archive.check_size(target, new_size)
                        stream.write(chunk)
                        downloaded += len(chunk)
                        event['bytes_received'] += len(chunk)
            raw = target.read_bytes()
            blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            require(len(raw)==item['bytes'], 'source_length:'+str(index))
            require(blob==item['git_blob_sha1'], 'source_blob:'+str(index))
            if item.get('sha256'):
                require(sha256(raw)==item['sha256'], 'source_sha256:'+str(index))
            event.update(status='verified', sha256=sha256(raw), git_blob_sha1=blob)
            bodies.append(raw)
        except BaseException as exc:
            event.update(status='failed', error=repr(exc))
            raise
        finally:
            archive.save('network_log.json', events, replace=True)
    return bodies


def audit_sources(root, archive):
    hashes = {}
    for name in ['answer_format_task.py','preflight_answer_format_task.py']:
        raw = (root/'scripts'/name).read_bytes()
        tree = ast.parse(raw)
        for node in ast.walk(tree):
            mods = [x.name.split('.')[0] for x in node.names] if isinstance(node, ast.Import) else (
                [node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) and node.module else [])
            require(set(mods) <= ALLOWED_IMPORTS, 'unexpected_source_import')
            require(not (isinstance(node,ast.Call) and isinstance(node.func,ast.Name)
                         and node.func.id in {'exec','eval','compile','__import__'}), 'dynamic_source_execution')
        hashes[name] = sha256(raw)
        archive.write('source_'+name, raw)
    return hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    require(args.execute, 'explicit_execute_flag_required')
    root = Path(__file__).resolve().parent.parent
    require(str(root)==SERVER_ROOT, 'server_execution_only')
    raw = (root/'configs/answer-format-task-preflight-proposal-v1.json').read_bytes()
    require(sha256(raw)==PROPOSAL_SHA, 'proposal_pin')
    config = strict_json(raw.decode('utf-8'))
    # Decimal is useful for response parsing, but config JSON numbers must be JSON serializable.
    config = json.loads(raw)
    out = root/config['run_path_if_later_executed']
    require(out.resolve().parent == (root/'results').resolve() and not out.is_symlink(), 'run_boundary')
    out.mkdir(exist_ok=False)
    archive = Archive(out, config['limits'])
    started = time.monotonic()
    state = dict(status='running', stage='initialize', pid=os.getpid(),
                 started_utc=datetime.now(timezone.utc).isoformat(), main_outputs=0,
                 engineering_outputs=0, model_libraries_loaded=False, gpu_queried=False,
                 score_fixtures_passed=0, data_fixtures_passed=0, network=[])
    def deadline(signum, frame):
        raise TimeoutError('120_second_wall_cap')
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(config['limits']['wall_seconds'])
    try:
        archive.save('summary.json', state)
        archive.write('proposal_snapshot.json', raw)
        require(not config['execution_enabled'] and not config['runner_implemented'], 'proposal_should_remain_historical')
        for key in ['contract','source_review']:
            body = (root/config[key]).read_bytes()
            require(sha256(body)==config[key+'_sha256'], key+'_pin')
            archive.write(key+'_snapshot'+Path(config[key]).suffix, body)
        hashes = audit_sources(root, archive)
        archive.save('execution_snapshot.json', dict(proposal_sha256=PROPOSAL_SHA,
            execution_enabled=True, runner_implemented=True, model_execution_enabled=False,
            source_hashes=hashes, command='.venv/bin/python scripts/preflight_answer_format_task.py --execute',
            python=sys.version, limits=config['limits'], original_proposal_unchanged=True))
        state['stage'] = 'score_fixtures'
        require(len(config['fixtures'])==config['limits']['software_score_fixtures']==24, 'score_fixture_count')
        fixture_results = []
        archive.save('score_fixtures.json', fixture_results)
        for case in config['fixtures']:
            result = score_response(case['raw'], case['golds'])
            row = dict(id=case['id'], expected=case, actual=result, status='checking')
            fixture_results.append(row)
            archive.save('score_fixtures.json', fixture_results, replace=True)
            for key in ['format','candidate','em']:
                require(type(result[key]) is type(case[key]) and result[key]==case[key], case['id']+':'+key)
            require(result['f1'] is None if case['f1'] is None else
                    result['f1'] is not None and abs(result['f1']-case['f1'])<=config['scoring']['fixture_tolerance_f1'],
                    case['id']+':f1')
            if case.get('reason'):
                require(result['reason']==case['reason'], case['id']+':reason')
            require(result['joint_success']==bool(case['format'] and case['em']), case['id']+':joint')
            row['status'] = 'pass'
            state['score_fixtures_passed'] += 1
            archive.save('score_fixtures.json', fixture_results, replace=True)
        state['stage'] = 'data_fixtures'
        require(len(config['data_fixtures'])==config['limits']['software_data_fixtures']==6, 'data_fixture_count')
        data_results = []
        archive.save('data_fixtures.json', data_results)
        for index in range(6):
            data_results.append(data_fixture(index, config))
            state['data_fixtures_passed'] += 1
            archive.save('data_fixtures.json', data_results, replace=True)
        state['stage'] = 'download_pinned_sources'
        archive.save('summary.json', state, replace=True)
        bodies = fetch_sources(config, archive, state['network'])
        tree = ast.parse(bodies[1])
        archive.save('static_reference_audit.json', dict(author_code_executed=False,
            python_reference_sha256=sha256(bodies[1]), python_ast_nodes=sum(1 for _ in ast.walk(tree)),
            reference_function_names=[n.name for n in tree.body if isinstance(n,ast.FunctionDef)],
            javascript_not_score_oracle=True))
        state['stage'] = 'full_dataset_validation'
        archive.save('summary.json', state, replace=True)
        dataset = strict_json(bodies[0].decode('utf-8'))
        validation = validate_dataset(dataset)
        archive.save('data_validation.json', validation)
        state['stage'] = 'article_split_freeze'
        cases, manifest = select_cases(dataset, config)
        require(len(cases)==config['limits']['selected_cases']==34, 'selected_case_count')
        archive.save('split_manifest.json', manifest)
        archive.write('selected_cases.jsonl', ''.join(json.dumps(x,ensure_ascii=True,allow_nan=False)+'\n' for x in cases).encode())
        archive.save('data_card.json', dict(source_url=config['downloads'][0]['url'],
            source_sha256=sha256(bodies[0]), source_git_blob=config['downloads'][0]['git_blob_sha1'],
            source_version='SQuAD v1.1 dev, project-adapted subset, not official test',
            authors='Pranav Rajpurkar, Jian Zhang, Konstantin Lopyrev, Percy Liang',
            data_license='CC BY-SA 4.0', data_license_url='https://creativecommons.org/licenses/by-sa/4.0/',
            code_repository_license='Apache-2.0 in fixed BiDAF repository; separate from data',
            changes='Fixed JSON prompt, deterministic article-component longest-paragraph selection and internal role split; source fields untouched',
            pretraining_independence=False, long_context_validated=False, source_checks=validation))
        require(not any(x.split('.')[0] in {'torch','transformers','vllm'} for x in sys.modules), 'forbidden_model_import')
        require(sha256((root/'configs/answer-format-task-preflight-proposal-v1.json').read_bytes())==PROPOSAL_SHA, 'proposal_changed')
        state.update(status='complete', stage='complete', source_checks=validation,
            selected_roles=manifest['roles'], article_components=manifest['total_components'],
            data_sha256=sha256(bodies[0]), selected_context_words_min=min(x['context_words'] for x in cases),
            selected_context_words_max=max(x['context_words'] for x in cases),
            selected_cases=34, tokenizer_checked=False, kv_budget_checked=False,
            full_task_gate=None, report_adapter_validated=False, scientific_confirmation=False)
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
        archive.write('failure.txt', traceback.format_exc().encode('utf-8'), final=True)
    finally:
        signal.alarm(0)
        state['elapsed_seconds'] = time.monotonic()-started
        state['finished_utc'] = datetime.now(timezone.utc).isoformat()
        archive.save('summary.json', state, replace=True, final=True)
        files = [p for p in sorted(out.rglob('*')) if p.is_file()]
        archive.save('manifest.json', {str(p.relative_to(out)):dict(sha256=sha256(p.read_bytes()),bytes=p.stat().st_size) for p in files}, final=True)
        print(json.dumps(state, ensure_ascii=True), flush=True)
    return 0 if state['status']=='complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
