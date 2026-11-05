"""CPU-only observer identity/exception tests and finalization fault cases."""
import sys
sys.dont_write_bytecode=True
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace


class TensorStub:
    dtype='torch.bfloat16'
    device='cuda:0'
    def __init__(self,shape):self.shape=tuple(shape)
    def stride(self):
        result=[];running=1
        for n in reversed(self.shape):result.insert(0,running);running*=n
        return tuple(result)
    def forbidden(self,*a,**k):raise AssertionError('tensor_value_operation_forbidden')
    cpu=clone=detach=numpy=to=float=item=__iter__=__bool__=forbidden


class BrokenMetadata(TensorStub):
    @property
    def shape(self):raise RuntimeError('descriptor_broken')
    def __init__(self):pass


class Marker:
    def __init__(self,events,label,enter_fail=False,exit_fail=False):
        self.events,self.label,self.enter_fail,self.exit_fail=events,label,enter_fail,exit_fail
    def __enter__(self):
        self.events.append(dict(action='enter',label=self.label))
        if self.enter_fail:raise RuntimeError('marker_enter')
        return self
    def __exit__(self,kind,value,tb):
        self.events.append(dict(action='exit',label=self.label,exception=None if kind is None else kind.__name__))
        if self.exit_fail:raise RuntimeError('marker_exit')
        return True  # Even a suppressing marker must never suppress the original error.


def profiler_spec():
    return [dict(id=1,name='kv_sdpa_0000001',parent=None,kernels=[]),
            dict(id=2,name='aten::scaled_dot_product_attention',parent=1,kernels=[]),
            dict(id=3,name='aten::_scaled_dot_product_flash_attention',parent=2,kernels=[dict(name='flash_kernel',device=0)]),
            dict(id=4,name='kv_sdpa_0000002',parent=None,kernels=[]),
            dict(id=5,name='aten::_scaled_dot_product_attention_math',parent=4,kernels=[]),
            dict(id=6,name='aten::bmm',parent=5,kernels=[dict(name='bmm_kernel',device=0)]),
            dict(id=7,name='aten::_scaled_dot_product_efficient_attention',parent=None,kernels=[dict(name='unassigned_kernel',device=0)])]


def make_events(spec):
    nodes={s['id']:SimpleNamespace(id=s['id'],name=s['name'],kernels=[SimpleNamespace(**k) for k in s['kernels']]) for s in spec}
    for s in spec:nodes[s['id']].cpu_parent=nodes[s['parent']] if s['parent'] is not None else None
    return list(nodes.values())


