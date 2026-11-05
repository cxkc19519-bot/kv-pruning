"""Server-only pinned draft download and paired tokenizer audit; no inference."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback
from urllib.request import Request, urlopen


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-dir',required=True)
    a=ap.parse_args();root=Path(__file__).resolve().parents[1]
    assert os.name=='posix'
    out=Path(a.run_dir).resolve();assert out.parent==root/'results';out.mkdir(exist_ok=False)
    specpath=root/'configs/controller-draft-pinned-v1.json'
    spec=json.loads(specpath.read_text());rev='c1899de289a04d12100db370d81485cdf75e47ca'
    assert spec['repo_id']=='Qwen/Qwen3-0.6B' and spec['revision']==rev
    dest=root/'models/Qwen3-0.6B'/rev;dest.mkdir(parents=True,exist_ok=True)
    target=root/'models/Qwen3-8B/b968826d9c46dd6066d109eabc6255188de91218'
    state=dict(status='running',pid=os.getpid(),start_unix=time.time(),rows=0,
               model_outputs=0,model_dir=str(dest),files=[],max_seconds=900,
               network_metadata_precheck=['Official HF server read failed Network unreachable',
                   'HF-mirror revision metadata returned HTTP403; official web API supplied pinned entries'])
    (out/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out/'official_selected_spec.json').write_bytes(specpath.read_bytes())
    log=(out/'attempts.jsonl').open('x')
    def save(): (out/'summary.json').write_text(json.dumps(state,indent=2)+'\n')
    def event(**x):log.write(json.dumps(x)+'\n');log.flush()
    def timeout(*_):raise TimeoutError('900 second preparation bound')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(900);save()
    try:
        for e in sorted(spec['files'],key=lambda x:x['size']):
            name=e['rfilename'];p=dest/name
            assert p.parent==dest and not p.is_symlink()
            def verify(q):
                assert q.stat().st_size==e['size'],name+' size mismatch'
                if e.get('lfs'):assert sha(q)==e['lfs']['sha256'],name+' sha mismatch'
                else:
                    raw=q.read_bytes()
                    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==e['blobId'],name+' git blob mismatch'
            if p.exists():verify(p)
            else:
                part=dest/(name+'.part');assert not part.exists(),'Do not overwrite an unreviewed partial'
                failures=[]
                urls=[f'https://www.modelscope.cn/models/{spec["repo_id"]}/resolve/master/{name}',
                      f'https://hf-mirror.com/{spec["repo_id"]}/resolve/{rev}/{name}',
                      f'https://huggingface.co/{spec["repo_id"]}/resolve/{rev}/{name}']
                for u in urls:
                    event(file=name,url=u,event='attempt')
                    try:
                        with urlopen(Request(u,headers={'User-Agent':'kv-pruning-pinned-draft'}),timeout=25) as resp:
                            assert resp.status==200
                            n=0
                            with part.open('wb') as f:
                                while True:
                                    b=resp.read(4*1024*1024)
                                    if not b:break
                                    n+=len(b);assert n<=e['size'];f.write(b)
                        verify(part);part.rename(p);break
                    except Exception as exc:
                        event(file=name,event='failed',error=repr(exc));failures.append(repr(exc))
                else:raise RuntimeError(name+': all transports failed: '+str(failures))
            row=dict(file=name,size=p.stat().st_size,sha256=sha(p),official_digest_verified=True)
            state['files'].append(row);event(event='verified',**row);save();print('VERIFIED',name,flush=True)
        cfg=json.loads((dest/'config.json').read_text())
        assert cfg['architectures']==['Qwen3ForCausalLM'] and cfg['num_hidden_layers']==28
        assert cfg.get('sliding_window') is None and not cfg.get('use_sliding_window',False)
        assert cfg['num_attention_heads']==16 and cfg['num_key_value_heads']==8
        from transformers import AutoTokenizer
        draft=AutoTokenizer.from_pretrained(dest,local_files_only=True,trust_remote_code=False)
        tgt=AutoTokenizer.from_pretrained(target,local_files_only=True,trust_remote_code=False)
        assert draft.get_vocab()==tgt.get_vocab(),'Tokenizer token-to-id mapping differs'
        assert draft.all_special_tokens==tgt.all_special_tokens
        assert draft.all_special_ids==tgt.all_special_ids
        assert draft.chat_template==tgt.chat_template
        cases=['Hello world!','你好，约束保持。','def f(x):\n    return x + 1','12345 = 0x3039',
               '<|im_start|>assistant\n','<think>\n\n</think>\n\n','é ñ العربية 日本語','a\t b\n\n c']
        for text in cases:assert draft.encode(text)==tgt.encode(text)
        msgs=[{'role':'system','content':'Be concise.'},{'role':'user','content':'Compute 2+3.'}]
        for thinking in [True,False]:
            assert draft.apply_chat_template(msgs,add_generation_prompt=True,enable_thinking=thinking)==tgt.apply_chat_template(msgs,add_generation_prompt=True,enable_thinking=thinking)
        tokenfiles={f:dict(draft=sha(dest/f),target=sha(target/f)) for f in
                    ['tokenizer.json','tokenizer_config.json','vocab.json','merges.txt']}
        state.update(status='pass',tokenizer_mapping_exact=True,vocab_size=len(draft),
                     special_tokens_exact=True,chat_template_exact=True,text_cases=len(cases),
                     tokenfiles=tokenfiles,weights_verified=True,model_loaded=False)
    except BaseException as exc:
        state.update(status='failed',error=repr(exc));(out/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0);log.close();state['elapsed_seconds']=time.time()-state['start_unix'];save()
        (out/'manifest.json').write_text(json.dumps({p.name:sha(p) for p in out.iterdir() if p.is_file()},indent=2)+'\n')
        print(json.dumps(state,indent=2),flush=True)
    return 0 if state['status']=='pass' else 1


if __name__=='__main__':raise SystemExit(main())
