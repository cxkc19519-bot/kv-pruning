"""Eager, single-worker SDPA observation. No torch import or tensor-value reads.

Metadata/sink/marker errors are recorded without replacing an original result or
exception. Callers must reject observation evidence when ``errors`` is nonempty.
Profiler lineage is read from supplied event objects, never guessed from timing.
"""
from contextlib import nullcontext
import functools
import threading

_owners = {}
_lock = threading.RLock()
_names = ('query', 'key', 'value', 'attn_mask', 'dropout_p', 'is_causal')
_backend_ops = {
    'aten::_scaled_dot_product_flash_attention': 'flash',
    'aten::_scaled_dot_product_efficient_attention': 'efficient',
    'aten::_scaled_dot_product_attention_math': 'math',
    'aten::_scaled_dot_product_cudnn_attention': 'cudnn',
}


def tensor_metadata(value):
    if value is None:
        return None
    shape = list(value.shape)
    if not all(type(i) is int for i in shape):
        raise TypeError('symbolic_shape_not_supported')
    return dict(shape=shape, stride=list(value.stride()), dtype=str(value.dtype), device=str(value.device))


def scalar_metadata(value):
    return value if type(value) in (str, bool, int, float, type(None)) else dict(type=type(value).__name__)


class SDPAObserver:
    def __init__(self, target, attribute='scaled_dot_product_attention', sink=None, marker_factory=None, max_records=4096):
        if type(max_records) is not int or max_records < 1:
            raise ValueError('max_records')
        self.target, self.attribute = target, attribute
        self.sink, self.marker_factory = sink, marker_factory
        self.max_records, self.calls = max_records, 0
        self.records, self.errors = [], []
        self.active, self.original, self.wrapper = False, None, None

    def error(self, code, error=None):
        detail = code if error is None else code + ':' + type(error).__name__
        if detail not in self.errors and len(self.errors) < 16:
            self.errors.append(detail)

    def emit(self, row):
        if len(self.records) >= self.max_records:
            self.error('record_limit_exceeded')
            return
        self.records.append(row)
        if self.sink is not None:
            try:
                self.sink(row)
            except Exception as error:
                self.error('sink_error', error)

    def describe(self, args, kwargs, call):
        supplied = dict(zip(_names, args[:6]))
        supplied.update(kwargs)
        row = dict(call=call, marker='kv_sdpa_' + str(call).zfill(7),
                   positional_count=len(args), keyword_order=list(kwargs),
                   supplied_names=list(_names[:min(6,len(args))]) + list(kwargs), status='attempted')
        for name in _names[:4]:
            try:
                row[name] = tensor_metadata(supplied.get(name))
            except Exception as error:
                row[name] = dict(metadata_error=type(error).__name__)
                self.error('metadata_error', error)
        for name, default in [('dropout_p',0.),('is_causal',False),('scale',None),('enable_gqa',False)]:
            row[name] = scalar_metadata(supplied.get(name,default))
        row['mask_is_none'] = supplied.get('attn_mask') is None
        return row

    def __enter__(self):
        key = (id(self.target),self.attribute)
        with _lock:
            if self.active or key in _owners:
                raise RuntimeError('observer_target_already_owned')
            original = getattr(self.target,self.attribute)
            if not callable(original):
                raise TypeError('target_not_callable')
            self.original = original

            @functools.wraps(original)
            def wrapped(*args,**kwargs):
                self.calls += 1
                row = self.describe(args,kwargs,self.calls)
                marker, entered = nullcontext(), False
                try:
                    if self.marker_factory is not None:
                        marker = self.marker_factory(row['marker'])
                    marker.__enter__()
                    entered = True
                except Exception as error:
                    self.error('marker_enter_error',error)
                try:
                    result = original(*args,**kwargs)
                except BaseException as error:
                    row.update(status='original_exception',exception_type=type(error).__name__)
                    if entered:
                        try:
                            marker.__exit__(type(error),error,error.__traceback__)
                        except Exception as marker_error:
                            self.error('marker_exit_error',marker_error)
                    self.emit(row)
                    raise
                else:
                    if entered:
                        try:
                            marker.__exit__(None,None,None)
                        except Exception as error:
                            self.error('marker_exit_error',error)
                    row['status'] = 'returned'
                    self.emit(row)
                    return result

            self.wrapper = wrapped
            setattr(self.target,self.attribute,wrapped)
            _owners[key] = self
            self.active = True
        return self

    def __exit__(self,exc_type,exc,tb):
        key = (id(self.target),self.attribute)
        with _lock:
            conflict = getattr(self.target,self.attribute) is not self.wrapper
            if not conflict:
                setattr(self.target,self.attribute,self.original)
            else:
                self.error('target_replaced_by_foreign_owner')
            if _owners.get(key) is self:
                del _owners[key]
            self.active = False
        if conflict and exc_type is None:
            raise RuntimeError('observer_restore_ownership_conflict')
        return False


def profiler_inventory(events):
    """Summarize supplied FunctionEvent-like objects under marker parent chains.

    Exact backend operator names are labels; raw kernel names remain available.
    No parent lineage means unassigned evidence, never a timing-based association.
    """
    events = list(events)
    markers = {id(e):dict(marker=e.name,event_id=e.id,backend_operators=[],kernels=[]) for e in events
               if e.name.startswith('kv_sdpa_')}
    unassigned = []
    for event in events:
        node,seen,marker = event,set(),None
        while node is not None:
            if id(node) in seen or len(seen) >= 256:
                raise ValueError('profiler_parent_cycle_or_depth')
            seen.add(id(node))
            if id(node) in markers:
                marker=markers[id(node)]
                break
            node=getattr(node,'cpu_parent',None)
        backend = _backend_ops.get(event.name)
        kernels = [dict(name=k.name,device=k.device,owner_event_id=event.id,owner_operator=event.name)
                   for k in getattr(event,'kernels',[])]
        if marker is not None:
            if backend is not None:
                marker['backend_operators'].append(dict(name=event.name,family=backend,event_id=event.id))
            marker['kernels'].extend(kernels)
        elif backend is not None or kernels:
            unassigned.append(dict(name=event.name,event_id=event.id,backend_family=backend,kernels=kernels))
    return dict(markers=sorted(markers.values(),key=lambda m:m['event_id']),unassigned_events=unassigned,
                association='explicit_cpu_parent_lineage_only',deduplicated_or_summed_kernel_durations=False)
