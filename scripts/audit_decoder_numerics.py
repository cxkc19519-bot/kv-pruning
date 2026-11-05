"""Offline saved-logit analysis and inert scalar replay of installed SDPA branches.

No Torch/tensor/model execution. Library function ASTs receive shape-only stubs.
The replay predicts Python dispatch arguments, not the CUDA kernel actually used.
"""
import sys
sys.dont_write_bytecode = True
from array import array
import ast
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
from types import SimpleNamespace


def save(out,name,value):
    (out/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


class Shape:
    def __init__(self,shape):self.shape=tuple(shape);self.ndim=len(shape)
    def all(self):return True
    def __getitem__(self,index):return self
    def transpose(self,*unused):return self
    def contiguous(self):return self


def source_replay(cfg,out,trace,case,maps):
    locations={Path(p).name:p for p in cfg['runtime_sources']}
    texts={k:Path(p).read_text() for k,p in locations.items()}
    captured={}; repeats=[]
    def sdpa(q,k,v,**kwargs):
        captured.update(query_shape=list(q.shape),key_shape=list(k.shape),value_shape=list(v.shape),
                        mask_none=kwargs['attn_mask'] is None,is_causal=kwargs['is_causal'],
                        enable_gqa=kwargs.get('enable_gqa',False))
        return Shape(q.shape)
    def repeat(k,n):
        repeats.append(n)
        return Shape((k.shape[0],k.shape[1]*n,k.shape[2],k.shape[3]))
    fake=SimpleNamespace(jit=SimpleNamespace(is_tracing=lambda:False),fx=SimpleNamespace(Proxy=type('Proxy',(),{})),
                         nn=SimpleNamespace(functional=SimpleNamespace(scaled_dot_product_attention=sdpa)))
    env=dict(torch=fake,is_torchdynamo_compiling=lambda:False,_is_torch_xpu_available=False,
             _is_torch_npu_available=False,_is_torch_greater_or_equal_than_2_5=True,
             _is_torch_greater_or_equal_than_2_8=False,repeat_kv=repeat)
    extracts=[]
    for filename,names in [('masking_utils.py',['_ignore_causal_mask_sdpa','causal_mask_function']),
                            ('sdpa_attention.py',['use_gqa_in_sdpa','sdpa_attention_forward'])]:
        tree=ast.parse(texts[filename])
        found=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
        assert len(found)==len(names)
        for node in found:
            extracts.append(dict(file=filename,name=node.name,line=node.lineno,original_source=ast.get_source_segment(texts[filename],node)))
            node.returns=None;node.decorator_list=[]
            for arg in node.args.posonlyargs+node.args.args+node.args.kwonlyargs:
                arg.annotation=None
            if node.args.vararg:node.args.vararg.annotation=None
            if node.args.kwarg:node.args.kwarg.annotation=None
            exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),filename,'exec'),env)
    save(out,'source_function_extracts.json',extracts)
    rows=[];mathematical_rows=0
    for t in trace:
        length=len(t['input_ids']);physical=t['physical_before'];kv=physical+length
        skip=env['_ignore_causal_mask_sdpa'](Shape((1,kv)),length,kv,0,None)
        mask=None if skip else Shape((1,1,length,kv))
        captured.clear();repeats.clear()
        env['sdpa_attention_forward'](SimpleNamespace(num_key_value_groups=7,is_causal=True),
            Shape((1,28,length,128)),Shape((1,4,kv,128)),Shape((1,4,kv,128)),mask,dropout=0.,scaling=128**-.5)
        row=dict(call=t['call'],path=t['path'],query_length=length,physical_before=physical,
                 **captured,repeat_kv_calls=len(repeats),status='source_logic_replay_not_runtime_kernel_observation')
        assert row['mask_none']==(length==1 or physical==0)
        assert row['enable_gqa']==row['mask_none']
        assert row['is_causal']==(length>1 and row['mask_none'])
        if t['path'].startswith('recency'):retained=maps['recency']
        elif t['path'].startswith('uniform_random'):retained=maps['uniform_random']
        else:retained=None
        for j,q in enumerate(t['cache_positions']):
            visible=[k for k in range(kv) if (True if row['mask_none'] and not row['is_causal'] else env['causal_mask_function'](0,0,q,k))]
            assert visible==list(range(physical+j+1))
            if retained is not None:
                logical_keys=retained+list(range(373,373+(physical-186)+length))
                assert [logical_keys[k] for k in visible]==retained+list(range(373,t['logical_positions'][j]+1))
            mathematical_rows+=1
        rows.append(row)
    save(out,'source_branch_replay.json',rows)
    return dict(replayed_calls=len(rows),mask_none=sum(r['mask_none'] for r in rows),
        explicit_mask=sum(not r['mask_none'] for r in rows),enable_gqa=sum(r['enable_gqa'] for r in rows),
        explicit_KV_repeat=sum(not r['enable_gqa'] for r in rows),is_causal_true=sum(r['is_causal'] for r in rows),
        mathematical_causal_rows_checked=mathematical_rows,visible_history_sets_equal_under_recorded_contract=True,
        exact_CUDA_kernel_observed=False,XPU_or_NPU_assumed_absent=True,trace_not_tensor_capture=True)


