"""Offline two-model native frontend/budget preflight, with no model library."""
import os
os.environ.update(USE_TORCH='0', USE_TF='0', USE_FLAX='0', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1')
import sys
sys.dont_write_bytecode = True
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import signal
import time
import traceback
from reliability_system_core import budget_plan, kv_layout, require


def sha(b): return hashlib.sha256(b).hexdigest()
def save(p, value): p.write_text(json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2)+'\n')


def effective_offsets(text, ids, offsets, special_map):
    """Zero-offset native controls may be mapped only by literal/ID occurrence."""
    out = [list(pair) for pair in offsets]; records = []
    for literal, token in special_map.items():
        positions = [i for i, v in enumerate(ids) if v == token]
        if not any(out[i] == [0, 0] for i in positions): continue
        starts = []; at = 0
        while True:
            start = text.find(literal, at)
            if start < 0: break
            starts.append(start); at = start+len(literal)
        require(len(starts) == len(positions), 'ambiguous_zero_offset_special')
        for i, start in zip(positions, starts):
            if out[i] == [0, 0]:
                out[i] = [start, start+len(literal)]
                records.append(dict(token_index=i, token_id=token, literal=literal, character_span=out[i]))
    require(all(type(a) is int and type(b) is int and 0 <= a < b <= len(text) for a, b in out), 'unmapped_or_invalid_offsets')
    return out, records


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--execute', action='store_true'); ap.add_argument('--proposal-sha256', required=True); ap.add_argument('--runner-sha256', required=True); ap.add_argument('--validator-sha256', required=True); a = ap.parse_args()
    r = Path(__file__).resolve().parent.parent
    require(a.execute and str(r) == '/home/user/jhk/project/Directional Exploration/kv-pruning', 'server_CPU_execute')
    raw = (r/'configs/independent-evidence-frontends-preflight-v1.json').read_bytes(); require(sha(raw) == a.proposal_sha256, 'proposal_pin')
    cfg = json.loads(raw); out = r/cfg['run']; require(out.resolve().parent == (r/'results').resolve(), 'run_boundary'); out.mkdir(exist_ok=False)
    started = time.monotonic(); active = None
    state = dict(status='running', stage='pins', pid=os.getpid(), main_outputs=0, engineering_outputs=0, model_forward_calls=0, tokenizer_encodes=0, full_native_variants=0, model_case_rows=0, budget_evaluations=0, GPU_queries=0, network_requests=0, weight_bytes_read=0)
    guards = dict(model_metadata_open_events=0, forbidden_read_attempts=0, network_attempts=0, subprocess_attempts=0)
    def timeout(*args): raise TimeoutError('CPU120_second_cap')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(cfg['bounds']['wall_seconds'])
    try:
        save(out/'summary.json', state); (out/'proposal_snapshot.json').write_bytes(raw)
        require(os.environ.get('KV_FRONTEND_CPU_WATCHDOG') == 'registered_150_seconds', 'outer_CPU_watchdog_required')
        require(sha(Path(__file__).read_bytes()) == a.runner_sha256, 'runner_pin')
        validator = r/cfg['independent_validator']; require(sha(validator.read_bytes()) == a.validator_sha256, 'validator_pin')
        (out/'source_runner.py').write_bytes(Path(__file__).read_bytes()); (out/'source_validator.py').write_bytes(validator.read_bytes()); (out/'source_core.py').write_bytes((r/'scripts/reliability_system_core.py').read_bytes())
        allowed = {Path(m['path']).resolve():{(Path(m['path'])/name).resolve() for name in m['metadata_sha256']} for m in cfg['models']}
        def audit(event, args):
            if event == 'open' and isinstance(args[0], (str, bytes)):
                p = Path(os.fsdecode(args[0])).resolve()
                for root, names in allowed.items():
                    if p.is_relative_to(root):
                        if p not in names:
                            guards['forbidden_read_attempts'] += 1; raise RuntimeError('nonallowlisted_model_file:'+str(p))
                        guards['model_metadata_open_events'] += 1
                if p.suffix in ('.safetensors', '.pt', '.pth', '.bin'):
                    guards['forbidden_read_attempts'] += 1; raise RuntimeError('weight_or_tensor_file_forbidden')
            elif event in ('socket.connect', 'socket.connect_ex', 'socket.bind'):
                guards['network_attempts'] += 1; raise RuntimeError('network_forbidden')
            elif event in ('subprocess.Popen', 'os.system'):
                guards['subprocess_attempts'] += 1; raise RuntimeError('subprocess_forbidden')
        sys.addaudithook(audit)
        input_bytes = 0
        for name, expected in cfg['inputs'].items():
            b = (r/name).read_bytes(); require(sha(b) == expected, 'input_pin:'+name); input_bytes += len(b)
        save(out/'input_manifest.json', dict(files=cfg['inputs'], bytes=input_bytes))
        metadata = {}; metadata_bytes = 0
        for model in cfg['models']:
            directory = Path(model['path']); require(directory.name == model['revision'], 'model_revision')
            checked = {}
            for name, expected in model['metadata_sha256'].items():
                b = (directory/name).read_bytes(); require(sha(b) == expected, 'model_metadata:'+name)
                metadata_bytes += len(b); checked[name] = dict(sha256=sha(b), bytes=len(b))
            tc = json.loads((directory/'tokenizer_config.json').read_text()); require(sha(tc['chat_template'].encode()) == model['chat_template_sha256'], 'native_template_pin')
            metadata[model['key']] = dict(path=str(directory), files=checked, template_sha256=model['chat_template_sha256'])
        require(metadata_bytes <= cfg['bounds']['max_metadata_bytes'], 'unique_metadata_byte_cap'); save(out/'metadata_checks.json', dict(models=metadata, unique_metadata_bytes=metadata_bytes))
        versions = {k:importlib.metadata.version(k) for k in cfg['versions']}; require(versions == cfg['versions'], 'framework_versions')
        save(out/'execution_snapshot.json', dict(proposal_sha256=sha(raw), runner_sha256=a.runner_sha256, validator_sha256=a.validator_sha256, execution_enabled=True, runner_implemented=True, scope='CPU tokenizer/config and predicted budget only', original_proposal_flags_unchanged=True, versions=versions, python=sys.version, environment={k:os.environ[k] for k in cfg['environment']}, weight_loading=False, GPU=False, network=False))
        allcases = [json.loads(line) for line in (r/cfg['cases']).read_text().splitlines()]
        cases = [c for c in allcases if c['split_role'] in cfg['selection']['allowed_roles']]
        require(Counter(c['split_role'] for c in cases) == {'engineering':4, 'development':12} and len({c['case_id'] for c in cases}) == 16, 'fixed_role_selection')
        old = {x['case_id']:x for x in json.loads((r/cfg['Qwen_regression_reference']).read_text())}; require(len(old) == 14, 'Qwen_reference_count')
        from transformers import AutoTokenizer, AutoConfig
        variants = []; rows = []; evaluations = []; layouts = {}; probes = {}; qwen_matches = []
        state['stage'] = 'native_frontends'
        for model in cfg['models']:
            key = model['key']; directory = Path(model['path']); layout = model['config_layout']
            ac = AutoConfig.from_pretrained(str(directory), local_files_only=True, trust_remote_code=False)
            require(ac.num_hidden_layers == layout['layers'] and ac.num_attention_heads == layout['attention_heads'] and ac.num_key_value_heads == layout['KV_heads'] and ac.hidden_size//ac.num_attention_heads == layout['head_dimension'], 'config_layout_changed')
            if key == 'Qwen': require(ac.model_type == 'qwen2' and not ac.use_sliding_window and set(ac.layer_types) == {'full_attention'}, 'Qwen_config_Full')
            else: require(ac.model_type == 'mistral' and ac.sliding_window is None, 'Mistral_config_Full_candidate')
            desc = kv_layout([dict(attention_type='full_attention', batch=1, key=dict(heads=layout['KV_heads'], dimension=layout['head_dimension'], element_bytes=2), value=dict(heads=layout['KV_heads'], dimension=layout['head_dimension'], element_bytes=2)) for _ in range(layout['layers'])])
            require(desc['bytes_per_prefix_slot'] == layout['bytes_per_prefix_slot_expected'], 'config_KV_byte_prediction'); layouts[key] = desc
            tok = AutoTokenizer.from_pretrained(str(directory), local_files_only=True, trust_remote_code=False, use_fast=True); require(tok.is_fast, 'fast_tokenizer_required')
            specials = {literal:tok.convert_tokens_to_ids(literal) for literal in tok.all_special_tokens}
            first_system = cases[0]['prompt']['system']; alone = tok.apply_chat_template([dict(role='system',content=first_system)], tokenize=False, add_generation_prompt=False)
            if key == 'Mistral': require(alone == tok.bos_token and first_system not in alone, 'Mistral_system_only_probe')
            probes[key] = dict(system_only_render=alone, system_only_contains_original_content=first_system in alone, cached_prefix_derived_from_full_render=True, special_token_map=specials)
            save(out/'native_layout_probes.json',probes); save(out/'layout_predictions.json',layouts)
            for case in cases:
                require(case['prompt']['system'] == first_system, 'unexpected_system_change')
                qstart = case['question_start_user_character']; original_user = case['prompt']['user']; require(original_user[qstart:] == case['question'], 'original_question_boundary')
                questions = [case['question']]+(cfg['query_boundary']['alternatives_for_engineering_only'] if case['split_role'] == 'engineering' else [])
                prefix_variants = []; base = None
                for index, question in enumerate(questions):
                    active = dict(model=key,case_id=case['case_id'],variant=index)
                    user = original_user[:qstart]+question; messages = [dict(role='system',content=first_system),dict(role='user',content=user)]
                    text = tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
                    if key == 'Qwen':
                        system_frame = '<|im_start|>system\n'+first_system+'<|im_end|>\n'
                        before_user = system_frame+'<|im_start|>user\n'; expected = before_user+user+'<|im_end|>\n<|im_start|>assistant\n'
                        require(alone == system_frame, 'Qwen_system_probe')
                    else:
                        system_frame = tok.bos_token+'[INST] '+first_system+'\n\n'; before_user = system_frame; expected = before_user+user+'[/INST]'
                    require(text == expected, 'native_render_contract')
                    encoded = tok(text, add_special_tokens=False, return_offsets_mapping=True); state['tokenizer_encodes'] += 1
                    native_ids = tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True); state['tokenizer_encodes'] += 1
                    ids = encoded['input_ids']; require(ids == native_ids and len(ids) <= cfg['bounds']['max_input_tokens'], 'native_ids_or_length')
                    offsets = [list(x) for x in encoded['offset_mapping']]; effective, mappings = effective_offsets(text,ids,offsets,specials)
                    qchar = len(before_user)+qstart; require(text[qchar:qchar+len(question)] == question, 'native_question_span')
                    n = next(i for i,(a,b) in enumerate(effective) if b > qchar)
                    require(0 < n < len(ids) and all(b <= qchar for a,b in effective[:n]) and all(b > qchar for a,b in effective[n:]), 'prefix_contains_query_or_noncontiguous_offsets')
                    protected = [i for i,(a,b) in enumerate(effective) if a < len(system_frame) and b > 0]
                    coverage = {j for i in protected for j in range(max(0,effective[i][0]),min(len(system_frame),effective[i][1]))}
                    require(coverage == set(range(len(system_frame))) and protected and max(protected) < n, 'incomplete_system_protection')
                    crossing = [i for i,(a,b) in enumerate(effective) if a < qchar < b]; require(all(i >= n for i in crossing), 'crossing_query_token_cached')
                    variant = dict(model=key,case_id=case['case_id'],split_role=case['split_role'],variant=index,question=question,rendered=text,rendered_sha256=sha(text.encode()),input_ids=ids,native_tokenized_ids=native_ids,offsets=offsets,effective_offsets=effective,zero_offset_control_mappings=mappings,prefix_tokens=n,suffix_tokens=len(ids)-n,system_character_end=len(system_frame),user_character_start=len(before_user),question_character_start=qchar,header_ids=protected,crossing_query_token_indices=crossing,prefix_ids_sha256=sha(json.dumps(ids[:n],separators=(',',':')).encode()))
                    variants.append(variant); prefix_variants.append(ids[:n]); state['full_native_variants'] += 1; save(out/'native_variants.json',variants)
                    if index == 0:
                        base = {k:v for k,v in variant.items() if k not in ['rendered','native_tokenized_ids','question','variant']}; base.update(prompt_sha256=case['prompt_sha256'],context_group_id=case['context_group_id'],gold_sha256=case['gold_sha256'],KV_bytes_per_slot_predicted=desc['bytes_per_prefix_slot'],actual_KV_tensor_verified=False)
                require(all(x == prefix_variants[0] for x in prefix_variants), 'alternative_query_changes_cached_prefix')
                if key == 'Qwen' and case['case_id'] in old:
                    prior = old[case['case_id']]
                    require(all(base[k] == prior[k] for k in ['input_ids','prefix_tokens','suffix_tokens','header_ids','prompt_sha256']), 'Qwen14_regression_changed'); qwen_matches.append(case['case_id'])
                rows.append(base); state['model_case_rows'] += 1; save(out/'tokenized_cases.json',rows)
                for retention in cfg['retentions']:
                    for mode in cfg['budget']['protected_modes']:
                        protected = base['header_ids'] if mode == 'complete_system_union_anchors' else []
                        budget = budget_plan(base['prefix_tokens'],retention,protected,cfg['budget']['sink'],cfg['budget']['recent'])
                        evaluations.append(dict(model=key,case_id=case['case_id'],split_role=case['split_role'],retention=retention,protection_mode=mode,budget=budget,requested_prefix_KV_bytes_predicted=budget['requested_slots']*desc['bytes_per_prefix_slot'],actual_KV_tensor_verified=False))
                state['budget_evaluations'] = len(evaluations); save(out/'budget_evaluations.json',evaluations); active = None; save(out/'summary.json',state)
        require(state['tokenizer_encodes'] == 96 and len(variants) == 48 and len(rows) == 32 and len(evaluations) == 128 and len(qwen_matches) == 14, 'complete_frontend_coverage')
        require(not any(name.split('.')[0] in ['torch','tensorflow','jax','vllm'] for name in sys.modules), 'forbidden_model_library_loaded')
        require(not any(guards[k] for k in ['forbidden_read_attempts','network_attempts','subprocess_attempts']), 'CPU_boundary_guard')
        coverage = []
        for model in ['Qwen','Mistral']:
            for retention in cfg['retentions']:
                for mode in cfg['budget']['protected_modes']:
                    row = dict(model=model,retention=retention,protection_mode=mode)
                    for role, count in [('engineering',4),('development',12)]:
                        values = [x for x in evaluations if x['model']==model and x['retention']==retention and x['protection_mode']==mode and x['split_role']==role]
                        require(len(values) == count, 'coverage_denominator'); row[role] = dict(scheduled=count,feasible=sum(x['budget']['state']=='ok' for x in values),infeasible=sum(x['budget']['state']=='infeasible_budget' for x in values))
                    coverage.append(row)
        save(out/'budget_coverage.json',coverage); save(out/'Qwen_regression.json',dict(matching_original_cases=qwen_matches,original14_unchanged=True))
        save(out/'CPU_guard_observations.json',dict(**guards,torch_loaded=False,model_forward_calls=0,network_requests=0,weight_bytes_read=0,GPU_queries=0))
        lines=['# CPU native frontend and budget preflight','','Predicted layout/budget only;no weights,models,GPU,network orsealed encodes.','','| Model | Retention | Protection | Engineering feasible/4 | DEV feasible/12 |','| --- | --- | --- | --- | --- |']
        for row in coverage:lines.append(f"| {row['model']} | {row['retention']} | {row['protection_mode']} | {row['engineering']['feasible']}/4 | {row['development']['feasible']}/12 |")
        lines+=['','CPU feasible does not imply tensor correctness or task support. Additional2engineering encodes do not replace oldGPU engineering cases. No automatic GPU queue.']
        (out/'report.md').write_text('\n'.join(lines)+'\n')
        for name,want in cfg['inputs'].items():require(sha((r/name).read_bytes())==want,'input_changed:'+name)
        state.update(status='complete',stage='complete',Qwen_original14_unchanged=True,model_libraries_loaded=False,sealed_encodes=0,tensor_or_task_support_verified=False)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc),active=active); (out/'failure.txt').write_text(traceback.format_exc()); save(out/'CPU_guard_observations_at_stop.json',guards)
    finally:
        signal.alarm(0); state['elapsed_seconds'] = time.monotonic()-started; save(out/'summary.json',state)
        files = [p for p in out.iterdir() if p.is_file()]
        if len(files)>=cfg['bounds']['max_archive_files'] or sum(p.stat().st_size for p in files)>=cfg['bounds']['max_archive_bytes']:
            state.update(status='failed',archive_cap_exceeded=True); save(out/'summary.json',state)
        save(out/'manifest.json',{p.name:sha(p.read_bytes()) for p in files}); print(json.dumps(state),flush=True)
    return 0 if state['status']=='complete' else 1


if __name__ == '__main__': raise SystemExit(main())
