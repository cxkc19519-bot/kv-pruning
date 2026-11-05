"""Explicit causal-mask suffix contract; prefix execution remains the pinned HF path."""
import hashlib
from decoder_kv_backend import SamePrefixBackend,need


class CommonBatchBackend(SamePrefixBackend):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.mask_records={}

    def forward(self,ids,logical_start,cache=None):
        if cache is None:
            return super().forward(ids,logical_start,cache)
        torch=self.torch;physical=int(cache.get_seq_length());length=len(ids)
        need(logical_start==373 and length==24 and physical in (186,373),'fixed_batch_suffix_contract')
        need(self.calls+1<=self.limits['forward_calls'] and self.tokens+length<=self.limits['input_tokens'],'resource_cap')
        self.calls+=1;self.tokens+=length
        positions=list(range(logical_start,logical_start+length));cp=list(range(physical,physical+length))
        mask=(torch.arange(physical+length,device=self.model.device)[None,:]<=torch.arange(physical,physical+length,device=self.model.device)[:,None])[None,None]
        raw=mask.cpu().numpy().tobytes();name='causal_mask_'+str(physical)+'.bool'
        digest=hashlib.sha256(raw).hexdigest()
        if name not in self.mask_records:
            (self.out/name).write_bytes(raw)
            self.mask_records[name]=dict(file=name,shape=list(mask.shape),bytes=len(raw),sha256=digest)
        else:need(self.mask_records[name]['sha256']==digest,'mask_changed')
        import json
        row=dict(call=self.calls,case_id=self.case_id,path=self.path,input_ids=ids,logical_positions=positions,
                 cache_positions=cp,physical_before=physical,physical_after_expected=physical+length,
                 attention_shape=list(mask.shape),mask_file=name,mask_sha256=digest,
                 mask_mode='explicit_full_attention_dictionary',attempted=True)
        with (self.out/'forward_trace.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
        result=self.model(input_ids=torch.tensor([ids],device=self.model.device),attention_mask={'full_attention':mask},
            position_ids=torch.tensor([positions],device=self.model.device),cache_position=torch.tensor(cp,device=self.model.device),
            past_key_values=cache,use_cache=True,logits_to_keep=1)
        need(hashlib.sha256(mask.cpu().numpy().tobytes()).hexdigest()==digest,'model_changed_supplied_mask')
        self.validate(result.past_key_values,physical+length)
        need(tuple(result.logits.shape)==(1,1,152064) and bool(torch.isfinite(result.logits).all()),'finite_logits')
        return result.past_key_values,result.logits[0,-1].float().cpu()
