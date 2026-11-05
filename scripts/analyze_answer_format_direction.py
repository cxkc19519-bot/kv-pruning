"""Scalar paired report and preregistered triage; stdlib, no model imports."""
import sys
sys.dont_write_bytecode=True
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
import traceback


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=True,allow_nan=False,indent=2)+'\n')
def check(x,s):
    if not x:raise ValueError(s)


def valid(row,metric):
    return row is not None and row['status']=='ok' and not row.get('truncated',False) and type(row['metrics'].get(metric)) is bool


def paired(full,method,metric):
    transitions={k:0 for k in ['C2C','C2W','W2C','W2W','N/A']};den=eligible=unknown=0
    for cid,base in full.items():
        row=method.get(cid);basegood=valid(base,metric)
        if basegood and base['metrics'][metric]:den+=1
        if basegood and valid(row,metric):
            transitions[('C' if base['metrics'][metric] else 'W')+'2'+('C' if row['metrics'][metric] else 'W')]+=1
            if base['metrics'][metric]:eligible+=1
        else:
            transitions['N/A']+=1
            if basegood and base['metrics'][metric]:unknown+=1
    damaged=transitions['C2W']
    return dict(transitions=transitions,all_available_Full_correct=den,eligible_Full_correct=eligible,
        unassessed_Full_correct=unknown,strict_conditional_damage=damaged/eligible if eligible else None,
        all_Full_correct_damage_bounds=[damaged/den,(damaged+unknown)/den] if den else None,
        bounds_are_not_confidence_interval=True)


def unique(rows):
    result={}
    for row in rows:
        key=(row['case_id'],row['condition']);check(key not in result,'duplicate_cell');result[key]=row
    return result


