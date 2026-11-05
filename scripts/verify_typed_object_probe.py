"""Independent stdlib reconstruction of42 finite-domain semantic outcomes."""
import hashlib
import json
from pathlib import Path
import sys


def need(value,reason):
    if not value:raise AssertionError(reason)


def verify(out):
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for name,digest in json.loads((out/'worker_manifest.json').read_text()).items():
        p=(out/name).resolve();need(p.is_relative_to(out) and sha(p)==digest,'manifest:'+name)
    cfg=json.loads((out/'registration_snapshot.json').read_text());mapping=json.loads((out/'snapshot-map.json').read_text())
    need(len(set(mapping.values()))==len(mapping) and set(mapping)==set(cfg['input_sha256']),'input_snapshot_map')
    for name,saved in mapping.items():need(sha(out/saved)==cfg['input_sha256'][name],'input_binding')
    selection=json.loads((out/mapping[cfg['selection']]).read_text())
    raw_groups=json.loads((out/mapping[cfg['raw_groups']]).read_text())
    need([json.loads(raw) for raw in raw_groups]==selection['cases'] and len(raw_groups)==3,'unchanged8_schemas')
    need(selection['widths']==[1,2,4] and len(selection['cases'])==3,'prospective_widths')
    for width,case in zip([1,2,4],selection['cases']):
        names=['k%03d'%i for i in range(width)]
        required_schema={'type':'object','properties':{k:{'type':'string','enum':['red','blue']} for k in names},'required':names,'additionalProperties':False}
        need(case['schema']==required_schema and case['case_id']=='typed-record-w'+str(width),'typed_schema_exact')
        need([t['description'] for t in case['tests']]==['all_red','alternating','missing_key','extra_key','wrong_enum','wrong_value_type','wrong_root_type'],'prospective_fixture_ids')
        truth=[]
        for test in case['tests']:
            value=test['data']
            valid=isinstance(value,dict) and set(value.keys())==set(names) and all(isinstance(x,str) and (x=='red' or x=='blue') for x in value.values())
            need(test['valid'] is valid,'independent_business_oracle')
            truth.append(valid)
        need(truth==[True,True,False,False,False,False,False],'positive_negative_balance')
    expected=[]
    for backend in ['xgrammar','llguidance']:
        for gi,case in enumerate(selection['cases']):
            for ti,test in enumerate(case['tests']):
                text=json.dumps(test['data'],ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False)
                expected.append(dict(backend=backend,case_id=case['case_id'],test_index=ti,
                    expected=test['valid'],serialized=text,tokens=list(text.encode('ascii'))+[133]))
    need(len(expected)==42 and json.loads((out/mapping[cfg['inventory']]).read_text())==expected,'frozen42_slots')
    process=json.loads((out/'worker-process.json').read_text());owner=[process['worker_pid'],process['worker_starttime']]
    rows=[json.loads(l) for l in (out/'events.jsonl').read_text().splitlines()]
    for i,row in enumerate(rows):
        need(row['seq']==i+1 and [row['owner_pid'],row['owner_starttime']]==owner,'event_owner_sequence')
        need(row['ns']>=process['spawn_ns'] and (not i or row['ns']>=rows[i-1]['ns']),'event_clock')
    ws=out/'worker-status.json';status=json.loads(ws.read_text()) if ws.exists() else None
    complete=status is not None and status['status']=='complete' and process['worker_exit_code']==0
    active=None;pending=None;call_ends={};begins={};groups={};ready=None;setup_end=None;timing=[]
    for row in rows:
        event=row['event']
        if event=='library_import_ready':
            ready=row['ns'];need(not row['cuda_initialized'],'cuda_ready');need(ready-process['spawn_ns']<30_000_000_000,'startup30')
        if event=='adapter_setup_begin':
            need(ready is not None and row['deadline_ns']==ready+5_000_000_000,'setup5_origin');active=row['deadline_ns']
        if event=='adapter_setup_complete':
            setup_end=row['ns'];need(row['deadline_ns']==active and setup_end<active and setup_end-process['spawn_ns']<30_000_000_000,'setup5_and_total30');active=None
        if event=='group_submitted':
            need(setup_end is not None and active is None,'no_compile_in_startup')
            key=(row['backend'],row['group_index']);need(key not in groups,'duplicate_group')
            need(row['payload_sha256']==hashlib.sha256(raw_groups[key[1]].encode()).hexdigest(),'raw_payload')
            groups[key]=dict(start=row['ns'],end=None,deadline=row['ns']+5_000_000_000)
            pending=key
        if event=='group_deadline':
            key=(row['backend'],row['group_index']);need(key==pending,'group_assignment')
            need(row['origin_ns']==groups[key]['start'] and row['deadline_ns']==groups[key]['deadline'],'shared_group5')
            active=row['deadline_ns']
        if event=='group_complete':
            key=(row['backend'],row['group_index']);need(row['deadline_ns']==active==groups[key]['deadline'],'no_group_reset')
            need(row['ns']<active,'group_finished_by5');groups[key]['end']=row['ns'];active=None;pending=None
        if event=='call_begin':
            cid=row['call_id'];need(cid==len(begins)+1 and cid not in begins,'call_ids')
            need(row['deadline_ns']==active and row['ns']<active,'call_budget_origin')
            if row['kind'] in ('schema_compile','schema_convert'):
                need(row['context']['phase']=='schema_group' and pending is not None,'schema_after_submission')
            begins[cid]=row
        if event=='call_end':
            cid=row['call_id'];need(cid in begins and cid not in call_ends,'call_end_identity')
            need(row['kind']==begins[cid]['kind'] and row['context']==begins[cid]['context'],'call_context')
            need(row['ns']>=begins[cid]['ns'],'call_clock')
            if row['ns']>=begins[cid]['deadline_ns']:timing.append(cid)
            call_ends[cid]=row
    need(len(begins)<=7516,'call_cap')
    if complete:
        need(len(begins)==len(call_ends) and not timing,'all_calls_closed_in_time')
        need(list(groups)==[(b,i) for b in ['xgrammar','llguidance'] for i in range(3)],'all16_groups_in_order')
        need(all(g['end'] is not None for g in groups.values()),'all_groups_closed')
        need(status['cuda_initialized'] is False and not status['readiness_live'],'final_cuda_expired')
        need(not any(status['boundary_counts'][k] for k in ('file_denied','process_denied','network_denied','forbidden_imports')),'final_guards')
    actual_rows=[json.loads(l) for l in (out/'instances.jsonl').read_text().splitlines()] if (out/'instances.jsonl').exists() else []
    actual={};position_rows={}
    for row in actual_rows:
        key=(row['backend'],row['group_index'],row['test_index']);need(key not in actual,'duplicate_instance');actual[key]=row
    masks=[json.loads(l) for l in (out/'masks.jsonl').read_text().splitlines()] if (out/'masks.jsonl').exists() else []
    need(len(masks)<=1186,'mask_position_cap')
    for m in masks:
        key=(m['backend'],m['group_index'],m['test_index']);position_rows.setdefault(key,[]).append(m)
        raw=bytes.fromhex(m['raw_hex']);need(17<=len(raw)<=64,'mask_byte_bounds')
        if m['backend']=='xgrammar':
            need(len(raw)==20 and len(m['words'])==5,'five_int32_words')
            packed=sum((v&0xffffffff)<<(32*i) for i,v in enumerate(m['words'])).to_bytes(20,'little')
            need(raw==packed,'word_bytes_independent')
        else:
            bias=bytes.fromhex(m.get('bias_hex',''))
            if actual.get(key,{}).get('status')=='complete':
                need(134<=len(bias)<=256 and all(v in (0,200) for v in bias[:134]),'bias_bounds')
                value=int.from_bytes(raw,'little')
                need(all(bool((value>>i)&1)==(bias[i]==200) for i in range(134)),'ll_bias_bit_crosscheck')
        if m['allowed'] is not None:
            need(m['allowed']==bool((int.from_bytes(raw,'little')>>m['token'])&1),'bit_decision_recomputed')
        if m.get('mask_call_id'):
            call=begins[m['mask_call_id']];need(call['kind']==('x_mask' if m['backend']=='xgrammar' else 'll_mask'),'mask_call_link')
        if m['commit_result'] is not None:
            need(m['allowed'] and begins[m['commit_call_id']]['kind']=='commit','commit_only_allowed')
    outcomes=[];summaries={}
    for backend in ['xgrammar','llguidance']:
        summaries[backend]=dict(total=21,known=0,matches=0,tp=0,tn=0,fp=0,fn=0,unknown=0,eos_accepted=0)
    for slot in expected:
        backend=slot['backend'];gi=next(i for i,c in enumerate(selection['cases']) if c['case_id']==slot['case_id'])
        key=(backend,gi,slot['test_index']);actual_row=actual.pop(key,None)
        outcome=dict(slot,status='not_executed_or_censored',accepted=None,matches_label=None)
        steps=position_rows.pop(key,[])
        if actual_row is not None:
            need(actual_row['case_id']==slot['case_id'] and actual_row['expected']==slot['expected'],'gold_identity')
            need(actual_row['steps']==len(steps),'step_count')
            outcome.update(status=actual_row['status'])
            if 'error' in actual_row:outcome['error']=actual_row['error']
            if 'warnings' in actual_row:outcome['warnings']=actual_row['warnings']
            if actual_row['status']=='complete':
                need(actual_row['serialized']==slot['serialized'] and actual_row['tokens']==slot['tokens'],'normalization_unchanged')
                need(steps,'nonempty_complete_trace')
                for pos,m in enumerate(steps):
                    need(m['position']==pos and m['token']==slot['tokens'][pos],'mask_position_token')
                    if pos<len(steps)-1:need(m['allowed'] and m['commit_result'] is True,'accepted_prefix')
                accepted=(len(steps)==len(slot['tokens']) and all(m['allowed'] and m['commit_result'] is True for m in steps))
                if accepted:
                    terminal=actual_row['terminal'];need(steps[-1]['token']==133 and terminal['stopped'],'explicit_eos_stop')
                    if backend=='llguidance':need(terminal['error'] is False,'ll_terminal_error')
                    outcome['terminal']=terminal;summaries[backend]['eos_accepted']+=1
                else:
                    need(steps[-1]['allowed'] is False and steps[-1]['commit_result'] is None,'rejection_mask')
                need(actual_row['accepted']==accepted and actual_row['matches_label']==(accepted==slot['expected']),'outcome_reconstructed')
                outcome.update(accepted=accepted,matches_label=accepted==slot['expected'])
        result=summaries[backend]
        if outcome['accepted'] is None:result['unknown']+=1
        else:
            result['known']+=1;result['matches']+=int(outcome['matches_label'])
            result['tp' if outcome['accepted'] and slot['expected'] else 'fp' if outcome['accepted'] else 'fn' if slot['expected'] else 'tn']+=1
        outcomes.append(outcome)
    need(not actual and not position_rows,'no_unplanned_slots')
    kinds={}
    for c in begins.values():kinds[c['kind']]=kinds.get(c['kind'],0)+1
    mask_api=sum(kinds.get(k,0) for k in ['x_mask','ll_mask','ll_bias'])
    need(mask_api<=1779 and kinds.get('commit',0)<=1186 and kinds.get('matcher_init',0)<=42,'operation_caps')
    if complete:
        need(len(actual_rows)==42,'all42_attempt_results')
        need([(r['backend'],r['case_id'],r['test_index']) for r in actual_rows]==[(r['backend'],r['case_id'],r['test_index']) for r in expected],'all42_in_original_order')
        need(kinds.get('schema_compile',0)==kinds.get('schema_convert',0)==3,'exact3_schemas_each')
        need(status['counters']==dict(schema_specs=6,matcher_constructions=kinds.get('matcher_init',0),
            mask_positions=kinds.get('x_mask',0)+kinds.get('ll_mask',0),mask_api_calls=mask_api,commit_calls=kinds.get('commit',0)),'independent_counters')
    paired=[(outcomes[i],outcomes[i+21]) for i in range(21)]
    agreement=sum(a['accepted']==b['accepted'] for a,b in paired if a['accepted'] is not None and b['accepted'] is not None)
    known_pairs=sum(a['accepted'] is not None and b['accepted'] is not None for a,b in paired)
    gate=complete and all(s['matches']==21 and s['unknown']==0 for s in summaries.values())
    report=dict(status='complete',worker_completed=complete,typed_object_semantic_gate=gate,summaries=summaries,
                known_pairs=known_pairs,backend_agreement=agreement,mask_positions=len(masks),mask_api_calls=mask_api,
                commit_calls=kinds.get('commit',0),native_boundaries=len(begins),timing_violations=timing,
                group_budget_seconds=5,request_SLO_claim=False,old_cold5_gate=False,old_ff_identity_gate=False,
                old_257_semantic_gate=False,readiness_live=False,resource_effects_measured=False,
                startup_ns=None if ready is None else ready-process['spawn_ns'],
                setup_ns=None if ready is None or setup_end is None else setup_end-ready)
    (out/'semantic-results.json').write_text(json.dumps(outcomes,sort_keys=True,indent=2)+'\n')
    (out/'independent_verification.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':verify(Path(sys.argv[1]).resolve())
