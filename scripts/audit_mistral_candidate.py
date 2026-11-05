"""Metadata-only fixed Mistral audit. No checkpoint tensors or GPU inference.

Native system+user wrapper and query-blind token split are checked on frozen
messages. Meta tensors establish shapes only, never checkpoint correctness.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import re
import threading
import time
from urllib.request import Request,urlopen


REPO='mistralai/Mistral-7B-Instruct-v0.3'
REV='c170c708c41dac9275d15a8fff4eca08d52bab71'
SOURCE_NAMES=['audit_mistral_candidate.py','answer_contract_audit.py','accessdenied_pilot.py',
              'prepare_accessdenied.py','baseline_audit.py','pilot.py','trace_pilot.py']


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def messages(case):
    query=re.findall(r'----- USER QUERY -----\n(.*)\n----- END USER QUERY -----\n',case['prompt']);assert len(query)==1
    system,n=re.subn(r'----- USER QUERY -----\n(.*)\n----- END USER QUERY -----\n','',case['prompt']);assert n==1
    return [dict(role='system',content=system),dict(role='user',content=query[0])]


def native_parts(tokenizer,msg):
    text=tokenizer.apply_chat_template(msg,tokenize=False,add_generation_prompt=True)
    system,query=msg[0]['content'],msg[1]['content']
    assert text==tokenizer.bos_token+'[INST] '+system+'\n\n'+query+'[/INST]'
    assert text.count(query)==1
    query_start=text.index(query);encoded=tokenizer(text,add_special_tokens=False,return_offsets_mapping=True)
    ids=encoded['input_ids'];assert ids==tokenizer.apply_chat_template(msg,tokenize=True,add_generation_prompt=True)
    cut=next(i for i,(s,e) in enumerate(encoded['offset_mapping']) if e>query_start)
    assert cut>1 and all(e<=query_start for s,e in encoded['offset_mapping'][:cut])
    assert ids==ids[:cut]+ids[cut:]
    return text,ids,cut


def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',required=True);p.add_argument('--out',required=True)
    p.add_argument('--development-data',required=True);p.add_argument('--confirmation-data',required=True)
    p.add_argument('--qwen3-reference',required=True);p.add_argument('--preregistration',required=True)
    p.add_argument('--metadata-from',help='Reuse previously fetched metadata after fresh pinned-digest verification');a=p.parse_args()
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False);assets=root/'metadata';assets.mkdir()
    spec_path=Path(a.spec);spec=json.loads(spec_path.read_text());assert spec['repo_id']==REPO and spec['revision']==REV
    assert spec['gated'] is False and spec['private'] is False
    for name in ['official_spec.json','preregistration.md']:
        source=spec_path if name=='official_spec.json' else Path(a.preregistration)
        (root/name).write_bytes(source.read_bytes())
    source_sha={}
    for name in SOURCE_NAMES:
        data=Path(__file__).with_name(name).read_bytes();source_sha[name]=sha(data);(root/('source_'+name)).write_bytes(data)
    manifest=dict(args=vars(a),status='preparing',rows=0,start_unix=time.time(),source_sha256=source_sha,
        revision=REV,repo=REPO,official_spec_sha256=sha(spec_path.read_bytes()),
        preregistration_sha256=sha((root/'preregistration.md').read_bytes()),
        full_baseline_gate=False,checkpoint_weights_downloaded=False,gpu_inference=False)
    save(root/'manifest.json',manifest);lock=threading.Lock()
    def record(event):
        with lock:
            with (root/'fetch_attempts.jsonl').open('a') as f:f.write(json.dumps(dict(time_unix=time.time(),**event))+'\n')
    def fetch(entry):
        name=entry['rfilename'];assert entry['size']<2_000_000 and '/' not in name
        if a.metadata_from:
            donor=Path(a.metadata_from);prior=json.loads((donor.parent/'manifest.json').read_text())
            assert prior['revision']==REV and prior['official_spec_sha256']==manifest['official_spec_sha256']
            data=(donor/name).read_bytes();assert len(data)==entry['size']
            digest=hashlib.sha256(data).hexdigest() if entry.get('lfs') else hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            assert digest==(entry['lfs']['sha256'] if entry.get('lfs') else entry['blobId'])
            (assets/name).write_bytes(data);record(dict(file=name,event='reused_verified',digest=digest))
            return dict(file=name,size=len(data),algorithm='sha256' if entry.get('lfs') else 'git_blob_sha1',digest=digest,
                sha256=sha(data),transport='local:'+str((donor/name).resolve()),verified=True)
        urls=[f'https://hf-mirror.com/{REPO}/resolve/{REV}/{name}',
              f'https://www.modelscope.cn/models/{REPO}/resolve/master/{name}',
              f'https://huggingface.co/{REPO}/resolve/{REV}/{name}']
        for url in urls:
            record(dict(file=name,event='attempt',url=url))
            try:
                with urlopen(Request(url,headers={'User-Agent':'kv-pruning-mistral-metadata'}),timeout=15) as response:
                    data=response.read(entry['size']+1)
                assert len(data)==entry['size'],'Metadata size mismatch'
                algorithm='sha256' if entry.get('lfs') else 'git_blob_sha1'
                digest=hashlib.sha256(data).hexdigest() if entry.get('lfs') else hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
                expected=entry['lfs']['sha256'] if entry.get('lfs') else entry['blobId']
                assert digest==expected,'Metadata digest mismatch'
                (assets/name).write_bytes(data)
                check=dict(file=name,size=len(data),algorithm=algorithm,digest=digest,sha256=sha(data),transport=url,verified=True)
                record(dict(file=name,event='verified',digest=digest));print('VERIFIED',name,flush=True);return check
            except Exception as error:record(dict(file=name,event='failure',url=url,type=type(error).__name__,message=str(error)))
        raise RuntimeError('All metadata transfers failed: '+name)
    try:
        entries=[e for e in spec['files'] if e['rfilename'] in spec['metadata_files']];assert len(entries)==10
        checks=[]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for future in as_completed([pool.submit(fetch,e) for e in entries]):
                checks.append(future.result());save(root/'metadata_checks.json',checks)
        import torch
        from transformers import AutoConfig,AutoModelForCausalLM,AutoTokenizer
        from answer_contract_audit import checked_source
        from accessdenied_pilot import validate_case
        manifest['versions']={name:importlib.metadata.version(name) for name in ['torch','transformers','tokenizers','safetensors','sentencepiece','protobuf']}
        manifest['python']=__import__('sys').version
        config=AutoConfig.from_pretrained(assets,local_files_only=True,trust_remote_code=False)
        assert config.model_type=='mistral' and config.num_hidden_layers==32 and config.num_attention_heads==32 and config.num_key_value_heads==8
        assert config.sliding_window is None
        with torch.device('meta'):
            model=AutoModelForCausalLM.from_config(config,torch_dtype=torch.bfloat16,attn_implementation='sdpa',trust_remote_code=False)
        assert all(param.device.type=='meta' for param in model.parameters())
        assert len(model.model.layers)==32 and all(layer.self_attn.config.sliding_window is None for layer in model.model.layers)
        index=json.loads((assets/'model.safetensors.index.json').read_text())
        assert set(index['weight_map'])==set(model.state_dict()),'Config-created state names differ from checkpoint index'
        parameters=sum(param.numel() for param in model.parameters());parameter_bytes=parameters*2
        assert index['metadata']['total_size']==parameter_bytes,'Index byte count differs from BF16 shape estimate'
        source_file=Path(inspect.getfile(type(model.model.layers[0].self_attn)));(root/'runtime_modeling_mistral.py').write_bytes(source_file.read_bytes())
        head_dim=config.hidden_size//config.num_attention_heads;per_token=2*32*8*head_dim*2;assert per_token==131072
        shape=dict(model_type=config.model_type,layers=32,query_heads=32,kv_heads=8,head_dim=head_dim,sliding_window=config.sliding_window,
            parameter_elements=parameters,bf16_parameter_bytes=parameter_bytes,checkpoint_index_state_names_match=True,
            checkpoint_tensor_headers_not_read=True,all_parameters_meta=True,kv_bytes_per_prefix_token_bf16=per_token,
            runtime_source_sha256=sha(source_file.read_bytes()),note='Meta construction/index only. Actual weights/dtype and generation remain unverified.')
        save(root/'architecture_checks.json',shape);del model
        tokenizer=AutoTokenizer.from_pretrained(assets,local_files_only=True,trust_remote_code=False,use_fast=True);assert tokenizer.is_fast
        reference=Path(a.qwen3_reference).resolve();qwen={c['case_id']:c for c in map(json.loads,(reference/'cases.jsonl').read_text().splitlines())}
        manifest['input_sha256']={str(reference/'cases.jsonl'):sha((reference/'cases.jsonl').read_bytes())}
        all_checks=[];cohort_summary={};cohorts={}
        for stage,location in [('development',a.development_data),('confirmation',a.confirmation_data)]:
            location=Path(location).resolve();origin,cases=checked_source(location);assert len(cases)==24
            for name in ['manifest.json','cases.jsonl']:manifest['input_sha256'][str(location/name)]=sha((location/name).read_bytes())
            prepared=[]
            for case in cases:
                validate_case(case);msg=messages(case)
                if stage=='development':
                    old=qwen[case['case_id']]
                    previous=[dict(role=role,content=content) for role,content in re.findall(r'<\|im_start\|>(system|user)\n(.*?)<\|im_end\|>\n',old['full_text'],re.S)]
                    assert previous==msg and old['source_id']==case['source_id'] and old['expected']==case['expected']
                text,ids,cut=native_parts(tokenizer,msg)
                assert len(ids)+512<=config.max_position_embeddings
                for query in ["Who is the user's supervisor?",'Is any salary information available?']:
                    _,alt_ids,alt_cut=native_parts(tokenizer,[msg[0],dict(role='user',content=query)])
                    assert ids[:cut]==alt_ids[:alt_cut],'Prefix changes with future query'
                system_only=tokenizer.apply_chat_template(msg[:1],tokenize=False,add_generation_prompt=False)
                assert msg[0]['content'] not in system_only,'Re-audit native prefix behavior if template changes'
                case.update(full_text=text,input_ids=ids,prefix_ids=ids[:cut],suffix_ids=ids[cut:],input_tokens=len(ids),prefix_tokens=cut,
                    message_sha256=sha(json.dumps(msg,ensure_ascii=False,sort_keys=True).encode()))
                prepared.append(case)
                all_checks.append(dict(stage=stage,case_id=case['case_id'],rendered_oracle_checked=True,original_task_messages_preserved=True,
                    native_system_user_fold_checked=True,full_tokenize_exact=True,prefix_excludes_query=True,two_query_prefix_probes_exact=True,
                    native_system_only_output=system_only,input_tokens=len(ids),prefix_tokens=cut,prefix_kv_bytes_bf16_estimate=cut*per_token))
            (root/(stage+'_cases.jsonl')).write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in prepared),encoding='utf-8')
            cohorts[stage]=prepared
            cohort_summary[stage]=dict(cases=24,input_tokens=[min(c['input_tokens'] for c in prepared),max(c['input_tokens'] for c in prepared)],
                prefix_tokens=[min(c['prefix_tokens'] for c in prepared),max(c['prefix_tokens'] for c in prepared)])
        for name in ['source_id','target_name']:assert {c[name] for c in cohorts['development']}.isdisjoint({c[name] for c in cohorts['confirmation']})
        save(root/'frontend_checks.json',all_checks)
        max_prefix=max(c['prefix_tokens'] for values in cohorts.values() for c in values)
        result=dict(metadata_files_verified=10,metadata_bytes=sum(x['size'] for x in checks),cohorts=cohort_summary,architecture=shape,
            estimated_parameters_plus_max_prefix_kv_bytes=parameter_bytes+max_prefix*per_token,
            estimated_parameters_plus_prefix_and_512_decode_kv_bytes=parameter_bytes+(max_prefix+512)*per_token,
            additional_runtime_workspace_unmeasured=True,all_48_tokenization_oracles_passed=True,
            native_system_only_prefix_usable=False,prefix_method='Slice complete native token stream before first token overlapping user query; verified with two alternate queries',
            candidate_admissible_for_weight_acquisition=True,model_task_capability_unknown=True,weights_not_downloaded=True,
            next_mode=dict(do_sample=False,repetition_penalty=1.,max_new_tokens=512,torch_dtype='bfloat16',attention='sdpa'),
            limitation='Native Mistral template folds system into INST. No Qwen-style role-token equivalence, cached-generation correctness, weight integrity, or task score claim.')
        save(root/'summary.json',result)
        manifest.update(status='complete',end_unix=time.time(),candidate_admissible=True,metadata_files=10,rows=0)
        save(root/'manifest.json',manifest);print('COMPLETE',json.dumps(result),flush=True)
    except Exception as error:
        manifest.update(status='failed',end_unix=time.time(),error_type=type(error).__name__,error_message=str(error));save(root/'manifest.json',manifest);raise


if __name__=='__main__':main()
