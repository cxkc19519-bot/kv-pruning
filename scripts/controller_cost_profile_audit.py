"""Server stdlib audit: read pinned source and reconstruct profiling geometry.

Never imports vLLM/torch, loads weights, executes author code or queries a GPU.
Geometry predictions are conditional on the audited source and fixed config;
they are not runtime measurements or cost-accuracy validation.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import time
import traceback

PINS={
 'v1/worker/gpu/spec_decode/adaptive_verification.py':'5f91af59e5924bfb89b0c6cc0b6eb62e02010d06',
 'v1/worker/gpu/model_runner.py':'57cef586f81fd48337bf43a437c392127ecc1a6b',
 'v1/worker/gpu/input_batch.py':'bd55a43f64123ff55e10eee912ac9029f4cd251b',
 'v1/worker/gpu/async_utils.py':'0d6481585e21b11d4cb6ad61a105de0648f94e7f',
 'v1/worker/gpu/cudagraph_utils.py':'73be62319a64bfd8e0986811fdfce1a0e3914123',
 'v1/worker/gpu_worker.py':'04feb5da025a6072f100eaba485baefe74247aaa',
 'config/vllm.py':'f27c8418ab4df614a32affb9b34a30ac6f734604',
 'config/compilation.py':'7a16e3d6a046aa7c59f3007983cc3fe291612944',
 'v1/worker/gpu/spec_decode/standalone_ar/speculator.py':'bd404ef38fd958263f3e29f53a2aa641003f170b',
 'envs.py':'a2b46030772f3845009fd837b5b55f6df1d11641'}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')


def geometry(captured):
    # Independent scalar reconstruction of the reviewed fixed-config path.
    size=captured[-1];tail={min(size+size//2,512)}
    while size<512:
        size=min(size*2,512);tail.add(size)
    points=captured+sorted(tail-set(captured));rows=[]
    for requested in points:
        n=min(requested,2)
        actual=min(requested,512-n)  # Standalone AR needs one extra slot/request.
        full=actual<=10 and actual in captured
        promised_query=5 if full else math.ceil(actual/n)
        context=max(min(8192,512-promised_query),0)
        split=[actual//n+int(i>=n-actual%n) for i in range(n)]
        rows.append(dict(requested_tokens=requested,actual_tokens=actual,num_reqs=n,
            split=split,full_cudagraph=full,promised_query_len=promised_query,
            clipped_context=context,actual_seq_lens=[context+q for q in split],repeats=5))
    return rows


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-dir',required=True);a=ap.parse_args()
    root=Path(__file__).resolve().parents[1];out=Path(a.run_dir).resolve()
    assert out.parent==root/'results';out.mkdir(exist_ok=False)
    start=time.monotonic();s=dict(status='running',pid=os.getpid(),main_outputs=0,
        engineering_answers=0,author_code_executed=False,model_loaded=False,gpu_queried=False)
    def timeout(*_):raise TimeoutError('60 second audit bound')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(60)
    try:
        proposal=root/'configs/controller-cost-profile-audit-v1.json'
        cfg=json.loads(proposal.read_text());prior=root/cfg['prior_run']
        assert sha(prior/'manifest.json')==cfg['prior_manifest_sha256']
        (out/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
        (out/'proposal_snapshot.json').write_bytes(proposal.read_bytes())
        execution=dict(cfg,execution_enabled=True,runner_sha256=sha(Path(__file__)))
        save(out/'execution_snapshot.json',execution)
        site=root/'.venv-controller-history/lib/python3.11/site-packages/vllm';checks={}
        for name,expected in PINS.items():
            raw=(site/name).read_bytes();actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            assert actual==expected
            dest=out/'upstream'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
            checks[name]=dict(expected_blob=expected,actual_blob=actual,sha256=sha(dest),match=True)
        save(out/'source_checks.json',checks)
        candidates=sorted(set([1,2,4]+list(range(8,21,8))+[5,10]))
        assert candidates==[1,2,4,5,8,10,16]
        default_captured=[x for x in candidates if x<=2*5]
        old=geometry([5,10]);default=geometry(default_captured)
        assert len(old)==9 and len(default)==13 and len(old)+len(default)<=32
        assert [r['requested_tokens'] for r in old]==[5,10,15,20,40,80,160,320,512]
        assert [r['clipped_context'] for r in old]==[507,507,504,502,492,472,432,352,257]
        assert all(r['num_reqs']==2 for r in old)
        assert sum(r['repeats'] for r in old)==45 and sum(r['repeats'] for r in default)==65
        assert {r['num_reqs'] for r in old if r['full_cudagraph']}=={2}
        assert {r['num_reqs'] for r in default if r['full_cudagraph']}=={1,2}
        analysis=json.loads((prior/'independent_analysis.json').read_text())
        assert analysis['native_costs']['draft_N1']==analysis['native_costs']['draft_N2']
        summary=json.loads((prior/'summary.json').read_text());draft,verify=summary['boundaries']['common']['cost_tables']
        assert len(set(verify[1:6]))==1
        answers=[json.loads(l) for l in (prior/'answers.jsonl').read_text().splitlines()]
        bounds=[len(x['prompt_ids'])+len(x['token_ids']) for x in answers]
        # Data-key scan, excluding copied Python source: final tables are not raw samples.
        found=[]
        def walk(x,path):
            if isinstance(x,dict):
                for k,v in x.items():
                    if k in ['forward_ms','drafter_ms']:found.append(dict(file=path,key=k))
                    walk(v,path)
            elif isinstance(x,list):
                for v in x:walk(v,path)
        for p in prior.glob('*.json'):walk(json.loads(p.read_text()),p.name)
        for p in prior.glob('*.jsonl'):
            for line in p.read_text().splitlines():walk(json.loads(line),p.name)
        assert not found
        # Full entropy can be larger despite much larger max-q.
        h_peaked=math.log(2)+0.5*math.log(151936-1)
        h_uniform=math.log(417)
        assert h_peaked>h_uniform and 0.5>1/417
        save(out/'geometry.json',dict(original=old,default_candidates=candidates,
            predicted_default_captured=default_captured,default_profile=default,
            original_draft_measured_request_keys=[2],default_predicted_draft_keys=[1,2],
            original_N1_draft_entry='snapped from first measured key N2; no dedicated N1 sample',
            original_requested_context=8192,graph_context_clamped_to=507,
            raw_timing_sample_keys_found=found,observed_logical_length_bound_range=[min(bounds),max(bounds)],
            entropy_counterexample=dict(V=151936,peaked_max_q=0.5,peaked_entropy_nats=h_peaked,
                uniform_support=417,uniform_max_q=1/417,uniform_entropy_nats=h_uniform)))
        s.update(status='complete',source_blobs_matched=len(checks),original_profile_shapes=9,
            original_dummy_steps_per_collection=45,original_draft_measured_keys=[2],
            default_predicted_profile_shapes=13,default_predicted_dummy_steps_per_collection=65,
            default_predicted_draft_keys=[1,2],raw_timing_recoverable=False,
            cost_table_semantics_explained=True,cost_accuracy_validated=False,
            normal_low_max_q_coverage_established=False,new_GPU_history_trial_ready=False,
            next_stage='Disabled two-answer raw profile measurement validation, not harm screening')
    except BaseException as exc:
        s.update(status='failed',error=repr(exc));(out/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0);s['elapsed_seconds']=time.monotonic()-start;save(out/'summary.json',s)
        save(out/'manifest.json',{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
        print(json.dumps(s,indent=2),flush=True)
    return 0 if s['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
