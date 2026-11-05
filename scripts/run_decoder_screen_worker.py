"""Full-first bounded screen, using accepted common-batch runtime. No generation."""
import sys
sys.dont_write_bytecode=True
import gzip
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path


def save(out,name,value):
    (out/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def main():
    out=Path(sys.argv[1]);cfg=json.loads((out/'registration_snapshot.json').read_text());root=Path(cfg['root']);directory=Path(cfg['model_path'])
    for name,h in cfg['weights'].items():
        actual=hashlib.sha256()
        with (directory/name).open('rb') as f:
            for b in iter(lambda:f.read(8388608),b''):actual.update(b)
        assert actual.hexdigest()==h
    for name,v in cfg['versions'].items():assert importlib.metadata.version(name)==v
    engineering=json.loads((root/cfg['engineering_verification']).read_text());assert engineering['operational_contract_verified']
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from pilot import WindowScores
    from common_batch_backend import CommonBatchBackend
    from decoder_objective import candidate_masks
    from decoder_screen_analysis import measurements,summarize
    torch.set_num_threads(4);torch.manual_seed(cfg['torch_seed'])
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    model=AutoModelForCausalLM.from_pretrained(str(directory),torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True,trust_remote_code=False).eval().to('cuda:0')
    assert len(model.model.layers)==28 and set(model.config.layer_types)=={'full_attention'} and not model.config.use_sliding_window
    assert all(p.dtype==torch.bfloat16 for p in model.parameters()) and model.config.num_key_value_heads==4
    tok=AutoTokenizer.from_pretrained(str(directory),local_files_only=True,trust_remote_code=False,use_fast=True)
    cases=[c for c in json.loads((root/cfg['native_inputs']).read_text()) if c['role']=='development']
    source={c['case_id']:c for c in json.loads((root/cfg['selected_cases']).read_text())}
    assert [c['case_id'] for c in cases]==cfg['development_case_ids'] and len(cases)==12
    for case in cases:
        c=source[case['case_id']];msgs=[dict(role='system',content=c['system']),dict(role='user',content=c['user'])]
        text=tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
        assert text==case['rendered'] and tok.apply_chat_template(msgs,tokenize=True,add_generation_prompt=True)==case['full_input_ids']
        assert tok(text+'{"answer":"',add_special_tokens=False)['input_ids']==case['branch_input_ids']
    save(out,'development_inputs.json',cases)
    save(out,'actual_runtime.json',dict(model_config=model.config.to_dict(),versions=cfg['versions'],Full_layers=28,KV_heads=4,bytes_per_slot=57344,
         attention='sdpa',dtype='bfloat16',tokenizer_encodes=24,tf32=False,operational_contract='common_batch_explicit_causal_v1'))
    backend=CommonBatchBackend(model,out,cfg['compute_bounds']);frozen={};fulls={};full_rows=[];plans=[];groups=[]
    def prefix(case):
        scorer=WindowScores(window=64,kernel=5);old=[tuple(x.self_attn._forward_hooks) for x in model.model.layers]
        handles=[x.self_attn.register_forward_hook(scorer.hook,with_kwargs=True) for x in model.model.layers]
        try:
            backend.path='scored_prefix';ref,unused=backend.forward(case['prefix_ids'],0)
        finally:
            for h in handles:h.remove()
        assert old==[tuple(x.self_attn._forward_hooks) for x in model.model.layers]
        scores={str(k):v.tolist() for k,v in scorer.scores.items()};assert len(scores)==28
        score_raw=json.dumps(scores,separators=(',',':'),allow_nan=False).encode()
        aggregated=[math.fsum(float(scorer.scores[l][0,h,i]) for l in range(28) for h in range(4))/112 for i in range(373)]
        plan=candidate_masks(373,186,aggregated,cfg['random_seeds'],[28,4,128,2]);assert len(plan['candidates'])==8
        return ref,score_raw,plan
    with torch.inference_mode():
        for case in cases:
            cid=case['case_id'];backend.case_id=cid;ref,scores,plan=prefix(case)
            (out/(cid+'.prefix_scores.json.gz')).write_bytes(gzip.compress(scores,mtime=0))
            before=backend.fingerprint(ref)
            backend.path='full';logits=backend.suffix(ref,case['suffix_ids'],373);backend.record_vector('full',logits)
            assert backend.fingerprint(ref)==before
            fulls[cid]=logits.tolist();frozen[cid]=(before,hashlib.sha256(scores).hexdigest(),plan)
            peak=max(logits[i].item() for i in [32,33,34,35]);pred=[i for i in [32,33,34,35] if logits[i].item()==peak]
            full_rows.append(dict(case_id=cid,gold=source[cid]['gold'],legal_argmax_ids=pred,gold_correct=pred==[32+'ABCD'.index(source[cid]['gold'])]))
            plans.append(dict(case_id=cid,reference_sha256=before,score_sha256=hashlib.sha256(scores).hexdigest(),mask_plan=plan))
            save(out,'Full_outcomes.json',full_rows);save(out,'candidate_plans.json',plans);save(out,'vectors.json',backend.vectors)
            del ref
        correct=sum(x['gold_correct'] for x in full_rows);support=correct>=10
        save(out,'Full_support.json',dict(correct=correct,total=12,threshold=10,passed=support,scope='finite_enum_branch_argmax_not_free_generation'))
        if support:
            for case in cases:
                cid=case['case_id'];backend.case_id=cid;ref,scores,plan=prefix(case)
                before=backend.fingerprint(ref);assert (before,hashlib.sha256(scores).hexdigest(),plan)==frozen[cid]
                row=dict(case_id=cid,gold=source[cid]['gold'],Full_legal_argmax_ids=next(x['legal_argmax_ids'] for x in full_rows if x['case_id']==cid),candidates=[])
                for candidate in plan['candidates']:
                    name=candidate['name'];branch=backend.copy_cache(ref,candidate['indices']);backend.validate(branch,186)
                    backend.path=name;logits=backend.suffix(branch,case['suffix_ids'],373);backend.record_vector(name,logits)
                    assert backend.fingerprint(ref)==before
                    value=measurements(fulls[cid],logits.tolist());row['candidates'].append(dict(name=name,**value))
                    del branch
                groups.append(row);save(out,'candidate_measurements.json',groups);save(out,'vectors.json',backend.vectors)
                del ref
            analysis=summarize(groups)
            assert backend.calls==132 and backend.tokens==11544 and backend.vector_count==108
        else:
            analysis=dict(decision='stop_Full_support_below10of12',development_go=False,groups=12,statistical_confirmation=False,novelty_established=False)
            assert backend.calls==24 and backend.tokens==4764 and backend.vector_count==12
        save(out,'analysis.json',analysis);save(out,'mask_records.json',list(backend.mask_records.values()))
        save(out,'screen_summary.json',dict(execution_completed=True,Full_support=support,Full_correct=correct,development_groups=12,
             forward_calls=backend.calls,input_tokens=backend.tokens,archived_logit_vectors=backend.vector_count,tokenizer_encodes=24,
             generated_tokens=0,model_answers=0,decision=analysis['decision'],development_go=analysis['development_go'],old_cross_path_gate_passed=False))
    print(json.dumps(dict(Full_correct=correct,Full_support=support,decision=analysis['decision'],vectors=backend.vector_count)),flush=True)


if __name__=='__main__':main()
