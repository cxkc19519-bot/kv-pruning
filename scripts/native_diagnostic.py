"""Compare recorded pilot prompts with unmodified HF model.generate (server only)."""
import argparse
import json
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

p = argparse.ArgumentParser()
p.add_argument("--model", required=True)
p.add_argument("--cases", required=True)
p.add_argument("--out", required=True)
args = p.parse_args()
torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
tok = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16,
                                          attn_implementation="sdpa", local_files_only=True).eval().to("cuda:0")
path = Path(args.out)
with path.open("x", encoding="utf-8") as f, torch.inference_mode():
    for line in Path(args.cases).read_text().splitlines()[:4]:
        case = json.loads(line)
        for request in case["requests"]:
            inputs = tok(request["full_text"], return_tensors="pt", add_special_tokens=False).to(model.device)
            generated = model.generate(**inputs, do_sample=False, repetition_penalty=1.0, max_new_tokens=24,
                                       pad_token_id=tok.eos_token_id)
            answer = tok.decode(generated[0, inputs.input_ids.shape[1]:], skip_special_tokens=True)
            row = {"case_id": case["id"], "allowed": request["allowed"], "expected": request["expected"],
                   "native_text": answer, "correct": answer.strip()==request["expected"]}
            f.write(json.dumps(row)+"\n"); f.flush()
            print(json.dumps(row), flush=True)
