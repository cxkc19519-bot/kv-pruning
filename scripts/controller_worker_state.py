"""Trusted offline worker control only; snapshots stay inside the worker.

The caller must verify no unfinished frontend requests before each RPC. The
worker additionally requires an empty request map. Not a general KV/model/RNG
checkpoint; handles controller state plus the idle request-slot allocation order.
"""
import copy
import hashlib
import types


EST = ('slope','intercepts','features','predictions','info','grad','counts')
ADAPT = ('_confidence_probs','_batch_draft_capacity','_num_non_draft_tokens',
         '_cu_num_logits','query_start_loc')


class ControllerHistoryWorkerExtension:
    """Named offline RPC avoids serializing Python callables over engine IPC."""
    def controller_history_control(self,operation,key='common',enabled=False):
        return control(self,operation,key,enabled)


def _training_step(self,*args,**kwargs):
    if not self._controller_frozen:
        return self._controller_original_step(*args,**kwargs)


def _objects(worker):
    import torch
    mr=worker.model_runner
    assert type(mr).__module__=='vllm.v1.worker.gpu.model_runner','Require MRV2'
    spec=mr.speculator
    assert type(spec).__name__=='StandaloneARSpeculator'
    est=spec.acceptance_estimator;av=mr.adaptive_verification
    assert est is not None and av is not None,'Both controllers must exist'
    assert not mr.req_states.req_id_to_index,'Worker request state has not drained'
    assert not mr.req_states.index_to_req_id
    av._copy_stream.synchronize()
    for event in av._copy_events:event.synchronize()
    torch.cuda.synchronize()
    return mr,spec,est,av


def _tensors(spec,est,av):
    t={'est.'+n:getattr(est,n) for n in EST}
    t.update({'av.'+n:getattr(av,n) for n in ADAPT})
    t['spec.confidence']=spec.draft_token_confidence_probs
    for i,b in enumerate(av._stale_confidences):
        t[f'av.stale{i}.cpu']=b.cpu;t[f'av.stale{i}.gpu']=b.gpu
    return t


def _small(mr,est,av):
    return dict(phase=est._steps_since_refit,refits=est._refits,
                frozen=getattr(est,'_controller_frozen',False),
                stale_idx=av._stale_idx,pending_resets=copy.deepcopy(av._pending_resets),
                batch_budget=copy.deepcopy(av._batch_budget),
                cudagraph_limit=av._cudagraph_limit,
                free_indices=list(mr.req_states.free_indices))


def _digest(tensors,small,cost):
    import pickle
    h=hashlib.sha256()
    for n,t in sorted(tensors.items()):
        x=t.detach().cpu().contiguous()
        h.update(n.encode());h.update(str((x.dtype,tuple(x.shape))).encode());h.update(x.numpy().tobytes())
    h.update(pickle.dumps(small,protocol=4))
    if cost is not None:
        for x in cost:h.update(x.tobytes())
    return h.hexdigest()


def _learning_digest(est):
    return _digest({n:getattr(est,n) for n in ('slope','intercepts','info','grad','counts')},
                   dict(phase=est._steps_since_refit,refits=est._refits),None)


def control(worker,operation,key='common',enabled=False):
    import torch
    mr,spec,est,av=_objects(worker)
    tensors=_tensors(spec,est,av)
    if not hasattr(worker,'_controller_snapshots'):worker._controller_snapshots={}
    if not hasattr(est,'_controller_original_step'):
        est._controller_original_step=est.step
        est._controller_frozen=False
        est.step=types.MethodType(_training_step,est)
    if operation=='inspect':
        specs=mr.get_kv_cache_spec()
        assert len(specs)==64,(len(specs),'Expected target36+draft28')
        assert all(type(x).__name__=='FullAttentionSpec' for x in specs.values())
        return dict(worker=type(worker).__name__,runner=type(mr).__name__,
                    speculator=type(spec).__name__,kv_layers=len(specs),
                    kv_types=sorted(set(type(x).__name__ for x in specs.values())),
                    reqs=len(mr.req_states.req_id_to_index),
                    tensor_names=sorted(tensors),cost_tables=av.cost_tables is not None)
    if operation=='save':
        worker._controller_snapshots[key]=dict(tensors={n:t.detach().cpu().clone() for n,t in tensors.items()},
             small=_small(mr,est,av),cost=copy.deepcopy(av.cost_tables),
             addresses={n:t.data_ptr() for n,t in tensors.items()})
    elif operation=='restore':
        snap=worker._controller_snapshots[key]
        assert snap['addresses']=={n:t.data_ptr() for n,t in tensors.items()}
        for n,t in tensors.items():t.copy_(snap['tensors'][n])
        s=snap['small'];est._steps_since_refit=s['phase'];est._refits=s['refits']
        est._controller_frozen=s['frozen'];av._stale_idx=s['stale_idx']
        av._pending_resets[:]=s['pending_resets'];av._batch_budget=copy.deepcopy(s['batch_budget'])
        av._cudagraph_limit=s['cudagraph_limit'];mr.req_states.free_indices[:]=s['free_indices']
        av.cost_tables=copy.deepcopy(snap['cost'])
        torch.cuda.synchronize()
        with torch.cuda.stream(av._copy_stream):
            for event in av._copy_events:event.record(av._copy_stream)
        av._copy_stream.synchronize()
    elif operation=='mutate':
        for t in tensors.values():t.fill_(0.125 if t.is_floating_point() else 7)
        est._steps_since_refit=(est._steps_since_refit+13)%100;est._refits+=1
        av._stale_idx^=1;av._pending_resets[:]=[0];av._batch_budget=None
        if av.cost_tables is not None:
            for c in av.cost_tables:c.fill(3.0)
        mr.req_states.free_indices.reverse()
    elif operation=='boundary':
        # Explicit synthetic engineering fixture, not a natural history result.
        est._steps_since_refit=95
    elif operation=='warm_refit':
        est._steps_since_refit=99
        z=torch.empty(0,device=est.device,dtype=torch.int32)
        est.step(z,z,z)
    elif operation=='freeze':est._controller_frozen=enabled
    elif operation not in ('status','save'):raise ValueError(operation)
    torch.cuda.synchronize()
    small=_small(mr,est,av)
    return dict(operation=operation,digest=_digest(tensors,small,av.cost_tables),
                learning_digest=_learning_digest(est),phase=small['phase'],refits=small['refits'],
                frozen=small['frozen'],slope=est.slope.item(),intercepts=est.intercepts.cpu().tolist(),
                stale_idx=small['stale_idx'],pending_resets=small['pending_resets'],
                tensor_addresses={n:t.data_ptr() for n,t in tensors.items()})
