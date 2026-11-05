"""CPU header/budget/selector/cache-gather preflight; no model weights or generation."""
import argparse
import ast
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import time

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, DynamicCache

from trec_pruning_utils import (gather_prefix_cache, kv_bytes, mandatory_positions,
    native_header_metadata, random_prefix_scores, select_prefix_indices, validate_indices)


PROPOSAL_SHA = "289bb122e62788cff3406df9ba42a792172b2f10959144be187271e52634093f"
PILOT_SHA = "476b3cbf8a9e16cdbb958286ba931a45d9b089f1bba4fb0a29f3a7ee9ebcdc1f"


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")


def cache_equal(a,b):
    return len(a.layers)==len(b.layers) and all(torch.equal(x.keys,y.keys) and torch.equal(x.values,y.values) for x,y in zip(a.layers,b.layers))


def synthetic_cache(n,layers=28,heads=4,dim=2):
    cache=DynamicCache()
    # Two exactly representable bfloat16 coordinates encode each original position.
    pos=torch.arange(n)
    key=torch.stack([pos//128,pos%128],dim=-1).to(torch.bfloat16)[None,None,:,:].expand(1,heads,n,dim).clone()
    for layer in range(layers):
        cache.update(key.clone(),(-key).clone(),layer)
    return cache


def hook_cpu_check(pilot_bytes):
    """Extract only the already reviewed hook class; independently check its math."""
    assert sha(pilot_bytes)==PILOT_SHA
    node=next(n for n in ast.parse(pilot_bytes).body if isinstance(n,ast.ClassDef) and n.name=="WindowScores")
    namespace=dict(torch=torch,F=F,math=math)
    exec(compile(ast.Module(body=[node],type_ignores=[]),"pinned_WindowScores","exec"),namespace)
    Hook=namespace["WindowScores"]
    reports=[]
    for n in [65,129]:
        generator=torch.Generator().manual_seed(317+n)
        heads,kv_heads,dim,hidden_size=4,2,8,32
        hidden=torch.randn(1,n,hidden_size,generator=generator)
        module=torch.nn.Module();module.q_proj=torch.nn.Linear(hidden_size,heads*dim,bias=False)
        with torch.no_grad():module.q_proj.weight.copy_(torch.randn(heads*dim,hidden_size,generator=generator)/16)
        module.config=type("Config",(),dict(num_attention_heads=heads))()
        module.layer_idx=0;module.head_dim=dim
        keys=torch.randn(1,kv_heads,n,dim,generator=generator);values=torch.randn(1,kv_heads,n,dim,generator=generator)
        cache=DynamicCache();cache.update(keys,values,0)
        angles=torch.arange(n)[:,None]/torch.tensor([1.,3.,7.,13.,1.,3.,7.,13.])[None,:]
        cos,sin=angles.cos()[None,:,:],angles.sin()[None,:,:]
        kwargs=dict(hidden_states=hidden,past_key_values=cache,position_embeddings=(cos,sin))
        before=[t.clone() for t in [hidden,keys,values,cos,sin]]
        hook=Hook(window=64,kernel=5);sentinel=object()
        with torch.no_grad():
            returned=hook.hook(module,(),kwargs,sentinel)
            first=hook.scores[0].clone()
            hook.hook(module,(),kwargs,sentinel)
            assert returned is sentinel and torch.equal(first,hook.scores[0])
            assert all(torch.equal(x,y) for x,y in zip(before,[hidden,keys,values,cos,sin]))
            w=64
            query=F.linear(hidden[:,-w:],module.q_proj.weight).reshape(1,w,heads,dim).transpose(1,2)
            rotated=query*cos[:,-w:].unsqueeze(1)+torch.cat([-query[...,dim//2:],query[...,:dim//2]],-1)*sin[:,-w:].unsqueeze(1)
            # Explicit query-head/time/key loops avoid reproducing the vectorized mask/GQA code.
            votes=torch.zeros(heads,n-w)
            for h in range(heads):
                for j in range(w):
                    logits=(rotated[0,h,j] @ keys[0,h//(heads//kv_heads),:n-w+j+1].T)/math.sqrt(dim)
                    probabilities=torch.softmax(logits,dim=-1)
                    votes[h]+=probabilities[:n-w]/w
            pooled=torch.zeros_like(votes)
            for position in range(n-w):
                pooled[:,position]=votes[:,max(0,position-2):min(n-w,position+3)].sum(-1)/5
            reference=pooled.reshape(kv_heads,heads//kv_heads,n-w).mean(1)[None,:,:]
            reference=F.pad(reference,(0,w),value=float(reference.max())+1)
            delta=float((reference-first).abs().max())
            assert torch.allclose(first,reference,atol=2e-7,rtol=2e-5),delta
        reports.append(dict(prefix_tokens=n,query_heads=heads,kv_heads=kv_heads,head_dim=dim,
                            causal_query_loop_max_abs_difference=delta,inputs_and_cache_unchanged=True,
                            deterministic_scores=True,output_object_unchanged=True))
    return reports


def rejection_checks():
    rejected=[]
    scores=torch.zeros(1,4,256)
    trials=[("protected_budget_overflow",lambda:select_prefix_indices(scores,32)),
            ("header_out_of_range",lambda:select_prefix_indices(scores,128,[256],True)),
            ("nonfinite_score",lambda:select_prefix_indices(torch.full_like(scores,float("nan")),128)),
            ("duplicate_indices",lambda:validate_indices(torch.zeros(1,4,128,dtype=torch.long),256,128,4)),
            ("missing_recent_anchor",lambda:validate_indices(torch.arange(128).expand(1,4,128),256,128,4)),
            ("invalid_budget",lambda:select_prefix_indices(scores,257))]
    for name,call in trials:
        try:call()
        except ValueError:rejected.append(name)
        else:raise AssertionError("Invalid selector input accepted: "+name)
    tied=select_prefix_indices(scores,128)
    required=mandatory_positions(256)
    expected=sorted(required+[p for p in range(256) if p not in set(required)][:128-len(required)])
    assert tied[0,0].tolist()==expected and torch.equal(tied[0,0],tied[0,3])
    return dict(expected_rejections=rejected,stable_tie_breaking_original_position=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--proposal",required=True);parser.add_argument("--tokenizer",required=True);parser.add_argument("--out",required=True)
    args=parser.parse_args();root=Path(args.out);root.mkdir(parents=True,exist_ok=False)
    sources={}
    for name in ["prepare_trec_pruning_cpu.py","trec_pruning_utils.py","pilot.py"]:
        data=Path(__file__).with_name(name).read_bytes();(root/("source_"+name)).write_bytes(data);sources[name]=sha(data)
    manifest=dict(status="preparing",rows=0,new_model_outputs=0,start_unix=time.time(),args=vars(args),command=sys.argv,
                  source_sha256=sources,scope="CPU tokenizer and synthetic-cache checks only; no model weights or generation",
                  versions={name:importlib.metadata.version(name) for name in ["torch","transformers","tokenizers"]})
    save(root/"manifest.json",manifest);inputs={}
    try:
        assert not torch.cuda.is_initialized();torch.set_num_threads(4)
        raw_proposal=Path(args.proposal).read_bytes();assert sha(raw_proposal)==PROPOSAL_SHA
        proposal=json.loads(raw_proposal);assert proposal["execution_enabled"] is False
        (root/"proposal.json").write_bytes(raw_proposal)
        raw_cases=Path(proposal["cases_path"]).read_bytes();assert sha(raw_cases)==proposal["cases_sha256"]
        cases=[json.loads(line) for line in raw_cases.decode().splitlines()];assert len(cases)==32
        baseline=Path(proposal["baseline_run"])
        baseline_raw=(baseline/"generations.jsonl").read_bytes();assert sha(baseline_raw)==proposal["baseline_generations_sha256"]
        baseline_rows=[r for r in map(json.loads,baseline_raw.decode().splitlines()) if r["condition"]=="with_demos"]
        assert [r["source_key"] for r in baseline_rows]==[c["source_key"] for c in cases]
        assert sum(r["metrics"]["exact_correct"] for r in baseline_rows)==19
        parent=Path("configs/trec-context-gate-proposal-v1.json")
        assert sha(parent.read_bytes())==proposal["parent_proposal_sha256"]
        header=json.loads(parent.read_text())["shared_system_header"]
        tokenizer=AutoTokenizer.from_pretrained(args.tokenizer,local_files_only=True)
        token_sha_path=Path("results/20261028-trec-data-preflight-v2/tokenizer_sha256.json")
        token_hashes=json.loads(token_sha_path.read_text())
        for name,d in token_hashes.items():assert sha((Path(args.tokenizer)/name).read_bytes())==d
        config=json.loads((Path(args.tokenizer)/"config.json").read_text())
        assert config["model_type"]=="qwen2" and not config.get("use_sliding_window",False)
        assert (config["num_hidden_layers"],config["num_key_value_heads"],config["hidden_size"]//config["num_attention_heads"])==(28,4,128)
        save(root/"tokenizer_sha256.json",token_hashes)
        metadata=[]
        # Freeze every real header/budget before any synthetic selector operation.
        for case in cases:
            v=case["versions"]["with_demos"]
            r=native_header_metadata(tokenizer,v["messages"],v["input_ids"],v["prefix_tokens"],header)
            assert r["required_pinned_count"]<=r["budget"]
            r.update(source_key=case["source_key"],prefix_ids=v["input_ids"][:v["prefix_tokens"]],
                     prefix_ids_sha256=sha(json.dumps(v["input_ids"][:v["prefix_tokens"]],separators=(",",":")).encode()),
                     analytical_full_prefix_bytes=r["prefix_tokens"]*57344,analytical_half_prefix_bytes=r["budget"]*57344,
                     analytical_header_bytes=r["header_count"]*57344,analytical_extra_header_bytes=r["extra_header_slots"]*57344)
            metadata.append(r)
        save(root/"header_budget_metadata.json",metadata)
        hook_checks=hook_cpu_check((root/"source_pilot.py").read_bytes());save(root/"hook_cpu_checks.json",hook_checks)
        save(root/"selector_edge_checks.json",rejection_checks())
        selection_root=root/"synthetic_maps";selection_root.mkdir()
        reports=[];all_ids={};scoring_seed=61423
        for r in metadata:
            n,budget=r["prefix_tokens"],r["budget"];key=r["source_key"]
            reference=synthetic_cache(n);before=[(layer.keys.clone(),layer.values.clone()) for layer in reference.layers]
            fixture={};maps={m["method"]:{} for m in proposal["conditions"]}
            for layer in range(28):
                seed=int.from_bytes(hashlib.sha256(json.dumps([scoring_seed,key,layer],separators=(",",":")).encode()).digest()[:8],"big")%(2**63)
                fixture[layer]=torch.rand((1,4,n),generator=torch.Generator().manual_seed(seed),dtype=torch.float32)
                random=random_prefix_scores(n,key,layer,4)
                replay=random_prefix_scores(n,key,layer,4);assert torch.equal(random,replay)
                for condition in proposal["conditions"]:
                    method=condition["method"];pinned=condition["pin_shared_header"]
                    scores=random if method.startswith("uniform_random") else fixture[layer]
                    before_scores=scores.clone()
                    indices=select_prefix_indices(scores,budget,r["header_ids"],pinned)
                    validate_indices(indices,n,budget,4,r["header_ids"],pinned)
                    assert torch.equal(scores,before_scores)
                    maps[method][layer]=indices
            checks_by_method={}
            for condition in proposal["conditions"]:
                method=condition["method"];pinned=condition["pin_shared_header"]
                compact=gather_prefix_cache(reference,maps[method],n,budget,r["header_ids"],pinned)
                assert kv_bytes(compact)==28*4*budget*2*2*2
                # Independent scalar head-wise index_select oracle checks K and V values.
                for layer in range(28):
                    for head in range(4):
                        idx=maps[method][layer][0,head]
                        assert torch.equal(compact.layers[layer].keys[0,head],reference.layers[layer].keys[0,head].index_select(0,idx))
                        assert torch.equal(compact.layers[layer].values[0,head],reference.layers[layer].values[0,head].index_select(0,idx))
                checks_by_method[method]=dict(synthetic_kv_bytes=kv_bytes(compact),layer_head_checks=112,
                                             analytical_model_prefix_bytes=budget*57344)
                del compact
            identity_maps={layer:select_prefix_indices(fixture[layer],n,r["header_ids"],True) for layer in range(28)}
            identity=gather_prefix_cache(reference,identity_maps,n,n,r["header_ids"],True)
            assert cache_equal(reference,identity) and kv_bytes(reference)==kv_bytes(identity)
            assert all(torch.equal(k,layer.keys) and torch.equal(v,layer.values) for (k,v),layer in zip(before,reference.layers))
            assert len({v["synthetic_kv_bytes"] for v in checks_by_method.values()})==1
            # Paired random variants must preserve every pre-existing selected header-external token
            # unless the extra mandatory header displaces it within the same budget.
            for layer in range(28):
                for head in range(4):
                    unpinned=set(maps["uniform_random_shared_anchors"][layer][0,head].tolist())
                    pinned=set(maps["uniform_random_shared_anchors_header_pinned"][layer][0,head].tolist())
                    assert pinned-unpinned <= set(r["header_ids"])
            packed={method:{str(layer):indices.tolist() for layer,indices in mapping.items()} for method,mapping in maps.items()}
            target=selection_root/(key+".json");save(target,packed);all_ids[str(target.relative_to(root))]=sha(target.read_bytes())
            reports.append(dict(source_key=key,prefix_tokens=n,budget=budget,header_count=r["header_count"],
                                required_pinned_count=r["required_pinned_count"],methods=checks_by_method,
                                identity_100_percent=True,reference_unchanged=True,random_replay_exact=True))
            del reference,before,identity,fixture,maps,packed
            print("CPU_CASE",len(reports),key,flush=True)
        save(root/"synthetic_cache_checks.json",reports)
        # One small full-model-shape physical gather verifies dtype/byte accounting beyond dim2 fixtures.
        n=metadata[0]["prefix_tokens"];budget=n//2
        real=DynamicCache();base=torch.zeros((1,4,n,128),dtype=torch.bfloat16)
        for layer in range(28):real.update(base.clone(),base.clone(),layer)
        real_maps={layer:select_prefix_indices(random_prefix_scores(n,metadata[0]["source_key"],layer,4),budget) for layer in range(28)}
        half=gather_prefix_cache(real,real_maps,n,budget)
        assert kv_bytes(real)==n*57344 and kv_bytes(half)==budget*57344
        save(root/"model_shape_byte_check.json",dict(prefix_tokens=n,kv_heads=4,head_dim=128,layers=28,dtype="bfloat16",
            synthetic_full_bytes=kv_bytes(real),synthetic_half_bytes=kv_bytes(half),model_weights_loaded=False))
        del real,base,half,real_maps
        summary=dict(cases=32,conditions=4,layer_head_selection_checks=32*4*28*4,identity_layer_head_checks=32*28*4,
                     header_count_range=[min(r["header_count"] for r in metadata),max(r["header_count"] for r in metadata)],
                     required_pinned_count_range=[min(r["required_pinned_count"] for r in metadata),max(r["required_pinned_count"] for r in metadata)],
                     extra_header_slots_range=[min(r["extra_header_slots"] for r in metadata),max(r["extra_header_slots"] for r in metadata)],
                     budget_range=[min(r["budget"] for r in metadata),max(r["budget"] for r in metadata)],
                     boundary_overlap_cases=sum(bool(r["boundary_overlaps"]) for r in metadata),
                     header_protection_fits_all_cases=True,equal_synthetic_bytes_all_four_methods=True,
                     random_stream_replay_exact=True,stable_tie_breaking=True,synthetic_100_percent_identity=True,
                     hook_cpu_math_and_nonmutation_passed=True,synthetic_fixture_head_dim=2,
                     full_model_shape_synthetic_check_head_dim=128,new_model_outputs=0,cuda_initialized=torch.cuda.is_initialized(),
                     actual_model_hook_cache_and_output_checks="not_run",actual_compressed_decode_checks="not_run",execution_enabled=False,
                     limitation="SnapKV selections use labeled synthetic scores here, not real model saliency. Metadata and synthetic gather correctness do not validate BF16 model hooks/Full replay or compression quality.")
        assert not torch.cuda.is_initialized()
        save(root/"summary.json",summary)
        prepared=dict(proposal,status="cpu_preflight_complete_pending_actual_model_engineering_checks",execution_enabled=False,
                      parent_proposal_sha256=PROPOSAL_SHA,cpu_preflight_run=str(root),cpu_preflight_source_sha256=sources,
                      header_budget_metadata_sha256=sha((root/"header_budget_metadata.json").read_bytes()),tokenizer_sha256=token_hashes,
                      selection_semantics="Stable score-descending selection excluding charged mandatory positions, tie by original index; original-position sorted physical gather",
                      cpu_synthetic_only=True)
        save(root/"prepared_config.json",prepared)
        for path in [Path(args.proposal),Path(proposal["cases_path"]),baseline/"manifest.json",baseline/"generations.jsonl",baseline/"execution_snapshot.json",parent,token_sha_path]:inputs[str(path)]=sha(path.read_bytes())
        manifest.update(status="complete",end_unix=time.time(),input_sha256=inputs,tokenizer_sha256=token_hashes,
                        artifact_sha256={str(p.relative_to(root)):sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and p.name!='manifest.json'},
                        cpu_engineering_gate_passed=True,model_engineering_gate_passed=False)
        save(root/"manifest.json",manifest)
        print("COMPLETE",json.dumps(summary),flush=True)
    except Exception as error:
        manifest.update(status="failed",end_unix=time.time(),input_sha256=inputs,error_type=type(error).__name__,error_message=str(error))
        save(root/"manifest.json",manifest)
        raise


if __name__=="__main__":main()
