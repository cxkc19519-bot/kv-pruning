"""FP32 cache/position correctness fixture, independent of real-model quality."""
import json
from pathlib import Path
import sys
import torch
from transformers import Qwen2Config, Qwen2ForCausalLM, DynamicCache
from pilot import fork_cache

torch.manual_seed(17)
config = Qwen2Config(vocab_size=80, hidden_size=64, intermediate_size=128,
                     num_hidden_layers=2, num_attention_heads=4,
                     num_key_value_heads=2, max_position_embeddings=256,
                     use_sliding_window=False, attention_dropout=0.)
config._attn_implementation = "sdpa"
model = Qwen2ForCausalLM(config).float().eval()
tokens = torch.randint(0, 80, (1, 51))
checks = []
with torch.inference_mode():
    whole = model(tokens, use_cache=False).logits[:, -7:]
    original = DynamicCache()
    model.model(tokens[:, :-7], past_key_values=original, use_cache=True)
    split = model(tokens[:, -7:], past_key_values=original,
                  position_ids=torch.arange(44,51)[None],
                  cache_position=torch.arange(44,51), use_cache=True).logits
    error = float((whole-split).abs().max())
    checks.append({"name":"fp32_split_monolithic", "max_abs_error":error,"passed":torch.allclose(whole,split,atol=2e-6,rtol=2e-5)})
    # A compressed-prefix forward must not expose future suffix tokens.
    reference = DynamicCache()
    model.model(tokens[:,:32],past_key_values=reference,use_cache=True)
    scores = {i:torch.rand(1,2,32) for i in range(2)}
    branch, idx = fork_cache(reference,scores,"snapkv_adapted",.5,[])
    branch2, _ = fork_cache(reference,scores,"snapkv_adapted",.5,[])
    suffix_a=tokens[:,32:39].clone(); suffix_b=suffix_a.clone();suffix_b[:,-1]=(suffix_b[:,-1]+1)%80
    def forward(cache,suffix):
        return model(suffix,past_key_values=cache,position_ids=torch.arange(32,39)[None],
                     cache_position=torch.arange(16,23),use_cache=True).logits
    a,b=forward(branch,suffix_a),forward(branch2,suffix_b)
    checks.append({"name":"compressed_suffix_causality","max_earlier_error":float((a[:,:-1]-b[:,:-1]).abs().max()),
                   "passed":torch.equal(a[:,:-1],b[:,:-1])})
path=Path(sys.argv[1]);path.parent.mkdir(exist_ok=True,parents=True)
path.write_text(json.dumps(checks,indent=2))
print(json.dumps(checks),flush=True)
if not all(x['passed'] for x in checks):raise SystemExit(1)
