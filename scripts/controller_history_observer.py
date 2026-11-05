"""Bounded worker-side observation of the pinned native controller.

No replacement of prediction, fitting or allocation. Synchronous trace reads
make this unsuitable for latency measurement. All wrappers call native methods
once, preserve their return values, and are installed after engine warmup.
"""
import hashlib
import json
from pathlib import Path
import types

from controller_worker_state import (
    ControllerHistoryWorkerExtension, _objects, control,
)


def _list(t):
    return t.detach().cpu().tolist()


class Observer:
    def __init__(self,worker,mr,est,av):
        self.worker,self.mr,self.est,self.av=worker,mr,est,av
        self.active=False
        self.stream=None
        self.events=0
        self.total_events=0
        self.counts={}
        self.old_get=av.get_num_tokens
        self.old_allocate=av.reallocate_drafts
        self.old_step=est.step
        obs=self

        def get(avself,num_tokens_per_req,draft_tokens):
            result=obs.old_get(num_tokens_per_req,draft_tokens)
            if obs.active:
                ids=list(num_tokens_per_req)
                slots=[mr.req_states.req_id_to_index[k] for k in ids]
                batch=avself._batch_budget
                assert batch is not None
                obs.write('budget',request_ids=ids,slots=slots,
                    scheduled_tokens=list(num_tokens_per_req.values()),
                    scheduled_drafts=[len(draft_tokens.get(k,())) for k in ids],
                    non_draft_tokens=[batch[1][k] for k in ids],
                    selected_draft_budget=int(batch[2]),total_tokens=int(result),
                    stale_idx=avself._stale_idx,
                    stale_confidences=avself._stale_confidences[avself._stale_idx].np[slots].tolist(),
                    phase=est._steps_since_refit,refits=est._refits)
            return result

        def allocate(avself,req_ids,idx_mapping):
            result=obs.old_allocate(req_ids,idx_mapping)
            if obs.active:
                n=len(req_ids)
                caps=_list(avself._batch_draft_capacity[:n])
                assert sum(caps)==int(result[2])
                obs.write('allocation',request_ids=list(req_ids),slots=_list(idx_mapping),
                    capacities=caps,selected_draft_budget=int(result[2]),
                    cu_num_logits=_list(result[0]),query_start_loc=_list(result[1][:n+1]),
                    phase=est._steps_since_refit,refits=est._refits)
            return result

        def step(estself,idx_mapping,num_sampled,num_rejected):
            if not obs.active:
                return obs.old_step(idx_mapping,num_sampled,num_rejected)
            slots=_list(idx_mapping)
            sampled,rejected=_list(num_sampled),_list(num_rejected)
            phase,refits=estself._steps_since_refit,estself._refits
            # Read features before native update and before the next propose.
            features=_list(estself.features[idx_mapping])
            predictions=_list(estself.predictions[idx_mapping])
            result=obs.old_step(idx_mapping,num_sampled,num_rejected)
            obs.write('verification',slots=slots,num_sampled=sampled,num_rejected=rejected,
                num_accepted=[max(int(v)-1,0) for v in sampled],features=features,
                predictions=predictions,phase_before=phase,refits_before=refits,
                phase_after=estself._steps_since_refit,refits_after=estself._refits,
                frozen=estself._controller_frozen,counts_after=_list(estself.counts),
                slope_after=estself.slope.item(),intercepts_after=_list(estself.intercepts))
            return result

        av.get_num_tokens=types.MethodType(get,av)
        av.reallocate_drafts=types.MethodType(allocate,av)
        est.step=types.MethodType(step,est)

    def write(self,event,**values):
        assert self.active and self.stream is not None
        self.events+=1;self.total_events+=1
        assert self.events<=512 and self.total_events<=12000,'Trace bound exceeded'
        self.counts[event]=self.counts.get(event,0)+1
        self.stream.write(json.dumps(dict(event=event,index=self.events,**values),allow_nan=False)+'\n')
        self.stream.flush()


class ControllerNaturalHistoryExtension(ControllerHistoryWorkerExtension):
    def controller_history_trace(self,operation,label='',path=''):
        mr,spec,est,av=_objects(self)
        if operation=='install':
            assert not hasattr(self,'_history_observer')
            assert hasattr(est,'_controller_original_step'),'Call inspect first'
            self._history_observer=Observer(self,mr,est,av)
            return dict(installed=True,active=False)
        obs=self._history_observer
        if operation=='begin':
            assert not obs.active and obs.stream is None
            p=Path(path).resolve();root=Path(__file__).resolve().parents[1]
            assert p.parent.parent==root/'results' and not p.is_symlink()
            obs.stream=p.open('x');obs.events=0;obs.counts={};obs.active=True
            obs.label=label
            return dict(active=True,label=label,path=str(p))
        if operation=='end':
            assert obs.active
            obs.active=False;obs.stream.close();obs.stream=None
            return dict(label=obs.label,events=obs.events,counts=dict(obs.counts),total_events=obs.total_events)
        raise ValueError(operation)

    def controller_history_detail(self):
        mr,spec,est,av=_objects(self)
        status=control(self,'status')
        return dict(status=status,info=_list(est.info),grad=_list(est.grad),counts=_list(est.counts),
                    features=_list(est.features),predictions=_list(est.predictions),
                    cost_tables=[x.tolist() for x in av.cost_tables],
                    cost_sha256=hashlib.sha256(b''.join(x.tobytes() for x in av.cost_tables)).hexdigest())
