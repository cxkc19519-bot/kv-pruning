"""Post-run stdlib audit; does not import the model, orchestrator or scorer."""
import sys
sys.dont_write_bytecode = True
import datetime
import gzip
import hashlib
import json
from pathlib import Path
from fractions import Fraction
from collections import Counter
import subprocess


def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(path.read_text())
def canonical(x): return sha(json.dumps(x, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2)+'\n')


def main():
    r = Path(__file__).resolve().parent.parent
    assert str(r) == '/home/user/jhk/project/Directional Exploration/kv-pruning'
    d = r/'results/20261030-hf-backend-engineering-v1'; cfg = read(d/'proposal_snapshot.json'); summary = read(d/'summary.json')
    assert summary['status'] == 'complete' and summary['raw_outputs'] == summary['engineering_outputs'] == 14 and summary['main_outputs'] == 0
    for name, expected in read(d/'manifest.json').items(): assert sha((d/name).read_bytes()) == expected, name
    for name, expected in cfg['inputs'].items(): assert sha((r/name).read_bytes()) == expected, name
    descriptor = read(d/'backend_execution_snapshot.json')
    for path, expected in descriptor['source_files'].items(): assert sha((r/path).read_bytes()) == expected, path
    scope = read(d/'registered_runtime_scope.json'); assert canonical(scope['material']) == scope['runtime_digest']
    assert scope['material']['proposal_sha256'] == sha((d/'proposal_snapshot.json').read_bytes())
    tokenized = read(r/cfg['tokenized']); source = {x['case_id']:x for x in map(json.loads, (r/cfg['cases']).read_text().splitlines())}
    cases = {x['case_id']:dict(x, context_group_id=source[x['case_id']]['context_group_id']) for x in tokenized}
    specs = {s['condition_id']:s for s in read(r/cfg['specs'])['specs']}
    bindings = {x['case_id']:x['case_input_digest'] for x in read(d/'prepared_bindings.json')}
    for cid, c in cases.items():
        assert bindings[cid] == canonical({k:c[k] for k in ['case_id','split_role','input_ids','prefix_tokens','header_ids','prompt_sha256','context_group_id']})
    old = {}
    for path, full in [(cfg['old_full_engineering'], True), (cfg['old_compact_engineering'], False)]:
        for x in map(json.loads, (r/path).read_text().splitlines()):
            if x['status'] != 'ok': continue
            name = x['condition']
            condition, branch = ('full', name) if full else (name[:-7], 'native') if name.endswith('_native') else (name, 'custom')
            old[(x['case_id'],condition,branch)] = x
    raw = list(map(json.loads, (d/'raw_engineering.jsonl').read_text().splitlines()))
    accepted = list(map(json.loads, (d/'accepted_engineering.jsonl').read_text().splitlines()))
    assert [x['result'] for x in accepted] == [x['result'] for x in raw]
    assert [x['request'] for x in map(json.loads, (d/'raw_engineering.jsonl').read_text().splitlines())] == list(map(json.loads, (d/'model_attempts.jsonl').read_text().splitlines()))
    got = {}; trace_steps = 0
    for row in raw:
        req, out = row['request'], row['result']; c = cases[req['case_id']]; spec = specs[req['condition_id']]
        key = (req['case_id'],req['condition_id'],req['path']); assert key not in got; got[key] = out
        assert req['phase'] == c['split_role'] == 'engineering' and req['case_id'] in cfg['engineering_case_ids']
        assert canonical({k:v for k,v in req.items() if k != 'request_digest'}) == out['request_digest'] == req['request_digest']
        assert req['case_input_digest'] == bindings[c['case_id']] and req['runtime_digest'] == scope['runtime_digest']
        fp = canonical(dict(version='condition_admission_v1',runtime_digest=scope['runtime_digest'],condition=spec))
        assert req['condition_fingerprint'] == fp
        prior = old[key]; assert out['ids'] == prior['ids'] and out['truncated'] == prior['truncated'] and out['trace'] == prior.get('trace')
        assert 0 < len(out['ids']) <= 128 and out['truncated'] == (out['ids'][-1] not in descriptor['decode']['eos_token_id'])
        n = c['prefix_tokens']; physical = n if req['condition_id'] == 'full' else n//2; suffix = len(c['input_ids'])-n
        if req['path'] == 'native_whole': assert out['actual_prefix_kv_bytes'] is None and out['final_live_kv_bytes'] is None
        else:
            assert out['actual_prefix_kv_bytes'] == physical*57344
            if out['trace'] is not None:
                assert len(out['trace']) == len(out['ids'])
                for i, entry in enumerate(out['trace']):
                    width = suffix if i == 0 else 1; logical = n if i == 0 else n+suffix+i-1
                    assert entry == dict(step=i,physical_start=physical,logical_start=logical,input_width=width)
                    physical += width; trace_steps += 1
            else: physical += suffix+len(out['ids'])-1
            assert out['final_live_kv_bytes'] == physical*57344
    assert set(got) == set(old) and sum(len(x['ids']) for x in got.values()) == summary['generated_tokens'] == 605
    # Compare actual archived maps/scores with immutable prior archives, then independently rank Snap scores.
    mapping_heads = 0; snap_rankings = 0
    for cid in cfg['engineering_case_ids']:
        c = cases[cid]; n = c['prefix_tokens']; olddir = r/'results/20261030-independent-squad-compression-v1'
        oldmanifest = read(olddir/'manifest.json')
        for suffix in ('.maps.json.gz','.scores.json.gz'):
            p = olddir/(cid+suffix); assert sha(p.read_bytes()) == oldmanifest[p.name]
        scores = json.loads(gzip.decompress((d/(cid+'.scores.json.gz')).read_bytes()))
        assert scores == json.loads(gzip.decompress((olddir/(cid+'.scores.json.gz')).read_bytes()))
        oldmaps = json.loads(gzip.decompress((olddir/(cid+'.maps.json.gz')).read_bytes()))
        required = set(range(min(4,n))) | set(range(max(0,n-64),n))
        for condition in ('adapted_snapkv','uniform_random'):
            maps = json.loads(gzip.decompress((d/(cid+'.'+condition+'.maps.json.gz')).read_bytes()))
            assert maps == oldmaps[condition] and set(maps) == {str(i) for i in range(28)}
            for layer, batches in maps.items():
                assert len(batches) == 1 and len(batches[0]) == 4
                for head, indices in enumerate(batches[0]):
                    assert len(indices) == n//2 and indices == sorted(set(indices)) and required <= set(indices) and all(0 <= p < n for p in indices)
                    mapping_heads += 1
                    if condition == 'adapted_snapkv':
                        values = scores[layer][0][head]; free = [i for i in range(n) if i not in required]
                        extra = sorted(free, key=lambda p:(-values[p],p))[:n//2-len(required)]
                        assert indices == sorted(required|set(extra)); snap_rankings += 1
    evidence = {x['condition_id']:x for x in read(d/'engineering_evidence.json')}
    for name, spec in specs.items():
        feasible = []
        for cid in cfg['engineering_case_ids']:
            c = cases[cid]; n = c['prefix_tokens']; ratio = Fraction(spec['retention']); slots = n*ratio.numerator//ratio.denominator
            required = set(range(min(4,n))) | set(range(max(0,n-64),n)) | (set(c['header_ids']) if spec['protect_system'] else set())
            feasible.append(len(required) <= slots)
            if feasible[-1]:
                outputs = [got[(cid,name,p)] for p in spec['required_paths']]
                assert all(x['ids'] == outputs[0]['ids'] and x['truncated'] == outputs[0]['truncated'] for x in outputs)
                if spec['compare_trace']: assert all(x['trace'] == outputs[0]['trace'] for x in outputs)
        assert evidence[name]['status'] == ('verified' if all(feasible) else 'unverified_budget_infeasible')
    assert len(read(d/'blocked_engineering.json')) == 4
    decisions = read(d/'DEV_admission_only.json'); expected_counts = Counter()
    for item in decisions:
        req = item['request']; c = cases[req['case_id']]; spec = specs[req['condition_id']]; n = c['prefix_tokens']; ratio = Fraction(spec['retention'])
        assert c['split_role'] == 'development'
        required = set(range(min(4,n))) | set(range(max(0,n-64),n)) | (set(c['header_ids']) if spec['protect_system'] else set())
        expected = 'blocked_budget' if len(required) > n*ratio.numerator//ratio.denominator else 'blocked_engineering_unverified' if spec['protect_system'] else 'eligible_for_configured_run'
        assert item['decision']['admission_state'] == expected; expected_counts[expected] += 1
    assert len(decisions) == 60 and expected_counts == {'eligible_for_configured_run':36,'blocked_budget':20,'blocked_engineering_unverified':4}
    runtime = read(d/'actual_runtime.json'); assert runtime['observed']['runtime_Full_layers'] == 28 and runtime['observed']['KV_heads'] == 4 and runtime['actual_attention_heads'] == 28
    assert runtime['model_parameter_dtypes'] == ['torch.bfloat16'] and not runtime['tf32_matmul'] and not runtime['tf32_cudnn']
    verified = {}
    for name, expected in {**descriptor['model_metadata_files'], **descriptor['weights']}.items():
        h = hashlib.sha256()
        with (Path(descriptor['model_path'])/name).open('rb') as f:
            for chunk in iter(lambda:f.read(8388608),b''): h.update(chunk)
        assert h.hexdigest() == expected; verified[name] = h.hexdigest()
    launch = read(Path(str(d)+'.launch.json')); assert launch['exit_code'] == 0 and not launch.get('watchdog_expired',False)
    assert not Path('/proc/'+str(summary['pid'])).exists() and not Path('/proc/'+str(launch['launcher_pid'])).exists()
    gpu = subprocess.run(['nvidia-smi','-i',descriptor['gpu_uuid'],'--query-gpu=uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15).stdout.strip()
    value = dict(status='passed',checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__).read_bytes()),input_files_unchanged=len(cfg['inputs']),all14_request_input_runtime_bindings_checked=True,all14_new_old_tokens_termination_trace_equal=True,raw_and_accepted_outputs=14,generated_tokens=605,independent_position_trace_steps=trace_steps,unique_layer_head_maps_checked=mapping_heads,independent_Snap_rankings=snap_rankings,new_old_scores_and_maps_equal=True,verified_conditions=3,protected_unverified_conditions=2,budget_blocked_engineering=4,DEV_decisions=dict(expected_counts),DEV_model_calls=0,sealed_model_calls=0,model_metadata_and_weights_rehashed=verified,own_worker_and_launcher_exited=True,gpu_after_raw=gpu,new_scientific_confirmation=False)
    save(d/'independent_verification.json',value)
    print(json.dumps({k:v for k,v in value.items() if k != 'model_metadata_and_weights_rehashed'}),flush=True)


if __name__ == '__main__': main()
