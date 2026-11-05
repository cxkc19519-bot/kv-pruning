"""Fixed non-thinking Qwen3 Full-KV model-selection audit on frozen messages.

No token selection/manual query scoring is used. Native Qwen3 handles its own
Q/K normalization. All task messages and grading come from the frozen cohort.
"""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import re
import struct
import time

import torch
from transformers import AutoConfig,AutoModelForCausalLM,AutoTokenizer,DynamicCache
from accessdenied_pilot import author_salary_grader,judge,summarize,validate_case
from baseline_audit import clone_cache,native_generate
from pilot import cache_bytes,generate
from trace_pilot import save,sha


REV='b968826d9c46dd6066d109eabc6255188de91218'


def verify_model_proof(model_dir,download_root):
    manifest=json.loads((download_root/'manifest.json').read_text())
    spec_path=download_root/'official_spec.json';spec=json.loads(spec_path.read_text())
    proof_path=download_root/'artifact_checks.json';proof=json.loads(proof_path.read_text())
    assert manifest['status']=='complete' and proof['complete']
    assert proof['revision']==spec['revision']==manifest['revision']==REV
    assert sha(spec_path.read_bytes())==manifest['official_spec_sha256']
    assert Path(proof['model_dir']).resolve()==model_dir.resolve()
    entries={x['rfilename']:x for x in spec['files']};assert len(entries)==len(proof['files'])
    for check in proof['files']:
        path=model_dir/check['path'];entry=entries[check['path']]
        assert check['verified'] and path.stat().st_size==entry['size']==check['size']
        assert path.stat().st_mtime_ns==check['mtime_ns'],'Artifact changed since full digest verification'
        expected=entry['lfs']['sha256'] if entry.get('lfs') else entry['blobId']
        assert check['digest']==expected
        if not entry.get('lfs'):
            data=path.read_bytes();assert __import__('hashlib').sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==expected
    return dict(revision=REV,official_spec_sha256=sha(spec_path.read_bytes()),
        artifact_checks_sha256=sha(proof_path.read_bytes()),download_manifest_sha256=sha((download_root/'manifest.json').read_bytes()),
        note='Full digests verified by downloader; this audit rechecks all file size/mtime and metadata blob hashes, preserving the pinned proof')