def software_checks():
    def row(em,fmt=True,truncated=False):return dict(status='ok',truncated=truncated,metrics=dict(em=em,format=fmt))
    outputs=[]
    p=paired({'a':row(True),'b':row(False)},{'a':row(False),'b':row(True)},'em')
    check(p['transitions']['C2W']==p['transitions']['W2C']==1 and p['strict_conditional_damage']==1,'damage_improvement');outputs.append(dict(id='paired_net_zero',status='pass',actual=p))
    p=paired({'a':row(True)},{'a':row(None,False)},'em')
    check(p['unassessed_Full_correct']==1 and p['strict_conditional_damage'] is None and p['all_Full_correct_damage_bounds']==[0,1],'N/A coverage');outputs.append(dict(id='unassessed_not_success',status='pass',actual=p))
    p=paired({'a':row(False)},{'a':row(True)},'em')
    check(p['all_Full_correct_damage_bounds'] is None and p['transitions']['W2C']==1,'zero denominator');outputs.append(dict(id='zero_denominator',status='pass',actual=p))
    p=paired({'a':row(True)},{'a':row(True,True,True)},'em')
    check(p['transitions']['N/A']==1 and p['unassessed_Full_correct']==1,'truncated exclusion');outputs.append(dict(id='truncation',status='pass',actual=p))
    p=paired({'a':row(True)},{},'format')
    check(p['unassessed_Full_correct']==1,'missing cell');outputs.append(dict(id='missing_cell',status='pass',actual=p))
    try:unique([dict(case_id='a',condition='m')]*2)
    except ValueError as exc:check(str(exc)=='duplicate_cell','duplicate error')
    else:raise ValueError('duplicate not rejected')
    outputs.append(dict(id='duplicate_hard_rejection',status='pass'))
    return outputs


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--proposal',required=True);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    r=Path(__file__).resolve().parent.parent;check(a.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning','server explicit execute')
    cfg=json.loads((r/a.proposal).read_text());out=r/cfg['run'];check(out.resolve().parent==(r/'results').resolve(),'boundary');out.mkdir(exist_ok=False)
    start=time.monotonic();state=dict(status='running',main_outputs=0,engineering_outputs=0,model_loaded=False,gpu_queried=False)
    try:
        (out/'proposal_snapshot.json').write_bytes((r/a.proposal).read_bytes());(out/'source.py').write_bytes(Path(__file__).read_bytes())
        for p,h in cfg['inputs'].items():check(sha(r/p)==h,'input pin:'+p)
        fixtures=software_checks();save(out/'software_fixtures.json',fixtures)
        for rootname in ['full','compression']:
            src=r/cfg[rootname];m=json.loads((src/'manifest.json').read_text())
            for name,h in m.items():check(sha(src/name)==h,'manifest:'+rootname+name)
        fullrows=[json.loads(x) for x in (r/cfg['full']/'generations.jsonl').read_text().splitlines()]
        compressed=[json.loads(x) for x in (r/cfg['compression']/'generations.jsonl').read_text().splitlines()] if (r/cfg['compression']/'generations.jsonl').exists() else []
        allcells=unique(fullrows+compressed);full={x['case_id']:x for x in fullrows}
        check(len(full)==16,'Full count')
        contract=json.loads((r/cfg['decision_contract']).read_text());methods=contract['compression']['methods']
        check(all(x['condition'] in ['full']+methods for x in fullrows+compressed),'unknown condition')
        from answer_format_task import score_response
        for row in fullrows+compressed:
            if row['status']!='ok':continue
            base=full[row['case_id']];check(row['prompt_sha256']==base['prompt_sha256'] and row['gold_sha256']==base['gold_sha256'],'case identity')
            check(row['prefix_tokens']==base['prefix_tokens'],'prefix identity')
            if row['condition']!='full':check(row['prefix_kv_bytes']==(base['prefix_tokens']//2)*57344,'actual equal budget')
        cases={x['case_id']:x for x in map(json.loads,(r/cfg['cases']).read_text().splitlines())}
        for row in fullrows+compressed:
            if row['status']=='ok':check(score_response(row['text'],[x['text'] for x in cases[row['case_id']]['answers']])==row['metrics'],'rescore mismatch')
        metrics={};planned=[]
        for method in ['full']+methods:
            by={cid:allcells.get((cid,method)) for cid in full};ok=[x for x in by.values() if x and x['status']=='ok'];good=[x for x in ok if not x['truncated']]
            for cid,row in by.items():planned.append(dict(case_id=cid,condition=method,status=row['status'] if row else 'not_run',truncated=row.get('truncated') if row else None,candidate_status=row['metrics']['candidate_status'] if row and row['status']=='ok' else None))
            f1=[x['metrics']['f1'] for x in good if x['metrics']['f1'] is not None]
            metrics[method]=dict(scheduled=16,ok=len(ok),not_run=sum(x is None for x in by.values()),errors=sum(x is not None and x['status']!='ok' for x in by.values()),truncated=sum(x['truncated'] for x in ok),task_em=sum(x['metrics']['em'] is True for x in good),format=sum(x['metrics']['format'] for x in good),joint=sum(x['metrics']['joint_success'] for x in good),task_candidate_available=sum(x['metrics']['candidate_status']=='available' for x in good),f1_mean=sum(f1)/len(f1) if f1 else None,f1_denominator=len(f1),paired_em=paired(full,by,'em'),paired_format=paired(full,by,'format'))
        complete=len(compressed)==64 and all(metrics[m]['ok']==16 and metrics[m]['truncated']==0 and metrics[m]['task_candidate_available']==16 for m in methods) and all(valid(x,'em') and valid(x,'format') for x in full.values())
        gate=contract['dev_signal_gate'];families=[]
        for m in ['adapted_snapkv','uniform_random']:
            pin=m+'_system_pinned';damage=metrics[m]['paired_format']['transitions']['C2W'];recovered=0
            for cid,b in full.items():
                x=allcells.get((cid,m));y=allcells.get((cid,pin))
                if all(valid(z,'format') for z in [b,x,y]) and b['metrics']['format'] and not x['metrics']['format'] and y['metrics']['format']:recovered+=1
            netdrop=metrics[m]['task_em']-metrics[pin]['task_em']
            passed=complete and damage>=gate['min_format_C2W_in_at_least_one_unpinned_method'] and recovered>=gate['min_same_method_format_failures_recovered_by_paid_system_protection'] and netdrop<=gate['max_task_EM_net_drop_protected_vs_same_unpinned']
            families.append(dict(unpinned=m,format_damage=damage,format_recovered_by_paid_protection=recovered,task_em_net_drop_with_protection=netdrop,signal_gate=passed))
        passed=any(x['signal_gate'] for x in families)
        report=dict(scope=contract['scope'],conditions=metrics,complete_comparable_DEV=complete,families=families,DEV_signal_gate=passed,decision=contract['conclusions']['dev_signal_gate_pass' if passed else 'dev_signal_gate_fail'],independent_confirmation_run=False,new_algorithm_or_safety_claim=False,planned_cells=planned)
        save(out/'report.json',report)
        text=['# Fixed reading+JSON half-KV DEV decision','',report['decision'],'','| Condition | EM /16 | Format /16 | F1 mean | EM damaged/improved | Format damaged/improved |','| --- | --- | --- | --- | --- | --- |']
        for m,c in metrics.items():
            e=c['paired_em']['transitions'];f=c['paired_format']['transitions'];text.append(f"| {m} | {c['task_em']} | {c['format']} | {c['f1_mean']} | {e['C2W']}/{e['W2C']} | {f['C2W']}/{f['W2C']} |")
        text+=['','All scheduled cells and N/A/truncation denominators are in report.json. Bounds are coverage bounds, not confidence intervals. No long-context, safety, novelty or degree-adequacy conclusion.']
        (out/'report.md').write_text('\n'.join(text)+'\n')
        state.update(status='complete',software_fixtures=6,DEV_signal_gate=passed,complete_comparable_DEV=complete,decision=report['decision'])
    except BaseException as exc:
        state.update(status='failed',error=repr(exc));(out/'failure.txt').write_text(traceback.format_exc())
    finally:
        state['elapsed_seconds']=time.monotonic()-start;save(out/'summary.json',state)
        files=[p for p in out.iterdir() if p.is_file()];check(len(files)<32 and sum(p.stat().st_size for p in files)<33554432,'archive cap')
        save(out/'manifest.json',{p.name:sha(p) for p in files});print(json.dumps(state),flush=True)
    return 0 if state['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
