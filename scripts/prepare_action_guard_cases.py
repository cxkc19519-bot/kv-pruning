"""CPU native-front-end audit and deterministic task cohort; no model inference."""
import argparse
from collections import Counter, defaultdict
import gc
import hashlib
import json
from pathlib import Path
import shutil
import time
import traceback

from action_guard_native import encode_rendered, render_case, schema_ok, source_namespace, strict_judgment


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--config',required=True)
    p.add_argument('--data-run',required=True)
    p.add_argument('--tokenizer-json',required=True)
    p.add_argument('--out',required=True)
    args=p.parse_args()
    root=Path(args.out);root.mkdir(parents=True,exist_ok=False)
    raw_config=Path(args.config).read_bytes();c=json.loads(raw_config)
    assert c['execution_enabled'] is False
    source=Path(__file__).read_bytes();helper=Path(__file__).with_name('action_guard_native.py').read_bytes()
    (root/'source_prepare.py').write_bytes(source);(root/'source_action_guard_native.py').write_bytes(helper)
    (root/'config.json').write_bytes(raw_config)
    m=dict(status='running',start_unix=time.time(),args=vars(args),rows=0,new_model_outputs=0,
           source_sha256=sha(source),helper_sha256=sha(helper),config_sha256=sha(raw_config),
           model_weights_loaded=False,model_forward_executed=False,recorded_tools_executed=False)
    save(root/'manifest.json',m)
    try:
        from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
        import transformers
        import torch
        origin=Path(c['native_source_run'])
        ns, native_hashes=source_namespace(origin)
        modelsrc=origin/'upstream/model'
        candidate=root/'candidate_tokenizer';candidate.mkdir()
        for name in ['config.json','tokenizer_config.json']:
            shutil.copy2(modelsrc/name,candidate/name)
        raw_tokenizer=Path(args.tokenizer_json).read_bytes()
        assert sha(raw_tokenizer)=='aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4'
        (candidate/'tokenizer.json').write_bytes(raw_tokenizer)
        tokenizer=AutoTokenizer.from_pretrained(candidate,local_files_only=True,trust_remote_code=False)
        cfg=AutoConfig.from_pretrained(candidate,local_files_only=True,trust_remote_code=False)
        assert cfg.num_hidden_layers==36 and cfg.num_key_value_heads==8 and cfg.head_dim==128
        assert not cfg.use_sliding_window and cfg.sliding_window is None
        assert cfg.layer_types==['full_attention']*36
        with torch.device('meta'):
            model=AutoModelForCausalLM.from_config(cfg,torch_dtype=torch.bfloat16,attn_implementation='eager')
        assert all(p.device.type=='meta' for p in model.parameters())
        assert len(model.model.layers)==36
        assert all(layer.attention_type=='full_attention' for layer in model.model.layers)
        index=json.loads((modelsrc/'model.safetensors.index.json').read_text())
        state=set(model.state_dict());ckpt=set(index['weight_map'])
        assert (state ^ ckpt) <= {'lm_head.weight','model.embed_tokens.weight'}
        assert model.get_input_embeddings().weight is model.get_output_embeddings().weight
        meta=dict(parameters=sum(p.numel() for p in model.parameters()), layers=36, all_full_attention=True,
                  bf16_kv_bytes_per_token=2*2*36*8*128,checkpoint_index_key_count=len(ckpt),
                  meta_key_count=len(state),tied_weight_key_difference=sorted(state^ckpt),
                  transformers=transformers.__version__,torch=torch.__version__,
                  cuda_initialized=torch.cuda.is_initialized(),model_forward_executed=False,
                  caveat='Meta-device shape/configuration compatibility only; no real weights, logits or original-framework reproduction.')
        del model;gc.collect()
        fixtures=[('<Judgment>safe</Judgment>',0),('<Judgment>unsafe</Judgment>',1),
                  ('The action is unsafe.',None),('<Judgment>unsafe</Judgment><Judgment>safe</Judgment>',None),
                  ('<Judgment>unsafe',None),('<Judgment>SAFE</Judgment>',0)]
        assert all(strict_judgment(text)==gold for text,gold in fixtures)
        schema='<Analysis>Enough evidence.</Analysis><Judgment>safe</Judgment><RiskSourcePresent>no</RiskSourcePresent><RiskSource>none</RiskSource>'
        assert schema_ok(schema) and not schema_ok('extra '+schema)
        data_root=Path(args.data_run)
        dm=json.loads((data_root/'manifest.json').read_text());assert dm['status']=='complete'
        records=[];inputs={};seen=defaultdict(set);errors=[]
        rule=c['cohort_rule']
        for file in dm['files']:
            path=data_root/'upstream'/file['path'];raw=path.read_bytes();assert sha(raw)==file['sha256']
            domain=path.stem
            for row_index,row in enumerate(json.loads(raw)):
                key=f'{domain}/{row["id-interaction"]}/{row["id-segment"]}/{row_index}'
                rec=dict(key=key,domain=domain,source_path=file['path'],source_row=row_index,
                         interaction=str(row['id-interaction']),segment=str(row['id-segment']),gold=row['score'])
                assert row['score'] in (0,1), f'Non-binary gold {key}'
                rec['gold']=int(row['score'])
                rec['sort_hash']=sha((rule['salt']+'|'+key).encode())
                try:
                    rendered,layout=render_case(row,ns)
                    full=encode_rendered(rendered['full'],tokenizer)
                    nohist=encode_rendered(rendered['no_history'],tokenizer)
                    prompt_sha=sha(rendered['full']['prompt'].encode())
                    seen[prompt_sha].add(rec['gold'])
                    rec.update(layout,full_tokens=full['full_token_count'],history_tokens=full['history_token_count'],
                               no_history_tokens=nohist['full_token_count'],prefix_length=full['prefix_length'],
                               prompt_sha256=prompt_sha,eligible=(rule['history_token_min']<=full['history_token_count']<=rule['history_token_max']
                                 and full['full_token_count']<=rule['full_input_token_max']
                                 and layout['prior_agent_steps']>=rule['minimum_prior_agent_steps']))
                    if rec['eligible']:
                        inputs[key]=dict(**rec,raw_source=row,rendered=rendered,encoded={'full':full,'no_history':nohist})
                except Exception as e:
                    rec.update(eligible=False,front_end_error=type(e).__name__+': '+str(e));errors.append(rec)
                records.append(rec)
        conflicts=[h for h,labels in seen.items() if len(labels)>1]
        (root/'all_source_metadata.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
        pools=defaultdict(lambda:defaultdict(list))
        for r in records:
            if r.get('eligible'):pools[r['gold']][r['domain']].append(r)
        for domains in pools.values():
            for pool in domains.values():pool.sort(key=lambda r:r['sort_hash'])
        selected=[];used_groups=set();used_prompts=set()
        # Unsafe first reserves scarce positive groups; each label rotates domains.
        for gold,target in [(1,rule['unsafe_cases']),(0,rule['safe_cases'])]:
            chosen=[];domains=sorted(pools[gold]);position={d:0 for d in domains}
            while len(chosen)<target:
                progress=False
                for domain in domains:
                    pool=pools[gold][domain]
                    while position[domain]<len(pool):
                        r=pool[position[domain]];position[domain]+=1
                        group=(domain,r['interaction'])
                        if group in used_groups or r['prompt_sha256'] in used_prompts:continue
                        chosen.append(r);used_groups.add(group);used_prompts.add(r['prompt_sha256']);progress=True;break
                    if len(chosen)==target:break
                if not progress:break
            selected.extend(chosen)
        selected.sort(key=lambda r:r['sort_hash'])
        gate=len(selected)==32 and not conflicts and not errors
        cases=[inputs[r['key']] for r in selected]
        (root/'provisional_cases.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in cases))
        summary=dict(n_source=len(records),gold_counts=dict(Counter(r['gold'] for r in records)),
                     eligible_counts={str(g):{d:len(v) for d,v in ds.items()} for g,ds in pools.items()},
                     selected=len(cases),selected_labels=dict(Counter(r['gold'] for r in cases)),
                     selected_domains=dict(Counter(r['domain'] for r in cases)),unique_interactions=len(used_groups),
                     exact_input_conflicts=len(conflicts),native_frontend_errors=len(errors),
                     cpu_gate=gate,model_registration_ready=False,
                     remaining_gate='Public training-overlap audit and frozen Full-only execution proposal are still required.',
                     meta_model=meta,native_source_sha256=native_hashes,
                     input_case_sha256=sha((root/'provisional_cases.jsonl').read_bytes()),
                     tokenizer_sha256=sha(raw_tokenizer),fixtures_checked=len(fixtures)+2,
                     scope='Only CPU/meta shapes and reviewed pure upstream native serializers/parsers; no benchmark executor or model forward.')
        save(root/'summary.json',summary)
        m.update(status='complete',end_unix=time.time(),cpu_gate=gate,model_registration_ready=False,
                 artifact_sha256={str(f.relative_to(root)):sha(f.read_bytes()) for f in root.rglob('*') if f.is_file() and f.name!='manifest.json'})
    except Exception as e:
        m.update(status='failed',end_unix=time.time(),error_type=type(e).__name__,error_message=str(e),traceback=traceback.format_exc());raise
    finally:save(root/'manifest.json',m)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
