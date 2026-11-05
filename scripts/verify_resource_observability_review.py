"""Stdlib-only reanalysis of archived native timings and source provenance."""
import ast
import hashlib
import json
from pathlib import Path
import sys


def main():
    root=Path(__file__).resolve().parents[1]
    source=root/'literature/20261102-resource-observability-review-v1'
    run=root/'results/20261102-typed-object-semantic-v1'
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(source/'manifest.json')=='635371e581a964d66205548f773f694b9369b7d7834b92c30f6226d475043dd4'
    assert sha(run/'manifest.json')=='494acca21215720b2aeea96cdbde1fcc15b044a513b39e89bb2a2f365aaba5d3'
    for folder in [source,run]:
        for name,digest in json.loads((folder/'manifest.json').read_text()).items():
            p=(folder/name).resolve();assert p.is_relative_to(folder) and sha(p)==digest
    for item in json.loads((source/'sources.json').read_text()):
        assert item['status']=='ok'
        raw=(source/item['snapshot']).read_bytes()
        assert sha(source/item['snapshot'])==item['sha256']
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==item['git_blob_sha1']
    rows=[json.loads(l) for l in (run/'events.jsonl').read_text().splitlines()]
    starts={r['call_id']:r for r in rows if r['event']=='call_begin'}
    ends={r['call_id']:r for r in rows if r['event']=='call_end'}
    samples=[json.loads(l) for l in (run/'process-samples.jsonl').read_text().splitlines()]
    expected={}
    durations={}
    for cid,start in starts.items():
        if start['kind'] not in ['schema_compile','schema_convert','matcher_init','x_mask','ll_mask']:continue
        end=ends[cid];key=start['context'].get('backend','setup')+':'+start['kind']
        delta=end['ns']-start['ns'];assert delta>=0
        durations.setdefault(key,[]).append(delta)
        expected.setdefault(key,[]).append(dict(call_id=cid,begin_ns=start['ns'],end_ns=end['ns'],duration_ns=delta))
    assert json.loads((source/'call-spans.json').read_text())==expected
    original=json.loads((source/'analysis.json').read_text());assert original['external_samples']==len(samples)==250
    for key,values in durations.items():
        values.sort();span=expected[key]
        two=sum(sum(s['ns']>=r['begin_ns'] and s['ns']<=r['end_ns'] for s in samples)>=2 for r in span)
        assert original['phase_summaries'][key]==dict(count=len(values),min_ns=values[0],median_ns=values[len(values)//2],max_ns=values[-1],calls_with_two_internal_external_samples=two,cpu_per_call_identifiable=False)
    latest_stub=source/'ll__python__llguidance___lib.pyi'
    functions=[n.name for n in ast.walk(ast.parse(latest_stub.read_text())) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    cancel_methods=[n for n in functions if 'cancel' in n.lower()]
    assert not cancel_methods
    report=dict(status='complete',backend_executions_added=0,experimental_runs_added=0,
                call_spans_verified=sum(map(len,durations.values())),max_selected_call_span_ns=max(map(max,durations.values())),
                external_samples=250,all_selected_calls_have_two_external_samples=False,
                selected_calls_with_two_external_samples=sum(v['calls_with_two_internal_external_samples'] for v in original['phase_summaries'].values()),
                cpu_tick_ns=10000000,latest_ll_python_cancel_methods=cancel_methods,
                same_slot_recovery_tested=False,cancellation_tested=False,scientific_gap_established=False)
    dest=root/'literature/20261102-resource-observability-verification-v1';dest.mkdir(exist_ok=False)
    (dest/'source_verifier.py').write_bytes(Path(__file__).read_bytes())
    (dest/'verification.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    mapping={p.name:sha(p) for p in dest.iterdir()}
    (dest/'manifest.json').write_text(json.dumps(mapping,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(report,manifest_sha256=sha(dest/'manifest.json'))))


if __name__=='__main__':main()