def observer_case(module,index):
    if index==17:
        spec=profiler_spec();value=module.profiler_inventory(make_events(spec))
        return dict(spec=spec,inventory=value)
    if index==18:
        spec=[dict(id=1,name='a',parent=2,kernels=[]),dict(id=2,name='b',parent=1,kernels=[])]
        try:module.profiler_inventory(make_events(spec))
        except ValueError as error:return dict(error=str(error),spec=spec)
        raise AssertionError('cycle_accepted')
    q=TensorStub([1,28,1,128]);k=TensorStub([1,4,187,128]);v=TensorStub([1,4,187,128])
    mask=TensorStub([1,1,24,210]);result=object();calls=[];markers=[]
    original_error=KeyboardInterrupt('original') if index==5 else RuntimeError('original')
    def original(*args,**kwargs):
        calls.append((args,kwargs))
        if index in (4,5,9):raise original_error
        return result
    if index==16:
        def original(query,key,value,attn_mask=None,dropout_p=0.,is_causal=False,*,scale=None,enable_gqa=False):
            calls.append(((query,key,value),{}));return result
    target=SimpleNamespace(scaled_dot_product_attention=original)
    def sink(row):
        if index==6:raise RuntimeError('sink')
    factory=lambda label:Marker(markers,label,enter_fail=index==7,exit_fail=index in (8,9))
    observer=module.SDPAObserver(target,sink=None if index==13 else sink,marker_factory=None if index==13 else factory,
                                 max_records=2 if index==14 else 20)
    args=(q,k,v);kwargs={};expected_args=args;expected_kwargs=kwargs
    if index==2:
        q=TensorStub([1,28,24,128]);k=TensorStub([1,4,210,128]);v=TensorStub([1,4,210,128])
        args=();kwargs=dict(query=q,key=k,value=v,attn_mask=mask,dropout_p=0.,is_causal=False,scale=.125,enable_gqa=False)
    if index==3:
        args=(q,k,v,None,0.,True);kwargs=dict(enable_gqa=True)
    if index==12:args=(BrokenMetadata(),k,v)
    if index==16:args=(q,k,v,mask);kwargs=dict(attn_mask=None)
    expected_args,expected_kwargs=args,kwargs
    nested_refused=conflict_refused=False;caught_identity=None;outputs=[]
    foreign=lambda *a,**kw:None
    try:
        with observer:
            if index==10:
                try:
                    with module.SDPAObserver(target):raise AssertionError('nested_body_reached')
                except RuntimeError as error:
                    assert str(error)=='observer_target_already_owned';nested_refused=True
            count=3 if index==14 else 1
            for unused in range(count):outputs.append(target.scaled_dot_product_attention(*args,**kwargs) is result)
            if index==11:target.scaled_dot_product_attention=foreign
    except BaseException as error:
        if index in (4,5,9):caught_identity=error is original_error;assert caught_identity
        elif index==11:
            conflict_refused=str(error)=='observer_restore_ownership_conflict';assert conflict_refused
        elif index==16:assert isinstance(error,TypeError);caught_identity=True
        else:raise
    if index==15:
        with observer:outputs.append(target.scaled_dot_product_attention(*args,**kwargs) is result)
    foreign_preserved=target.scaled_dot_product_attention is foreign if index==11 else None
    restored=target.scaled_dot_product_attention is original
    assert (foreign_preserved if index==11 else restored) and not observer.active
    assert all(outputs)
    for received_args,received_kwargs in calls:
        assert len(received_args)==len(expected_args) and all(a is b for a,b in zip(received_args,expected_args))
        assert list(received_kwargs)==list(expected_kwargs) and all(received_kwargs[n] is expected_kwargs[n] for n in expected_kwargs)
    return dict(original_body_calls=len(calls),observer_calls=observer.calls,records=observer.records,errors=observer.errors,
                original_restored=restored,foreign_preserved=foreign_preserved,nested_refused=nested_refused,
                conflict_refused=conflict_refused,original_exception_identity=caught_identity,returned_identity=outputs,
                argument_objects_and_keyword_order_preserved=True,marker_events=markers)


def archive_case(module,index,out):
    directory=out/'archive_fixtures'/('A'+str(index).zfill(2));directory.mkdir(parents=True)
    (directory/'payload.txt').write_text('preserve me\n')
    if index==5:
        (directory/'nested').mkdir();(directory/'nested'/'payload.txt').write_text('nested\n')
    limits=dict(max_files=3 if index in (1,5) else 2 if index==2 else 8,max_bytes=1 if index==3 else 1048576)
    state=dict(status='failed',error='worker_failed') if index==4 else dict(status='complete')
    value=module.finalize_archive(directory,state,**limits)
    duplicate_refused=False
    if index==6:
        before={str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*') if p.is_file()}
        try:module.finalize_archive(directory,state,**limits)
        except ValueError as error:duplicate_refused=str(error)=='new_archive_only_no_overwrite'
        assert duplicate_refused and before=={str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*') if p.is_file()}
    return dict(directory=str(directory.relative_to(out)),limits=limits,input_status=state['status'],result=value,duplicate_refused=duplicate_refused)


def main():
    out=Path(sys.argv[1])
    import sdpa_observer as observer
    import checked_archive as archive
    cases=[dict(id='O'+str(i).zfill(2),kind='observer',index=i) for i in range(1,19)]+[dict(id='A'+str(i).zfill(2),kind='archive',index=i) for i in range(1,7)]
    (out/'software_cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    results=[]
    for case in cases:
        value=observer_case(observer,case['index']) if case['kind']=='observer' else archive_case(archive,case['index'],out)
        results.append(dict(id=case['id'],output=value))
        (out/'software_results.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
    assert not observer._owners
    print(json.dumps(dict(status='complete',software_cases=24,real_SDPA_calls=0,GPU_queries=0)),flush=True)


if __name__=='__main__':main()
