"""Full-KV Mistral audit on frozen original task messages, never prompt search."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import time

import torch
from transformers import AutoConfig,AutoModelForCausalLM,AutoTokenizer,DynamicCache
from accessdenied_pilot import author_salary_grader,judge,summarize,validate_case
from answer_contract_audit import checked_source
from audit_mistral_candidate import messages,native_parts
from baseline_audit import clone_cache,native_generate
from fetch_pinned_model import verify,sha,save
from pilot import cache_bytes,generate
from qwen3_access_audit import inspect_weight_headers


REPO='mistralai/Mistral-7B-Instruct-v0.3'
REV='c170c708c41dac9275d15a8fff4eca08d52bab71'
SOURCES=['mistral_access_audit.py','audit_mistral_candidate.py','answer_contract_audit.py','accessdenied_pilot.py',
         'prepare_accessdenied.py','baseline_audit.py','fetch_pinned_model.py','pilot.py','trace_pilot.py','qwen3_access_audit.py']


def model_proof(model_path,download):
    m=json.loads((download/'manifest.json').read_text());spec=json.loads((download/'official_spec.json').read_text())
    proof=json.loads((download/'artifact_checks.json').read_text())
    assert m['status']=='complete' and proof['complete'] and m['model_repo']==spec['repo_id']==proof['repo']==REPO
    assert m['revision']==spec['revision']==proof['revision']==REV
    assert sha((download/'official_spec.json').read_bytes())==m['official_spec_sha256']
    assert Path(proof['model_dir']).resolve()==Path(m['model_dir']).resolve()==model_path.resolve()
    entries={e['rfilename']:e for e in spec['files']};assert len(proof['files'])==len(entries)==13
    assert {e['path'] for e in proof['files']}==set(entries)
    for c in proof['files']:
        entry=entries[c['path']];p=model_path/c['path']
        assert c['verified'] and p.stat().st_size==c['size']==entry['size'] and p.stat().st_mtime_ns==c['mtime_ns']
        assert c['digest']==(entry['lfs']['sha256'] if entry.get('lfs') else entry['blobId'])
        if c['path'] in spec['metadata_files']:assert verify(p,entry)
    return dict(repo=REPO,revision=REV,official_spec_sha256=m['official_spec_sha256'],
        artifact_checks_sha256=sha((download/'artifact_checks.json').read_bytes()),download_manifest_sha256=sha((download/'manifest.json').read_bytes()),
        note='Downloader verified complete file digests. All sizes/mtime and metadata hashes rechecked before loading.')


def main():
    p=argparse.ArgumentParser()
    for name in ['model','download-run','candidate-run','out','preregistration']:p.add_argument('--'+name,required=True)
    p.add_argument('--stage',choices=['development','confirmation'],required=True);p.add_argument('--gate-run');a=p.parse_args()
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False);candidate=Path(a.candidate_run).resolve();model_path=Path(a.model).resolve()
    source={}
    for name in SOURCES:
        data=Path(__file__).with_name(name).read_bytes();source[name]=sha(data);(root/('source_'+name)).write_bytes(data)
    (root/'preregistration.md').write_bytes(Path(a.preregistration).read_bytes())
    m=dict(args=vars(a),status='preparing',rows=0,start_unix=time.time(),source_sha256=source,
        versions={n:importlib.metadata.version(n) for n in ['torch','transformers','tokenizers','safetensors','sentencepiece','protobuf']},
        cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES','all'),
        decode_policy=dict(do_sample=False,repetition_penalty=1.,max_new_tokens=512),
        preregistration_sha256=sha((root/'preregistration.md').read_bytes()),
        scope='Original frozen task messages, native Mistral INST-folded system/user wrapper; Full KV only, no prompt changes or compression')
    save(root/'manifest.json',m)
    try:
        m['model_proof']=model_proof(model_path,Path(a.download_run))
        m['checkpoint_headers']=inspect_weight_headers(model_path)
        assert m['checkpoint_headers']['parameter_elements']==7248023552
        m['model_config_sha256']=sha((model_path/'config.json').read_bytes())
        config=AutoConfig.from_pretrained(model_path,local_files_only=True,trust_remote_code=False)
        assert config.model_type=='mistral' and config.num_hidden_layers==32 and config.num_key_value_heads==8 and config.sliding_window is None
        cm=json.loads((candidate/'manifest.json').read_text());closure=json.loads((candidate/'closure_audit.json').read_text())
        assert cm['status']=='complete' and cm['candidate_admissible'] and cm['revision']==REV and closure['status']=='complete'
        for path,digest in closure['input_sha256'].items():assert sha(Path(path).read_bytes())==digest
        stage=a.stage;prepared_file=candidate/(stage+'_cases.jsonl')
        cases=[json.loads(s) for s in prepared_file.read_text().splitlines()];assert len(cases)==24
        origin_path=Path(cm['args'][stage+'_data']).resolve();_,originals=checked_source(origin_path)
        original={c['case_id']:c for c in originals}
        m['input_sha256']={str(p):sha(p.read_bytes()) for p in [candidate/'manifest.json',candidate/'closure_audit.json',prepared_file,origin_path/'manifest.json',origin_path/'cases.jsonl']}
        if stage=='confirmation':
            assert a.gate_run
            prior=Path(a.gate_run);gate=json.loads((prior/'manifest.json').read_text())
            assert gate['status']=='complete' and gate['full_baseline_gate'] is True,'Mistral development quality gate failed'
            assert gate['decode_policy']==m['decode_policy'] and gate['model_proof']['revision']==REV
            assert Path(gate['args']['model']).resolve()==model_path
            old=[json.loads(s) for s in (prior/'cases.jsonl').read_text().splitlines()]
            for field in ['source_id','target_name']:assert {c[field] for c in cases}.isdisjoint({c[field] for c in old})
            m['development_gate_manifest_sha256']=sha((prior/'manifest.json').read_bytes())
        tokenizer=AutoTokenizer.from_pretrained(model_path,local_files_only=True,trust_remote_code=False,use_fast=True)
        front=[]
        for c in cases:
            validate_case(c);old=original[c['case_id']]
            for field in ['prompt','expected','actor','forbidden_incomes','source_id','target_name']:assert c[field]==old[field]
            text,ids,cut=native_parts(tokenizer,messages(c))
            assert text==c['full_text'] and ids==c['input_ids'] and cut==c['prefix_tokens']
            assert c['prefix_ids']==ids[:cut] and c['suffix_ids']==ids[cut:]
            for query in ["Who is the user's supervisor?",'Is any salary information available?']:
                msg=messages(c);msg[1]['content']=query;_,alt_ids,alt_cut=native_parts(tokenizer,msg)
                assert ids[:cut]==alt_ids[:alt_cut]
            front.append(dict(case_id=c['case_id'],native_ids_exact_to_candidate=True,oracle_checked=True,prefix_query_blind_probes_exact=True))
        (root/'cases.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases),encoding='utf-8')
        save(root/'message_checks.json',front)
        grade,mapping=author_salary_grader(origin_path/'upstream/scripts/grade.py')
        torch.manual_seed(20261028);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=False
        m.update(status='running',planned_rows=24);save(root/'manifest.json',m)
        model=AutoModelForCausalLM.from_pretrained(model_path,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True,trust_remote_code=False).eval().to('cuda:0')
        assert len(model.model.layers)==32 and all(layer.self_attn.config.sliding_window is None for layer in model.model.layers)
        assert all(param.dtype==torch.bfloat16 for param in model.parameters())
        per_token=2*config.num_hidden_layers*config.num_key_value_heads*(config.hidden_size//config.num_attention_heads)*next(model.parameters()).element_size()
        assert per_token==131072
        rows=[];checks=[];done=set()
        with (root/'generations.jsonl').open('w',encoding='utf-8') as f:
            for c in cases:
                text,ids=native_generate(model,tokenizer,c['input_ids'],512,repetition_penalty=1.)
                row={k:c[k] for k in ['case_id','base','condition','source_id','source_row_index','expected','input_tokens','prefix_tokens']}
                row.update(text=text,ids=ids,metrics=judge(text,c,grade,mapping),generation_at_limit=len(ids)>=512)
                rows.append(row);m['rows']=len(rows);f.write(json.dumps(row)+'\n');f.flush()
                if c['condition'] not in done:
                    with torch.inference_mode():
                        reference=DynamicCache();model.model(torch.tensor([c['prefix_ids']],device=model.device),past_key_values=reference,use_cache=True)
                    measured=cache_bytes(reference);assert measured==len(c['prefix_ids'])*per_token
                    branch=clone_cache(reference);_,cached=native_generate(model,tokenizer,c['suffix_ids'],512,branch,len(c['prefix_ids']),repetition_penalty=1.);del branch
                    branch=clone_cache(reference);_,custom,_=generate(model,tokenizer,branch,len(c['prefix_ids']),c['suffix_ids'],512);del branch,reference
                    checks.append(dict(case_id=c['case_id'],bytes_per_prefix_token=per_token,full_prefix_kv_bytes=measured,
                        native_ids=ids,cached_ids=cached,custom_ids=custom,native_cached_exact=ids==cached,custom_cached_exact=ids==custom))
                    save(root/'correctness_checks.json',checks);assert ids==cached==custom,'Mistral cache-path token parity failed'
                    done.add(c['condition'])
                save(root/'summary.json',summarize(rows));save(root/'manifest.json',m)
                print('CASE',c['case_id'],row['metrics']['correct'],flush=True)
        result=summarize(rows);m.update(status='complete',end_unix=time.time(),full_baseline_gate=result['full_baseline_gate'])
        save(root/'manifest.json',m);save(root/'summary.json',result);print('COMPLETE',json.dumps(result),flush=True)
    except Exception as error:
        m.update(status='failed',end_unix=time.time(),error_type=type(error).__name__,error_message=str(error));save(root/'manifest.json',m);raise


if __name__=='__main__':main()
