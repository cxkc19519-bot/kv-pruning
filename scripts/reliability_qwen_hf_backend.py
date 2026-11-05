"""Lazy Qwen2.5 HF adapter. No torch/HF import or model action at module import.

The orchestration gate must authorize every call. Actual GPU behavior remains
unvalidated for this new adapter until a separately registered engineering run.
"""
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
from reliability_system_core import require
from reliability_system_adapters import hash_json


class QwenHFBackend:
    kind='real_hf'

    def __init__(self,config):
        self.config=copy.deepcopy(config);self.model=None;self.reference=None;self.scores=None;self.reference_key=None
        self.actual_runtime=None

    def _load(self):
        if self.model is not None:return
        cfg=self.config
        require(cfg.get('separate_GPU_execution_registered') is True,'GPU_protocol_not_registered')
        require(cfg.get('execution_enabled') is True,'backend_execution_disabled')
        require(os.environ.get('CUDA_VISIBLE_DEVICES')==cfg['gpu_uuid'],'GPU_UUID_mismatch')
        root=Path(cfg['project_root']).resolve();modeldir=Path(cfg['model_path'])
        require(str(root)=='/home/user/jhk/project/Directional Exploration/kv-pruning','backend_project_root')
        require(modeldir.name==cfg['model_revision'],'model_revision')
        for rel,expected in cfg['source_files'].items():require(hashlib.sha256((root/rel).read_bytes()).hexdigest()==expected,'backend_source_changed:'+rel)
        for name,expected in cfg['model_metadata_files'].items():require(hashlib.sha256((modeldir/name).read_bytes()).hexdigest()==expected,'backend_model_metadata_changed:'+name)
        versions={k:importlib.metadata.version(k) for k in cfg['versions']};require(versions==cfg['versions'],'backend_framework_version')
        device=subprocess.run(['nvidia-smi','-i',cfg['gpu_uuid'],'--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15).stdout.strip()
        used,util=[int(s.strip()) for s in device.split(',')];require(used<=cfg['idle_memory_mib_max'] and util==0,'GPU_not_idle')
        for name,expected in cfg['weights'].items():
            h=hashlib.sha256()
            with (modeldir/name).open('rb') as f:
                for b in iter(lambda:f.read(8388608),b''):h.update(b)
            require(h.hexdigest()==expected,'backend_weight_hash:'+name)
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
        import torch
        from transformers import AutoModelForCausalLM,GenerationConfig
        from trec_context_gate import native,clone_cache,cache_state
        from trec_pruning_run import scored_prefill,decode_compact,native_compact,build_maps
        from trec_pruning_utils import gather_prefix_cache,kv_bytes
        torch.set_num_threads(4);torch.manual_seed(cfg['torch_seed']);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        self.model=AutoModelForCausalLM.from_pretrained(str(modeldir),torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True,trust_remote_code=False).eval().to('cuda:0')
        require(len(self.model.model.layers)==28 and set(self.model.config.layer_types)=={'full_attention'} and not self.model.config.use_sliding_window,'backend_actual_Full_Attention')
        require(all(getattr(x.self_attn,'sliding_window',None) is None for x in self.model.model.layers),'backend_actual_sliding')
        require(all(p.dtype==torch.bfloat16 for p in self.model.parameters()),'backend_actual_dtype')
        self.decode=GenerationConfig(**cfg['decode']);self.model.generation_config=copy.deepcopy(self.decode)
        self.torch=torch;self.native=native;self.clone=clone_cache;self.cache_state=cache_state;self.prefill=scored_prefill
        self.custom=decode_compact;self.native_compact=native_compact;self.build_maps=build_maps;self.gather=gather_prefix_cache;self.kv_bytes=kv_bytes
        self.actual_runtime=dict(model_path=str(modeldir),versions=versions,decode=self.decode.to_dict(),runtime_Full_layers=28,KV_heads=4,head_dimension=128,dtype='bfloat16',bytes_per_slot=57344)

    def execute(self,request,case,spec,budget):
        material={k:case[k] for k in ['case_id','split_role','input_ids','prefix_tokens','header_ids','prompt_sha256','context_group_id']}
        require(hash_json(material)==request['case_input_digest'],'backend_input_binding')
        require(request['runtime_digest']==self.config['registered_runtime_digest'],'backend_runtime_binding')
        require(budget['state']=='ok','backend_infeasible_budget')
        require(spec['retention']==('1' if spec['condition_id']=='full' else '1/2'),'backend_retention_not_supported')
        require(spec['sink']==4 and spec['recent']==64,'backend_anchor_policy_not_supported')
        self._load()
        n=case['prefix_tokens'];suffix=case['input_ids'][n:];name=spec['condition_id'];path=request['path'];trace=None
        if path=='native_whole':
            require(name=='full','whole_path_requires_Full');ids=self.native(self.model,case['input_ids'],self.decode)
            prefix_bytes=final_bytes=None
        else:
            key=(case['case_id'],request['case_input_digest'])
            if key!=self.reference_key:
                self.reference=None;self.scores=None
                self.reference,self.scores=self.prefill(self.model,case['input_ids'][:n]);self.reference_key=key
                require(self.kv_bytes(self.reference)==n*57344,'backend_reference_KV_bytes')
                for layer in self.reference.layers:
                    require(tuple(layer.keys.shape)==tuple(layer.values.shape)==(1,4,n,128) and layer.keys.dtype==self.torch.bfloat16,'backend_reference_KV_shape')
            before=self.cache_state(self.reference)
            if name=='full':branch=self.clone(self.reference)
            else:
                condition=dict(method=name,pin_shared_header=spec['protect_system'])
                maps=self.build_maps(self.scores,case['context_group_id'],n,dict(header_ids=case['header_ids']),[condition])[name]
                branch=self.gather(self.reference,maps,n,budget['effective_slots'],case['header_ids'],spec['protect_system'])
                for li,layer in enumerate(branch.layers):
                    idx=maps[li].to(self.model.device).unsqueeze(-1).expand(1,4,budget['effective_slots'],128)
                    require(self.torch.equal(layer.keys,self.reference.layers[li].keys.gather(2,idx)) and self.torch.equal(layer.values,self.reference.layers[li].values.gather(2,idx)),'backend_gather_values')
            prefix_bytes=self.kv_bytes(branch);require(prefix_bytes==budget['effective_slots']*57344,'backend_actual_budget_bytes')
            if path=='native_split':
                require(name=='full','native_split_requires_Full');ids=self.native(self.model,suffix,self.decode,branch,n)
            elif path=='native':ids,trace=self.native_compact(self.model,branch,n,suffix,self.decode)
            else:
                require(path in ['custom','custom_split'],'unknown_backend_path')
                ids,trace=self.custom(self.model,branch,n,suffix,self.decode.max_new_tokens,set(self.decode.eos_token_id))
            final_bytes=self.kv_bytes(branch)
            require(self.cache_state(self.reference)==before,'backend_reference_mutated')
        return dict(request_digest=request['request_digest'],execution_state='ok',ids=ids,
            truncated=not (ids and ids[-1] in self.decode.eos_token_id),trace=trace,
            actual_prefix_kv_bytes=prefix_bytes,final_live_kv_bytes=final_bytes,
            runtime_metadata=self.actual_runtime,scope='Qwen2.5-only audit adapter;new wrapper GPU engineering not yet validated')
