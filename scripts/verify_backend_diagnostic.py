"""Independent raw byte, call-count and aggregate watchdog evidence verifier."""
import hashlib
import json
from pathlib import Path
import sys


def need(value, reason):
    if not value:
        raise AssertionError(reason)


def verify(out):
    for name, digest in json.loads((out / 'worker_manifest.json').read_text()).items():
        path = (out / name).resolve()
        need(path.is_relative_to(out), 'manifest_boundary')
        need(hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'artifact_hash:' + name)
    cfg = json.loads((out / 'registration_snapshot.json').read_text())
    draft = json.loads((out / 'input_legacy-backend-diagnostic-draft-v1.json').read_text())
    processes = json.loads((out / 'processes.json').read_text())
    need([p['backend'] for p in processes] == ['llguidance', 'xgrammar'], 'backend_order')
    eventsets = {}
    for process in processes:
        backend = process['backend']
        rows = [json.loads(line) for line in (out / (backend + '-events.jsonl')).read_text().splitlines()]
        need(rows and rows[0]['event'] == 'guard_installed', 'guard_evidence')
        need(len(rows[0]['affinity']) <= 2, 'CPU_affinity')
        for i, row in enumerate(rows):
            need(row['seq'] == i+1 and row['backend'] == backend, 'event_sequence')
            need(row['pid'] == process['pid'] and row['starttime'] == process['starttime'], 'PID_identity')
            if i:
                need(row['ns'] >= rows[i-1]['ns'], 'monotonic_clock')
        need(not process['identity_present_after_wait'], 'process_not_reaped')
        eventsets[backend] = rows
    data = json.loads((out / 'llguidance-byte-evidence.json').read_text())
    need(data['constructor'] == dict(vocab_size=257,eos_id=256,special_ids=[256],slices=[]), 'original_constructor')
    need([r['token'] for r in data['single']] == list(range(257)), 'all257_single_ids')
    need([r['token'] for r in data['special']] == list(range(257)), 'all257_special_ids')
    mismatches = []
    errors = []
    for row in data['single']:
        token = row['token']
        expected = bytes([token]) if token < 256 else b'<|eos|>'
        if row['error']:
            errors.append(token)
            continue
        need(row['input_hex'] == expected.hex(), 'token_input')
        if row['actual_hex'] is not None:
            actual = bytes.fromhex(row['actual_hex'])
            need(len(actual) == row['actual_length'] and (actual == expected) == row['normalized_equals_input'], 'byte_evidence')
            if actual != expected:
                mismatches.append(token)
    full = data['full']
    need(full['input_hex'] == bytes(range(256)).hex(), 'full_original_input')
    first = None
    if full.get('actual_hex') is not None:
        actual = bytes.fromhex(full['actual_hex'])
        expected = bytes(range(256))
        first = next((i for i in range(max(len(actual),len(expected)))
                      if i>=len(actual) or i>=len(expected) or actual[i]!=expected[i]), None)
        need(first == full['first_difference'] and len(actual)==full['actual_length'], 'full_difference')
        if not errors and all(r.get('actual_hex') is not None for r in data['single'][:256]):
            need(actual == b''.join(bytes.fromhex(r['actual_hex']) for r in data['single'][:256]), 'concat_single_full')
    need([p['input_hex'] for p in data['encoder_probes']] == draft['llguidance_diagnostic']['tokenize_byte_probes_hex'], 'encode_probe_inputs')
    for p in data['encoder_probes']:
        if not p['error']:
            need(all(isinstance(t,int) and 0<=t<=256 for t in p['returned_tokens']), 'encode_id_range')
    ll = eventsets['llguidance']
    starts = [r for r in ll if r['event']=='call_begin']
    ends = [r for r in ll if r['event']=='call_end']
    need(len(starts)==len(ends)==data['public_calls']==520, 'all520_calls')
    for a,b in zip(starts,ends):
        need(a['call_id']==b['call_id'] and a['kind']==b['kind'] and a['ns']<=b['ns'], 'call_pair')
    for event, records in [('single_byte_evidence',data['single']),('special_evidence',data['special']),('encoder_evidence',data['encoder_probes'])]:
        need([r['evidence'] for r in ll if r['event']==event]==records, 'immediate_evidence:' + event)
    need([r['evidence'] for r in ll if r['event']=='full_byte_evidence']==[full], 'immediate_full')
    prediction = (data['single'][255].get('actual_hex')=='' and data['special'][255]['actual'] is True
                  and full.get('actual_length')==255 and first==255)
    x = eventsets['xgrammar']
    begins = [r for r in x if r['event']=='aggregate_import_begin']
    ended = [r for r in x if r['event']=='aggregate_import_end']
    need(len(begins)==1 and len(ended)<=1 and begins[0]['deadline_ns']==5_000_000_000, 'single_aggregate_clock')
    checkpoints = [r for r in x if r['event'] in draft['xgrammar_import_diagnostic']['checkpoints']]
    names = [r['event'] for r in checkpoints]
    need(names == draft['xgrammar_import_diagnostic']['checkpoints'][:len(names)], 'checkpoint_prefix')
    xp = processes[1]
    stack = (out / 'xgrammar-stacks.txt').read_text()
    need(len(stack.encode())<=524288, 'stack_cap')
    if xp.get('aggregate_deadline'):
        need(not ended and xp['exit_code']==-9, 'timeout_censoring')
        need(xp['watchdog_ns']-begins[0]['ns']>=5_000_000_000, 'no_early_or_reset_timeout')
        need(stack, 'timed_out_without_stack')
    elif ended:
        need(xp['exit_code']==0, 'completed_import_exit')
    else:
        need(xp['exit_code']!=0 and any(r['event']=='worker_complete' and r['status']=='failed' for r in x), 'missing_failure_evidence')
    report = dict(status='complete', diagnostic_evidence_verified=True,
                  llguidance=dict(public_calls=520, byte_mismatch_ids=mismatches, decode_error_ids=errors,
                    full_actual_length=full.get('actual_length'), first_difference=first,
                    special_ids=[r['token'] for r in data['special'] if r['actual']],
                    source_prediction_confirmed=prediction,
                    return_types=sorted({r.get('return_type','error') for r in data['single']})),
                  xgrammar=dict(checkpoints=names, import_completed=bool(ended),
                    phase_within_original_deadline=bool(ended and ended[0]['ns']-begins[0]['ns']<=5_000_000_000),
                    aggregate_timeout=xp.get('aggregate_deadline',False),
                    observed_phase_ns=(ended[0]['ns'] if ended else xp.get('watchdog_ns',x[-1]['ns']))-begins[0]['ns'],
                    stack_snapshots=stack.count('Timeout ('),
                    immediate_guard_blocks=[r for r in x if r['event']=='guard_block']),
                  finite_semantic_gate=False, schema_calls=0, mask_calls=0, labeled_instances=0,
                  qualification='diagnostic completion does not pass the original semantic gate')
    save = out / 'independent_verification.json'
    with save.open('x') as stream:
        json.dump(report,stream,indent=2,sort_keys=True)
        stream.write('\n')
    print(json.dumps(report))


if __name__=='__main__':
    verify(Path(sys.argv[1]).resolve())