def inspect_weight_headers(model_dir):
    index=json.loads((model_dir/'model.safetensors.index.json').read_text())['weight_map']
    tensors={};dtypes={};elements=0
    for name in sorted(set(index.values())):
        with (model_dir/name).open('rb') as f:
            length=struct.unpack('<Q',f.read(8))[0];assert 0<length<10_000_000
            header=json.loads(f.read(length))
        for key,value in header.items():
            if key=='__metadata__':continue
            assert key not in tensors and index[key]==name
            tensors[key]=name;dtypes[value['dtype']]=dtypes.get(value['dtype'],0)+1
            elements+=__import__('math').prod(value['shape'])
    assert set(index)==set(tensors),'Tensor index/header mismatch'
    assert set(dtypes)=={'BF16'},'Unexpected quantized or mixed checkpoint weights'
    return dict(tensors=len(tensors),parameter_elements=elements,tensor_dtypes=dtypes,index_headers_match=True,
                note='Header inspection after complete digest verification; no tensor values loaded by this check')


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--download-run',required=True)
    p.add_argument('--data-root',required=True);p.add_argument('--out',required=True)
    p.add_argument('--stage',choices=['development','confirmation'],default='development')
    p.add_argument('--reference-run');p.add_argument('--gate-run');a=p.parse_args()
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False);data_root=Path(a.data_root);model_dir=Path(a.model)
    source={}
    for name in ['qwen3_access_audit.py','accessdenied_pilot.py','prepare_accessdenied.py','baseline_audit.py','pilot.py','trace_pilot.py']:
        data=Path(__file__).with_name(name).read_bytes();source[name]=sha(data);(root/('source_'+name)).write_bytes(data)
    manifest=dict(args=vars(a),status='preparing',rows=0,start_unix=time.time(),source_sha256=source,
        versions={n:importlib.metadata.version(n) for n in ['torch','transformers','tokenizers','safetensors']},
        cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES','all'),
        decode_policy=dict(enable_thinking=False,do_sample=False,repetition_penalty=1.,max_new_tokens=512),
        scope='Frozen task messages, model-specific native wrapper; Full-KV only, same Qwen family and no algorithm/architecture-generalization claim')
    save(root/'manifest.json',manifest)
    manifest['model_proof']=verify_model_proof(model_dir,Path(a.download_run))
    manifest['checkpoint_headers']=inspect_weight_headers(model_dir)
    config=AutoConfig.from_pretrained(a.model,local_files_only=True,trust_remote_code=False)
    assert config.model_type=='qwen3' and config.num_hidden_layers==36
    assert not config.use_sliding_window and config.sliding_window is None
    manifest['model_config_sha256']=sha((model_dir/'config.json').read_bytes())
    dmanifest=json.loads((data_root/'manifest.json').read_text());assert dmanifest['status']=='complete'
    assert sha((data_root/'cases.jsonl').read_bytes())==dmanifest['cases_sha256']
    for name,info in dmanifest['upstream_files'].items():assert sha((data_root/'upstream'/name).read_bytes())==info['sha256']
    cases=[json.loads(s) for s in (data_root/'cases.jsonl').read_text().splitlines()];assert len(cases)==24
    manifest['input_sha256']={str(path):sha(path.read_bytes()) for path in [data_root/'manifest.json',data_root/'cases.jsonl']}
    if a.stage=='confirmation':
        assert a.gate_run
        prior=Path(a.gate_run);m=json.loads((prior/'manifest.json').read_text())
        eligible=m['status']=='complete' and m.get('full_baseline_gate') is True and m['decode_policy']==manifest['decode_policy']
        if not eligible:
            manifest.update(status='refused_quality_gate',end_unix=time.time(),reason='Qwen3 development Full gate failed')
            save(root/'manifest.json',manifest);raise RuntimeError('Development quality gate failed; confirmation not run')
        assert m['model_proof']['revision']==REV and Path(m['args']['model']).resolve()==model_dir.resolve()
        old=[json.loads(s) for s in (prior/'cases.jsonl').read_text().splitlines()]
        assert {c['source_id'] for c in cases}.isdisjoint({c['source_id'] for c in old})
        assert {c['target_name'] for c in cases}.isdisjoint({c['target_name'] for c in old})
        manifest['development_gate_manifest_sha256']=sha((prior/'manifest.json').read_bytes())
    references={}
    if a.stage=='development':
        assert a.reference_run;prior=Path(a.reference_run)
        references={c['case_id']:c for c in map(json.loads,(prior/'cases.jsonl').read_text().splitlines())}
        manifest['qwen2_reference_sha256']={name:sha((prior/name).read_bytes()) for name in ['cases.jsonl','generations.jsonl']}
    tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True,trust_remote_code=False)
    grade,mapping=author_salary_grader(data_root/'upstream/scripts/grade.py')
    message_hashes=[]
    for case in cases:
        validate_case(case);prompt=case['prompt']
        query=re.findall(r'----- USER QUERY -----\n(.*)\n----- END USER QUERY -----\n',prompt);assert len(query)==1
        system,n=re.subn(r'----- USER QUERY -----\n(.*)\n----- END USER QUERY -----\n','',prompt);assert n==1
        messages=[dict(role='system',content=system),dict(role='user',content=query[0])]
        if references:
            ref=references[case['case_id']];assert ref['source_id']==case['source_id'] and ref['expected']==case['expected']
            previous=[dict(role=r,content=c) for r,c in re.findall(r'<\|im_start\|>(system|user)\n(.*?)<\|im_end\|>\n',ref['full_text'],re.S)]
            assert previous==messages,'Task message content differs across models'
        text=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
        prefix=tok.apply_chat_template(messages[:1],tokenize=True,add_generation_prompt=False,enable_thinking=False)
        ids=tok.encode(text,add_special_tokens=False);assert ids[:len(prefix)]==prefix
        assert '<think>\n\n</think>' in text[text.rfind('<|im_start|>assistant'):], 'Expected native non-thinking prefill missing'
        mh=sha(json.dumps(messages,ensure_ascii=False,sort_keys=True).encode());message_hashes.append(dict(case_id=case['case_id'],message_sha256=mh))
        case.update(full_text=text,input_ids=ids,prefix_ids=prefix,suffix_ids=ids[len(prefix):],input_tokens=len(ids),prefix_tokens=len(prefix),message_sha256=mh)
    with (root/'cases.jsonl').open('w') as f:
        for case in cases:f.write(json.dumps(case)+'\n')
    save(root/'message_checks.json',dict(cases=len(cases),messages_identical_to_qwen2=bool(references),message_hashes=message_hashes,
        native_non_thinking_prefill_checked=True,all_final_rendered_oracles_checked=True))
    torch.manual_seed(20261028);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=False
    manifest.update(status='running',planned_rows=len(cases));save(root/'manifest.json',manifest)
    try:model=AutoModelForCausalLM.from_pretrained(a.model,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True,trust_remote_code=False).eval().to('cuda:0')
    except torch.OutOfMemoryError:
        manifest.update(status='failed_oom',end_unix=time.time());save(root/'manifest.json',manifest);raise
    assert len(model.model.layers)==36 and all(getattr(x.self_attn,'sliding_window',None) is None for x in model.model.layers)
    element_size=next(model.parameters()).element_size()
    bytes_per_token=2*config.num_hidden_layers*config.num_key_value_heads*config.head_dim*element_size
    assert bytes_per_token==147456
    rows=[];checks=[];done=set()
    with (root/'generations.jsonl').open('w') as f:
        for case in cases:
            text,ids=native_generate(model,tok,case['input_ids'],512,repetition_penalty=1.)
            row={k:case[k] for k in ['case_id','base','condition','source_id','source_row_index','expected','input_tokens','prefix_tokens']}
            row.update(text=text,ids=ids,metrics=judge(text,case,grade,mapping),generation_at_limit=len(ids)>=512)
            rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
            if case['condition'] not in done:
                with torch.inference_mode():
                    reference=DynamicCache();model.model(torch.tensor([case['prefix_ids']],device=model.device),past_key_values=reference,use_cache=True)
                measured=cache_bytes(reference);assert measured==len(case['prefix_ids'])*bytes_per_token
                branch=clone_cache(reference);_,cached=native_generate(model,tok,case['suffix_ids'],512,branch,len(case['prefix_ids']),repetition_penalty=1.);del branch
                branch=clone_cache(reference);_,custom,_=generate(model,tok,branch,len(case['prefix_ids']),case['suffix_ids'],512);del branch,reference
                checks.append(dict(case_id=case['case_id'],bytes_per_prefix_token=bytes_per_token,full_prefix_kv_bytes=measured,
                    native_ids=ids,cached_ids=cached,custom_ids=custom,native_cached_exact=ids==cached,custom_cached_exact=ids==custom))
                save(root/'correctness_checks.json',checks);assert ids==cached==custom,'Qwen3 Full cache-path parity failed';done.add(case['condition'])
            save(root/'summary.json',summarize(rows));print('CASE',case['case_id'],'rows',len(rows),'correct',row['metrics']['correct'],flush=True)
    result=summarize(rows);manifest.update(status='complete',rows=len(rows),end_unix=time.time(),full_baseline_gate=result['full_baseline_gate'])
    save(root/'manifest.json',manifest);print('COMPLETE',json.dumps(result),flush=True)


if __name__=='__main__':main()
