"""Server CPU acceptance of stage orchestration and lazy HF guard wiring."""
import sys
sys.dont_write_bytecode=True
import argparse
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback
from reliability_system_core import ContractError,require
from reliability_system_adapters import hash_json
from reliability_hf_orchestrator import HFOrchestrator,case_binding
from hf_orchestration_acceptance import validate_case


def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=True,allow_nan=False,indent=2)+'\n')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-dry-run',action='store_true');a=ap.parse_args()
    r=Path(__file__).resolve().parent.parent;require(a.execute_dry_run and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning','server dry-run required')
    raw=(r/'configs/hf-orchestration-dry-run-v1.json').read_bytes();cfg=json.loads(raw);o=r/cfg['run'];require(o.resolve().parent==(r/'results').resolve(),'run boundary');o.mkdir(exist_ok=False)
    started=time.monotonic();state=dict(status='running',stage='verify_sources',pid=os.getpid(),main_outputs=0,engineering_outputs=0,software_cases_passed=0)
    def timeout(*a):raise TimeoutError('60_second_cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(60)
    try:
        require(cfg['mode']=='dry_run' and not any(cfg[k] for k in ['model_loading_allowed','bootstrap_generation_allowed','DEV_generation_allowed']),'dry_run_only_proposal')
        (o/'proposal_snapshot.json').write_bytes(raw)
        names=['reliability_hf_orchestrator.py','reliability_qwen_hf_backend.py','hf_orchestration_acceptance.py','accept_hf_orchestration_dry_run.py','reliability_execution_contract.py','reliability_system_core.py','reliability_system_adapters.py']
        sourcehash={};lazy_imports=[]
        heavy={'torch','transformers','trec_context_gate','trec_pruning_run','trec_pruning_utils'}
        allowed={'copy','time','hashlib','importlib','json','os','pathlib','subprocess','sys','argparse','ast','collections','signal','traceback','fractions','math','reliability_system_core','reliability_system_adapters','reliability_execution_contract','reliability_hf_orchestrator','hf_orchestration_acceptance','reliability_qwen_hf_backend'}|heavy
        for name in names:
            b=(r/'scripts'/name).read_bytes();tree=ast.parse(b)
            parents={child:parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
            for n in ast.walk(tree):
                mods=[x.name.split('.')[0] for x in n.names] if isinstance(n,ast.Import) else ([n.module.split('.')[0]] if isinstance(n,ast.ImportFrom) and n.module else [])
                require(set(mods)<=allowed,'import outside source allowlist')
                require(not(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ['exec','eval','compile','__import__']),'dynamic execution')
                if set(mods)&heavy:
                    owner=parents.get(n)
                    while owner is not None and not isinstance(owner,(ast.FunctionDef,ast.AsyncFunctionDef)):owner=parents.get(owner)
                    require(name=='reliability_qwen_hf_backend.py' and owner is not None and owner.name=='_load','heavy_import_not_lazy_guarded')
                    lazy_imports.append(dict(source=name,function=owner.name,modules=mods))
            sourcehash[name]=sha(b);(o/('source_'+name)).write_bytes(b)
        bodies={};nbytes=nlines=0
        for p,h in cfg['inputs'].items():
            b=(r/p).read_bytes();require(sha(b)==h,'input pin:'+p);bodies[p]=b;nbytes+=len(b)
            if p.endswith('.jsonl'):nlines+=len(b.splitlines())
        require(nbytes<=cfg['bounds']['input_bytes_max'] and nlines<=cfg['bounds']['jsonl_rows_max'],'input bounds')
        save(o/'input_manifest.json',dict(files=cfg['inputs'],bytes=nbytes,jsonl_rows=nlines))
        save(o/'execution_snapshot.json',dict(execution_enabled=True,runner_implemented=True,execution_scope='CPU dry-run and software doubles only',source_sha256=sourcehash,proposal_sha256=sha(raw),python=sys.version,lazy_heavy_import_audit=lazy_imports,real_model_execution_enabled=False,bounds=cfg['bounds']))
        state['stage']='software_acceptance';cases_out=[];save(o/'software_acceptance.json',cases_out)
        for i in range(22):
            v=validate_case(i);require(v['id']==cfg['acceptance_ids'][i],'acceptance id');cases_out.append(v);state['software_cases_passed']+=1;save(o/'software_acceptance.json',cases_out)
        read=lambda p:json.loads(bodies[p])
        tok=read('results/20261030-independent-squad-tokenizer-v1/tokenized_cases.json')
        prepared={x['case_id']:x for x in map(json.loads,bodies['results/20261030-independent-task-preflight-v1/selected_provisional.jsonl'].splitlines())}
        cases=[]
        for x in tok:
            c=dict(x);require(c['split_role'] in ['engineering','development'],'no sealed input');c['context_group_id']=prepared[c['case_id']]['context_group_id'];cases.append(c)
        old_spec=read('results/20261030-condition-admission-v1/condition_specs.json')
        old_evidence=read('results/20261030-condition-admission-v1/engineering_evidence.json')
        old_report=read('results/20261030-condition-admission-v1/report.json')
        actual=read('results/20261030-independent-squad-full-v1/execution_snapshot.json')
        runtime_scope=dict(version='new_HF_adapter_scope_v1',model_runtime_reference=actual,implementation_source_sha256=sourcehash,
            input_file_sha256=cfg['inputs']['results/20261030-independent-squad-tokenizer-v1/tokenized_cases.json'],note='Desired runtime bound to new code,not yet observed by GPU execution')
        runtime=hash_json(runtime_scope)
        policy=dict(mode='dry_run',execution_enabled=False,bootstrap_generation_enabled=False,DEV_generation_enabled=False,
            runtime_digest=runtime,max_engineering_calls=14,max_DEV_calls=36,max_input_tokens=2048,wall_seconds=60)
        spy=[]
        def forbidden_factory():spy.append('unexpected factory');raise AssertionError('dry_run_loaded_backend')
        engine=HFOrchestrator(cases,old_spec['specs'],runtime,policy,forbidden_factory)
        stale=[]
        for ev in old_evidence:
            try:engine.offer_evidence(ev)
            except ContractError as exc:
                require(str(exc)=='stale_engineering_for_new_backend','unexpected old evidence rejection');stale.append(dict(condition_id=ev['condition_id'],reason=str(exc)))
            else:raise AssertionError('old engineering silently reused')
        state['stage']='plan_stage_order';plan=engine.dry_run_plan()
        require(not spy and engine.loader_attempts==engine.backend_calls==0,'backend called during dryrun')
        basecfg=read('configs/independent-squad-full-proposal-v1.json');tp=read('configs/independent-squad-tokenizer-proposal-v1.json')
        backend_descriptor=dict(adapter='reliability_qwen_hf_backend.QwenHFBackend',adapter_source_sha256=sourcehash['reliability_qwen_hf_backend.py'],
            execution_enabled=False,separate_GPU_execution_registered=False,registered_runtime_digest=runtime,
            project_root=str(r),model_path=tp['model'],model_revision=tp['model_revision'],model_metadata_files=tp['files'],
            source_files={**{('scripts/'+n):h for n,h in basecfg['sources'].items()},**{('scripts/'+n):h for n,h in sourcehash.items()}},versions=basecfg['versions'],weights=basecfg['weights'],
            decode=basecfg['decode'],gpu_uuid=basecfg['gpu_uuid'],idle_memory_mib_max=128,torch_seed=20261030,
            outer_GPU_watchdog_registered=False,real_GPU_engineering_validated=False)
        save(o/'backend_descriptor.json',backend_descriptor)
        save(o/'runtime_scope.json',dict(runtime_digest=runtime,material=runtime_scope))
        save(o/'prepared_bindings.json',[dict(case_id=c['case_id'],role=c['split_role'],case_input_digest=case_binding(c)) for c in cases])
        save(o/'stage_plan.json',plan);save(o/'stale_evidence.json',stale)
        eng=plan['engineering'];dev=plan['development'];counts=Counter(x['decision']['decision']['admission_state'] for x in dev)
        prior=old_report['actual']
        observed=dict(prepared_cases=len(cases),old_scope_eligible_DEV=prior['future_eligible'],old_scope_blocked_budget_DEV=prior['future_blocked_budget'],old_scope_blocked_evidence_DEV=prior['future_blocked_engineering_unverified'],
            old_evidence_rejected_for_new_backend_conditions=len(stale),new_scope_bootstrap_planned_operations=sum(x['state']=='planned_no_execution' for x in eng),
            new_scope_bootstrap_budget_blocked_case_conditions=sum(x['state']=='blocked_budget' for x in eng),
            new_scope_DEV_cells=len(dev),new_scope_DEV_blocked_budget=counts['blocked_budget'],new_scope_DEV_waiting_current_engineering=counts['blocked_engineering_unverified'],
            dry_plan_backend_factory_attempts=engine.loader_attempts,dry_plan_backend_execute_calls=engine.backend_calls,
            negative_real_adapter_guard_invocations=2,real_model_weight_loads=0,model_outputs=0)
        require(observed==cfg['expected'],'frozen stage expectations:'+str(observed))
        require(not any(x.split('.')[0] in ['torch','transformers','vllm','trec_context_gate','trec_pruning_run'] for x in sys.modules),'heavy module imported')
        for p,h in cfg['inputs'].items():require(sha((r/p).read_bytes())==h,'input changed')
        save(o/'report.json',dict(actual=observed,new_runtime_digest=runtime,old_runtime_digest=old_spec['runtime_digest'],
            new_scope_engineering_observations_created=0,prospective_plan_only=True,lazy_HF_code_wired=True,new_HF_GPU_behavior_validated=False,
            real_model_callback_invoked=False,old_results_and_gates_unchanged=True,independent_scientific_confirmation=False))
        (o/'report.md').write_text('# New HF orchestration dry-run\n\n22software cases passed. No weight loading,model inference,GPU or network operation.\n\nOld scope:36eligible/20budget-blocked/4evidence-blocked DEV cells.\n\nNew code scope:14planned bootstrap calls and4budget-blocked engineering case-conditions;60DEV cells consist of20budget blocks and40waiting for new-version engineering. Old evidence rejected for all5conditions.\n\nThis is code wiring and CPU control-flow validation,not GPU engineering success or authorization to run the planned cells.\n')
        state.update(status='complete',stage='complete',input_files=len(bodies),input_bytes=nbytes,jsonl_rows=nlines,actual=observed,model_libraries_loaded=False,gpu_queried=False)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc));(o/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0);state['elapsed_seconds']=time.monotonic()-started;save(o/'summary.json',state)
        files=[p for p in o.iterdir() if p.is_file()];require(len(files)<32 and sum(p.stat().st_size for p in files)<16777216,'archive cap')
        save(o/'manifest.json',{p.name:sha(p.read_bytes()) for p in files});print(json.dumps(state),flush=True)
    return 0 if state['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
