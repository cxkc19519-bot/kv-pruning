"""Bounded native estimator check; server only, no model or serving worker.

Tests installed predict/accumulate/refit kernels and estimator-only in-place
restore. Adaptive-verification buffers and worker RPC remain out of scope.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import time
import traceback


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-dir', required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    run = Path(args.run_dir).resolve()
    assert run.parent == root / 'results'
    run.mkdir(exist_ok=False)
    state = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
                 pid=os.getpid(), model_outputs=0, engineering_answers=0,
                 scope='Native estimator only; not worker/async-buffer restore',
                 atol=1e-4, rtol=1e-4, max_seconds=180, max_step_calls=256)
    started = time.monotonic()
    (run / 'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (run / 'execution_snapshot.json').write_text(json.dumps(dict(
        execution_enabled=True, model_load_enabled=False, gpu='physical GPU 1',
        max_seconds=180, max_step_calls=256, max_requests=8, draft_steps=4,
        synthetic_vocab=128, cpu_reference_sha256=
        '2e7e9c2c6d4ac9cc49a717f56c244b6609aa80a8fa7fcc59cd75f63936a43c81',
        expected_estimator_blob='f7a4a2f2c1e3221407d12c70cc067cc8cc045bd1',
        measured_latency=False, authorization='user_start_next_step'), indent=2)+'\n')
    def timeout(*_):
        raise TimeoutError('180 second native check limit')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(180)
    try:
        import torch
        from vllm.v1.worker.gpu.spec_decode import acceptance_estimator as upstream
        from controller_history_preflight import Reference, sigmoid
        raw = Path(upstream.__file__).read_bytes()
        blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert blob == 'f7a4a2f2c1e3221407d12c70cc067cc8cc045bd1'
        reference_path = root / 'scripts/controller_history_preflight.py'
        assert hashlib.sha256(reference_path.read_bytes()).hexdigest() == state_ref_sha()
        torch.cuda.set_device(0)
        torch.cuda.set_per_process_memory_fraction(0.03, 0)
        state.update(torch=torch.__version__, cuda=torch.version.cuda,
                     device=torch.cuda.get_device_name(0),
                     capability=list(torch.cuda.get_device_capability(0)))
        est = upstream.OnlineAcceptanceEstimator(8, 4, torch.device('cuda:0'))
        names = ['slope', 'intercepts', 'features', 'predictions', 'info', 'grad', 'counts']
        def snapshot():
            torch.cuda.synchronize()
            return {**{n:getattr(est,n).clone() for n in names},
                    '_steps_since_refit': est._steps_since_refit, '_refits': est._refits}
        def restore(s):
            torch.cuda.synchronize()
            for n in names:
                getattr(est,n).copy_(s[n])
            est._steps_since_refit=s['_steps_since_refit']
            est._refits=s['_refits']
            torch.cuda.synchronize()
        def exact(a,b):
            return all(torch.equal(a[n],b[n]) for n in names) and all(
                a[n]==b[n] for n in ['_steps_since_refit','_refits'])
        pointers = {n:getattr(est,n).data_ptr() for n in names}
        clean = snapshot()
        mapping = torch.arange(8, device='cuda', dtype=torch.int32)
        temp = torch.ones(8, device='cuda')
        confidence = torch.empty(8,4,device='cuda')
        calls=0
        ref=Reference()
        worst=dict(feature=0.0,prediction=0.0,reference=0.0)
        traces=[]
        def advance(t, reference=True):
            nonlocal calls
            rows=[]
            for slot in range(8):
                x=[((t*7+slot*3+k*5)%29-14)/7 for k in range(4)]
                accepted=(t+slot)%5
                admitted=4 if accepted==4 else min(4,accepted+1+(t%2))
                rows.append(dict(slot=slot,features=x,accepted=accepted,admitted=admitted))
            for k in range(4):
                logits=torch.zeros(8,128,device='cuda')
                logits[:,0]=torch.tensor([math.log(127)+r['features'][k] for r in rows],device='cuda')
                est.predict(logits,mapping,torch.tensor(k,device='cuda',dtype=torch.int32),confidence,temp)
            torch.cuda.synchronize()
            expected_x=torch.tensor([r['features'] for r in rows])
            expected_p=torch.sigmoid(est.slope.cpu()*expected_x+est.intercepts.cpu())
            torch.testing.assert_close(est.features.cpu(),expected_x,atol=1e-5,rtol=1e-5)
            torch.testing.assert_close(confidence.cpu(),expected_p,atol=1e-5,rtol=1e-5)
            worst['feature']=max(worst['feature'],(est.features.cpu()-expected_x).abs().max().item())
            worst['prediction']=max(worst['prediction'],(confidence.cpu()-expected_p).abs().max().item())
            sampled=torch.tensor([r['accepted']+1 for r in rows],device='cuda',dtype=torch.int32)
            rejected=torch.tensor([r['admitted']-r['accepted'] for r in rows],device='cuda',dtype=torch.int32)
            est.step(mapping,sampled,rejected);calls+=1
            assert calls<=256
            if reference: ref.step(rows)
        def compare_ref():
            s=ref.s
            expected=dict(slope=[s['slope']],intercepts=s['bias'],features=s['features'],
                          predictions=s['predictions'],info=s['info'],grad=s['grad'],counts=s['counts'])
            for n,v in expected.items():
                actual=getattr(est,n).cpu();target=torch.tensor(v,dtype=actual.dtype)
                torch.testing.assert_close(actual,target,atol=1e-4,rtol=1e-4)
                worst['reference']=max(worst['reference'],(actual-target).abs().max().item())
            assert est._steps_since_refit==s['phase'] and est._refits==s['refits']
            traces.append(dict(calls=calls,phase=s['phase'],slope=est.slope.item(),
                               intercepts=est.intercepts.cpu().tolist()))
        # Compile all three paths once, then restore the common clean state.
        est._steps_since_refit=99
        advance(0,False)
        restore(clean)
        for t in range(105):
            advance(t)
            if t==94: checkpoint=snapshot()
            if t in [0,94,98,99,104]: compare_ref()
        endpoint=snapshot()
        restore(checkpoint)
        for t in range(95,105): advance(t,False)
        assert exact(snapshot(),endpoint), 'Native estimator full-state replay mismatch'
        state['native_estimator_replay_exact']=True
        # Preserve the negative control: theta alone leaves phase/statistics wrong.
        for n in ['slope','intercepts']:getattr(est,n).copy_(checkpoint[n])
        for t in range(95,105):advance(t,False)
        assert not exact(snapshot(),endpoint)
        state['theta_only_negative_control_detected']=True
        restore(clean)
        est._steps_since_refit=99
        empty=torch.empty(0,device='cuda',dtype=torch.int32)
        est.step(empty,empty,empty);calls+=1
        torch.cuda.synchronize()
        assert est._steps_since_refit==0 and est._refits==1
        assert all(torch.equal(getattr(est,n),clean[n]) for n in names)
        assert pointers=={n:getattr(est,n).data_ptr() for n in names}
        state.update(status='pass', step_calls=calls, worst_abs_difference=worst,
                     empty_refit_pass=True, tensor_addresses_preserved=True,
                     peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                     peak_reserved_bytes=torch.cuda.max_memory_reserved(), checkpoints=traces)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc))
        (run/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0)
        state.update(elapsed_seconds=time.monotonic()-started,
                     finished_utc=datetime.now(timezone.utc).isoformat())
        (run/'summary.json').write_text(json.dumps(state,indent=2)+'\n')
        (run/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in run.iterdir() if p.is_file()},indent=2)+'\n')
        print(json.dumps(state,indent=2),flush=True)
    return 0 if state['status']=='pass' else 1


def state_ref_sha():
    return '2e7e9c2c6d4ac9cc49a717f56c244b6609aa80a8fa7fcc59cd75f63936a43c81'


if __name__=='__main__':
    raise SystemExit(main())
