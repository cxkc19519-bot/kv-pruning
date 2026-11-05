"""Close metadata audit with independent slow/fast tokenizer agreement."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args()
    root=Path(a.run).resolve();m=json.loads((root/'manifest.json').read_text());assert m['status']=='complete'
    own_source=Path(__file__).read_bytes();(root/'closure_source_check_mistral_candidate.py').write_bytes(own_source)
    result=dict(status='checking',start_unix=time.time(),source_sha256=hashlib.sha256(own_source).hexdigest())
    try:
        for name,digest in m['source_sha256'].items():assert sha(root/('source_'+name))==digest
        for name,digest in m['input_sha256'].items():assert sha(Path(name))==digest
        assert sha(root/'official_spec.json')==m['official_spec_sha256']
        assert sha(root/'preregistration.md')==m['preregistration_sha256']
        metadata=json.loads((root/'metadata_checks.json').read_text());assert len(metadata)==10
        for item in metadata:assert sha(root/'metadata'/item['file'])==item['sha256'] and item['verified']
        from transformers import AutoTokenizer
        from audit_mistral_candidate import messages
        slow=AutoTokenizer.from_pretrained(root/'metadata',use_fast=False,local_files_only=True,trust_remote_code=False)
        assert not slow.is_fast
        checks=[]
        for stage in ['development','confirmation']:
            for c in map(json.loads,(root/(stage+'_cases.jsonl')).read_text().splitlines()):
                ids=slow.encode(c['full_text'],add_special_tokens=False)
                assert ids==c['input_ids'],'Native slow/fast tokenizer discrepancy: '+stage+'/'+c['case_id']
                assert slow.apply_chat_template(messages(c),tokenize=False,add_generation_prompt=True)==c['full_text']
                checks.append(dict(stage=stage,case_id=c['case_id'],slow_fast_ids_exact=True,slow_fast_native_render_exact=True))
        (root/'tokenizer_crosschecks.json').write_text(json.dumps(checks,indent=2));assert len(checks)==48
        import torch,sentencepiece
        result.update(status='complete',all_source_input_metadata_hashes_verified=True,slow_fast_requests=48,
            cuda_initialized=torch.cuda.is_initialized(),sentencepiece_version=sentencepiece.__version__,sentencepiece_path=sentencepiece.__file__,
            input_sha256={str(root/name):sha(root/name) for name in ['manifest.json','summary.json','official_spec.json','preregistration.md','development_cases.jsonl','confirmation_cases.jsonl','frontend_checks.json','metadata_checks.json']},
            gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader'],text=True))
        assert not result['cuda_initialized']
    except Exception as error:
        result.update(status='failed',error_type=type(error).__name__,error_message=str(error));raise
    finally:
        result['end_unix']=time.time();(root/'closure_audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))


if __name__=='__main__':main()
