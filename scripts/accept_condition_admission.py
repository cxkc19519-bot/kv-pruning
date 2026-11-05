"""Read-only condition admission and engineering-evidence acceptance on server."""
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
from reliability_system_core import require
from reliability_system_adapters import hash_json
from reliability_execution_contract import condition_fingerprint,plan_case,engineering_evidence,admission,historical_observation
from execution_contract_acceptance import validate_case


def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=True,allow_nan=False,indent=2)+'\n')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    r=Path(__file__).resolve().parent.parent;require(a.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning','server explicit execution')
    raw=(r/'configs/condition-admission-acceptance-v1.json').read_bytes();cfg=json.loads(raw)
    out=r/cfg['run'];require(out.resolve().parent==(r/'results').resolve(),'run boundary');out.mkdir(exist_ok=False)
    started=time.monotonic();state=dict(status='running',stage='inputs',pid=os.getpid(),main_outputs=0,engineering_outputs=0,software_cases_passed=0)
    def timeout(*args):raise TimeoutError('60_second_cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(60)
    try:
        (out/'proposal_snapshot.json').write_bytes(raw)
        sources={};allowed={'sys','argparse','ast','collections','hashlib','json','os','pathlib','signal','time','traceback','copy','fractions','math','reliability_system_core','reliability_system_adapters','reliability_execution_contract','execution_contract_acceptance'}
        for name in ['reliability_execution_contract.py','execution_contract_acceptance.py','accept_condition_admission.py','reliability_system_core.py','reliability_system_adapters.py']:
            b=(r/'scripts'/name).read_bytes();tree=ast.parse(b)
            for n in ast.walk(tree):
                mods=[x.name.split('.')[0] for x in n.names] if isinstance(n,ast.Import) else ([n.module.split('.')[0]] if isinstance(n,ast.ImportFrom) and n.module else [])
                require(set(mods)<=allowed,'import outside allowlist')
                require(not(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ['exec','eval','compile','__import__']),'dynamic execution')
            sources[name]=sha(b);(out/('source_'+name)).write_bytes(b)
        bodies={};size=lines=0
        for path,digest in cfg['inputs'].items():
            b=(r/path).read_bytes();require(sha(b)==digest,'input pin:'+path);bodies[path]=b;size+=len(b)
            if path.endswith('.jsonl'):lines+=len(b.splitlines())
        require(size<=cfg['bounds']['input_bytes_max'] and lines<=cfg['bounds']['jsonl_rows_max'],'input bound')
        save(out/'input_manifest.json',dict(files=cfg['inputs'],bytes=size,jsonl_rows=lines))
        save(out/'execution_snapshot.json',dict(execution_enabled=True,runner_implemented=True,proposal_sha256=sha(raw),source_sha256=sources,
            python=sys.version,bounds=cfg['bounds'],inference=False,network=False,GPU=False,legacy_aggregate_pass_not_consumed=True))
        state['stage']='software_acceptance';fixtures=[];save(out/'software_acceptance.json',fixtures)
        for i in range(20):
            result=validate_case(i);require(result['id']==cfg['acceptance_ids'][i],'acceptance id');fixtures.append(result)
            state['software_cases_passed']+=1;save(out/'software_acceptance.json',fixtures)
        read=lambda p:json.loads(bodies[p])
        readrows=lambda p:[json.loads(x) for x in bodies[p].splitlines()]
        prefix='results/20261030-independent-squad-'
        fs=read(prefix+'full-v1/execution_snapshot.json');cs=read(prefix+'compression-v1/execution_snapshot.json')
        keys=['model_path','decode_actual','runtime_full_layers','kv_heads','head_dim','kv_dtype','bytes_per_token','versions','runner_sha256','source_hashes']
        require(all(fs[k]==cs[k] for k in keys),'runtime mismatch')
        runtime_digest=hash_json({k:fs[k] for k in keys})
        tokens=read(prefix+'tokenizer-v1/tokenized_cases.json');eng=[x for x in tokens if x['split_role']=='engineering'];dev=[x for x in tokens if x['split_role']=='development']
        require(len(eng)==2 and len(dev)==12 and len({x['case_id'] for x in tokens})==14,'frozen role plan')
        full_eng=readrows(prefix+'full-v1/engineering.jsonl');compact_eng=readrows(prefix+'compression-v1/engineering.jsonl')
        histories=readrows(prefix+'full-v1/generations.jsonl')+readrows(prefix+'compression-v1/generations.jsonl')
        history={}
        for row in histories:
            key=(row['case_id'],row['condition']);require(key not in history,'duplicate historical cell');history[key]=row
        require(len(history)==60,'historical cell count')
        specs=[];evidences=[];rows=[];condition_reports={}
        for name in cfg['conditions']:
            full=name=='full';pin=name.endswith('_system_pinned')
            spec=dict(condition_id=name,retention='1' if full else '1/2',protect_system=pin,sink=4,recent=64,
                selector_version_digest=hash_json(dict(condition_id=name,source_hashes=fs['source_hashes'],random_seed=20261028,window=64,kernel=5)),
                engineering_cases_required=2,required_paths=['native_whole','native_split','custom_split'] if full else ['native','custom'],compare_trace=not full)
            specs.append(spec);fp=condition_fingerprint(spec,runtime_digest)
            engplans=[plan_case(x['case_id'],x['prefix_tokens'],x['header_ids'],spec,runtime_digest) for x in eng]
            obs=[]
            for rawrow in full_eng if full else compact_eng:
                rawcondition=rawrow['condition']
                if full:
                    path=rawcondition
                elif rawcondition==name+'_native':path='native'
                elif rawcondition==name:path='custom' if rawrow['status']=='ok' else None
                else:continue
                x=next(x for x in eng if x['case_id']==rawrow['case_id'])
                require(rawrow['prompt_sha256']==x['prompt_sha256'],'engineering input hash')
                obs.append(dict(case_id=rawrow['case_id'],path=path,execution_state=rawrow['status'],condition_fingerprint=fp,
                    case_input_digest=rawrow['prompt_sha256'],ids=rawrow.get('ids'),trace=rawrow.get('trace'),truncated=rawrow.get('truncated')))
            evidence=engineering_evidence(spec,runtime_digest,engplans,obs);evidences.append(evidence)
            decisions=[];observed=[]
            for x in dev:
                p=plan_case(x['case_id'],x['prefix_tokens'],x['header_ids'],spec,runtime_digest)
                d=admission(p,evidence);original=history[(x['case_id'],name)]
                require(original['prompt_sha256']==x['prompt_sha256'],'DEV input hash')
                v=historical_observation(d,original);decisions.append(d);observed.append(v)
                rows.append(dict(case_plan=p,admission=d,historical=v,original_record_sha256=hash_json(original),origin='pinned archival record; no rescoring'))
            condition_reports[name]=dict(engineering_status=evidence['status'],engineering_verified=evidence['path_sequences_verified'],
                engineering_verified_cases=evidence['verified_engineering_cases'],engineering_infeasible_cases=evidence['infeasible_engineering_cases'],
                verified_sequence_but_truncated=evidence['sequence_verified_but_truncated_cases'],
                scheduled=len(dev),budget_feasible=sum(x['budget_state']=='ok' for x in decisions),
                future_admission_counts=dict(Counter(x['admission_state'] for x in decisions)),
                historical_generated=sum(x['actual_generated'] for x in observed),historical_generated_diagnostic_only=sum(x['historical_diagnostic_only'] for x in observed))
        expected=cfg['expected']
        actual=dict(main_cells=len(rows),mathematically_feasible=sum(x['case_plan']['budget']['state']=='ok' for x in rows),mathematically_infeasible=sum(x['case_plan']['budget']['state']=='infeasible_budget' for x in rows),
            future_eligible=sum(x['admission']['launch_allowed'] for x in rows),future_blocked_budget=sum(x['admission']['admission_state']=='blocked_budget' for x in rows),
            future_blocked_engineering_unverified=sum(x['admission']['admission_state']=='blocked_engineering_unverified' for x in rows),
            historical_generated=sum(x['historical']['actual_generated'] for x in rows),historical_generated_condition_unverified=sum(x['historical']['historical_diagnostic_only'] for x in rows),
            historical_not_generated_infeasible=sum(x['historical']['execution_state']=='infeasible_budget' for x in rows),verified_conditions=sum(x['path_sequences_verified'] for x in evidences),
            unverified_protected_conditions=sum(x['status']=='unverified_budget_infeasible' for x in evidences),engineering_sequence_verified_but_truncated_cases=sum(x['sequence_verified_but_truncated_cases'] for x in evidences))
        require(actual==expected,'frozen acceptance counts:'+str(actual))
        save(out/'condition_specs.json',dict(runtime_digest=runtime_digest,specs=specs))
        save(out/'engineering_evidence.json',evidences)
        (out/'admission_cells.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=True,allow_nan=False)+'\n' for x in rows))
        save(out/'report.json',dict(version='condition_admission_v1',actual=actual,conditions=condition_reports,
            preserved_legacy_task_report_sha256=cfg['inputs']['results/20261030-independent-development-analysis-v1/report.json'],
            legacy_scores_or_gates_rewritten=False,model_outputs=0,independent_confirmation=False))
        md=['# Condition admission and engineering evidence','','No model execution. Prospective strict policy is separate from preserved historical diagnostics.','','| Condition | Budget feasible /12 | Engineering evidence | Future eligible /12 | Historical generated | Diagnostic only |','| --- | --- | --- | --- | --- | --- |']
        for name,v in condition_reports.items():md.append(f"| {name} | {v['budget_feasible']} | {v['engineering_status']} | {v['future_admission_counts'].get('eligible_for_configured_run',0)} | {v['historical_generated']} | {v['historical_generated_diagnostic_only']} |")
        md+=['','A matching sequence at the decode cap establishes only tested-path numerical equality; one SnapKV engineering case was truncated. Protected paths had no feasible engineering cases, so the4archived protected DEV outputs remain diagnostic and future dispatch is blocked. Existing outputs and all prior scores/gates remain unchanged.']
        (out/'report.md').write_text('\n'.join(md)+'\n')
        for path,expected_hash in cfg['inputs'].items():require(sha((r/path).read_bytes())==expected_hash,'input changed')
        require(not any(x.split('.')[0] in ['torch','transformers','vllm'] for x in sys.modules),'model import')
        state.update(status='complete',stage='complete',input_files=len(bodies),input_bytes=size,jsonl_rows=lines,actual=actual,model_libraries_loaded=False,gpu_queried=False)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc));(out/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0);state['elapsed_seconds']=time.monotonic()-started;save(out/'summary.json',state)
        files=[p for p in out.iterdir() if p.is_file()];require(len(files)<32 and sum(p.stat().st_size for p in files)<8388608,'archive cap')
        save(out/'manifest.json',{p.name:sha(p.read_bytes()) for p in files});print(json.dumps(state),flush=True)
    return 0 if state['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
