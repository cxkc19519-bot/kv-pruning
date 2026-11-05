"""Kineto device-aware adapter; the CPU-validated SDPA wrapper stays unchanged."""
from types import SimpleNamespace as NS
from sdpa_observer import SDPAObserver,profiler_inventory as _inventory


def device_name(event):
    value=getattr(event,'device_type',None);name=getattr(value,'name',None)
    if isinstance(name,str):return name
    text=str(value)
    return text.rsplit('.',1)[-1] if text in ('CPU','CUDA','DeviceType.CPU','DeviceType.CUDA') else 'unknown'


def profiler_inventory(events):
    events=list(events)
    if any(e.name.startswith('kv_sdpa_') and device_name(e)=='unknown' for e in events):
        raise ValueError('unknown_marker_device_type')
    cpu=[e for e in events if device_name(e)=='CPU']
    value=_inventory(cpu)
    value['CPU_parent_scope_only']=True
    value['ignored_non_CPU_marker_annotations']=sum(e.name.startswith('kv_sdpa_') and device_name(e)!='CPU' for e in events)
    return value


def run_cpu_checks():
    def e(i,name,kind,parent=None,kernels=()):
        return NS(id=i,name=name,device_type=NS(name=kind),cpu_parent=parent,kernels=list(kernels))
    marker=e(1,'kv_sdpa_0000001','CPU')
    op=e(2,'aten::_scaled_dot_product_efficient_attention','CPU',marker,[NS(name='synthetic_kernel',device=0)])
    gpu=e(1,'kv_sdpa_0000001','CUDA')
    value=profiler_inventory([marker,op,gpu])
    assert len(value['markers'])==1 and value['ignored_non_CPU_marker_annotations']==1 and len(value['markers'][0]['kernels'])==1
    orphan=e(3,'orphan_gpu_kernel','CUDA');value=profiler_inventory([marker,op,gpu,orphan])
    assert len(value['markers'])==1 and not value['unassigned_events']
    unknown=e(9,'kv_sdpa_unknown','unknown')
    try:profiler_inventory([unknown])
    except ValueError as error:assert str(error)=='unknown_marker_device_type'
    else:raise AssertionError('unknown_device_accepted')
    a=e(10,'a','CPU');b=e(11,'b','CPU',a);a.cpu_parent=b
    try:profiler_inventory([a,b])
    except ValueError:pass
    else:raise AssertionError('cycle_accepted')
    result=object();target=NS(scaled_dot_product_attention=lambda *a,**k:result);original=target.scaled_dot_product_attention
    with SDPAObserver(target) as observer:assert target.scaled_dot_product_attention(None,None,None) is result
    assert target.scaled_dot_product_attention is original and not observer.errors
    return dict(passed=True,cases=5,CPU_GPU_same_name_disambiguated=True,unknown_devices_rejected=True,
                orphan_GPU_not_assigned=True,cycle_rejected=True,original_observer_pass_through_unchanged=True,synthetic_only=True)