def logdist(values):
    m=max(values);z=math.log(math.fsum(math.exp(x-m) for x in values))
    return [v-m-z for v in values]


def scope_metrics(p,q):
    lp,lq=logdist(p),logdist(q)
    pp,qq=[math.exp(v) for v in lp],[math.exp(v) for v in lq]
    delta=[b-a for a,b in zip(p,q)];shift=math.fsum(w*d for w,d in zip(pp,delta))
    maximum_p,maximum_q=max(p),max(q)
    winners_p=[i for i,x in enumerate(p) if x==maximum_p];winners_q=[i for i,x in enumerate(q) if x==maximum_q]
    top=sorted(pp,reverse=True)
    js=0.
    for a,b,la,lb in zip(pp,qq,lp,lq):
        mixture=(a+b)/2
        if mixture:
            if a:js+=.5*a*(la-math.log(mixture))
            if b:js+=.5*b*(lb-math.log(mixture))
    return dict(max_abs_logit=max(abs(d) for d in delta),KL_p_q=max(0.,math.fsum(a*(la-lb) for a,la,lb in zip(pp,lp,lq))),
        KL_q_p=max(0.,math.fsum(b*(lb-la) for b,la,lb in zip(qq,lp,lq))),
        total_variation=.5*math.fsum(abs(a-b) for a,b in zip(pp,qq)),Jensen_Shannon=max(0.,js),
        max_probability_error=max(abs(a-b) for a,b in zip(pp,qq)),reference_top_probability=max(pp),
        comparison_top_probability=max(qq),reference_probability_margin=top[0]-top[1],
        argmax_equal=winners_p==winners_q,reference_argmax_indices=winners_p,comparison_argmax_indices=winners_q,
        probability_weighted_logit_shift=shift,reference_weighted_centered_RMS=math.sqrt(math.fsum(w*(d-shift)**2 for w,d in zip(pp,delta))),
        shift_centered_max_logit_error=max(abs(d-shift) for d in delta),
        same_decision_margin_sufficient=top[0]-top[1]>2*max(abs(a-b) for a,b in zip(pp,qq)))


def main():
    out=Path(sys.argv[1]);cfg=json.loads((out/'registration_snapshot.json').read_text());root=Path(cfg['root']);parent=root/cfg['parent_run']
    vectors={}
    for r in json.loads((parent/'vectors.json').read_text()):
        values=array('f');values.frombytes((parent/r['file']).read_bytes());assert len(values)==152064
        vectors[r['name']]=values
    trace=[json.loads(line) for line in (parent/'forward_trace.jsonl').read_text().splitlines()]
    maps={p['name']:p['indices'] for p in json.loads((parent/'gather_plans.json').read_text())}
    case=json.loads((parent/'engineering_inputs.json').read_text())[0]
    branches=source_replay(cfg,out,trace,case,maps)
    pairs=[('whole_full','whole','full_batch'),('whole_split','whole','split_full_batch'),
           ('recency_paths','recency_batch','recency_tokenwise'),('random_paths','uniform_random_batch','uniform_random_tokenwise')]
    reports=[]
    for name,a,b in pairs:
        p,q=vectors[a],vectors[b]
        scopes={label:scope_metrics([p[i] for i in ids],[q[i] for i in ids]) for label,ids in [('global',range(len(p))),('allowed',[32,33,34,35])]}
        reports.append(dict(name=name,reference_path=a,comparison_path=b,scopes=scopes,
             all_values_on_BF16_grid=all(struct.unpack('<I',struct.pack('<f',v))[0]&65535==0 for v in list(p)+list(q))))
    save(out,'logit_probability_metrics.json',reports)
    save(out,'summary.json',dict(status='complete',pairs=4,source_branch_analysis=branches,
        new_model_calls=0,tokenizer_encodes=0,GPU_queries=0,weight_bytes_read=0,
        parent_engineering_status='failed_unchanged',H3_candidate_rankings_computed=False,
        all_error_due_to_backend_switch_proven=False,new_tolerance_selected=False))
    assert not any(n.split('.')[0] in ('torch','transformers','numpy','tokenizers') for n in sys.modules)
    print(json.dumps(dict(status='complete',pairs=4,source_branch_analysis=branches)),flush=True)


if __name__=='__main__':main()
