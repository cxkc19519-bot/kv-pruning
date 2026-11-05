"""Frozen SQuADtrain integrity/provisional split and BoolQ software checks."""
import sys
sys.dont_write_bytecode=True
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback
import urllib.request
from answer_format_task import strict_json,validate_dataset,article_components,normalized_title,normalized_paragraph
from boolq_task import score_boolq


def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=True,allow_nan=False,indent=2)+'\n')
def check(x,s):
    if not x:raise ValueError(s)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**k):raise ValueError('unexpected_redirect')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');args=ap.parse_args()
    r=Path(__file__).resolve().parent.parent;check(args.execute and str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning','server execute')
    raw=(r/'configs/independent-task-preflight-v1.json').read_bytes();cfg=json.loads(raw);o=r/cfg['run'];check(o.resolve().parent==(r/'results').resolve(),'boundary');o.mkdir(exist_ok=False)
    start=time.monotonic();s=dict(status='running',stage='software_fixtures',pid=os.getpid(),main_outputs=0,engineering_outputs=0,software_passed=0,network_requests=0)
    def timeout(*a):raise TimeoutError('90secondcap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(90)
    try:
        (o/'proposal_snapshot.json').write_bytes(raw)
        for name in ['preflight_independent_task.py','boolq_task.py','answer_format_task.py']:
            body=(r/'scripts'/name).read_bytes();(o/('source_'+name)).write_bytes(body)
            if name=='answer_format_task.py':check(sha(body)==cfg['source_module_sha256'],'source pin')
        oldraw=(r/cfg['historical_data']).read_bytes();check(sha(oldraw)==cfg['historical_data_sha256'],'historical pin')
        fixtures=[];save(o/'bool_software_fixtures.json',fixtures)
        for case in cfg['boolean_fixtures']:
            result=score_boolq(case['raw'],case['gold']);fixtures.append(dict(id=case['id'],expected=case,actual=result))
            save(o/'bool_software_fixtures.json',fixtures)
            for key in ['format','candidate','em']:check(type(result[key]) is type(case[key]) and result[key]==case[key],'fixture:'+case['id']+':'+key)
            check(result['joint_success']==bool(case['format'] and case['em']),'joint')
            check(result['candidate_status']==('unavailable' if case['candidate'] is None else 'available'),'false candidate availability')
            s['software_passed']+=1
        check(len(fixtures)==20,'fixturecount')
        s['stage']='download_fixed_source';s['network_requests']=1;save(o/'summary.json',s)
        target=o/'squad_train.source';received=0
        with urllib.request.build_opener(NoRedirect()).open(cfg['dataset_url'],timeout=25) as response:
            check(response.status==200 and response.geturl()==cfg['dataset_url'],'source endpoint')
            with target.open('xb') as f:
                while True:
                    b=response.read(65536)
                    if not b:break
                    received+=len(b);check(received<=cfg['bounds']['download_bytes_max'],'download cap');f.write(b)
        b=target.read_bytes();check(len(b)==cfg['dataset_bytes'],'source bytes')
        blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();check(blob==cfg['dataset_git_blob'],'source blob')
        save(o/'source_identity.json',dict(url=cfg['dataset_url'],bytes=len(b),git_blob_sha1=blob,sha256=sha(b),data_license='CC BY-SA4.0',author_attribution='Rajpurkar,Zhang,Lopyrev,Liang;SQuAD v1.1 training release',old_raw_unchanged=True))
        s['stage']='full_source_validation';save(o/'summary.json',s)
        data=strict_json(b.decode('utf-8'));counts=validate_dataset(data);save(o/'dataset_validation.json',counts)
        old=strict_json(oldraw.decode('utf-8'));oldtitles={normalized_title(a['title']) for a in old['data']};oldcontexts={normalized_paragraph(p['context']) for a in old['data'] for p in a['paragraphs']}
        groups,links=article_components(data['data']);seed=cfg['selection_seed'].encode();eligible=[];excluded=[]
        for g in groups:
            overlap=any(normalized_title(data['data'][ai]['title']) in oldtitles or any(normalized_paragraph(p['context']) in oldcontexts for p in data['data'][ai]['paragraphs']) for ai in g['article_indices'])
            g['rank_sha256']=sha(seed+g['component_id'].encode())
            (excluded if overlap else eligible).append(g)
        eligible.sort(key=lambda g:(g['rank_sha256'],g['component_id']))
        roles=[role for role,n in cfg['target'].items() for _ in range(n)];check(len(roles)==64 and len(eligible)>=64,'insufficient_disjoint_groups')
        selected=[];frozen_prompt=json.loads((r/'configs/answer-format-task-preflight-proposal-v1.json').read_text())['prompt']['system']
        for g,role in zip(eligible[:64],roles):
            choices=[(sha(q['id'].encode()),q['id'],ai,pi,q) for ai in g['article_indices'] for pi,p in enumerate(data['data'][ai]['paragraphs']) for q in p['qas']]
            _,_,ai,pi,qa=min(choices,key=lambda x:x[:4]);context=data['data'][ai]['paragraphs'][pi]['context'];prefix='Passage:\n'+context+'\n\nQuestion:\n'
            prompt=dict(system=frozen_prompt,user=prefix+qa['question'])
            selected.append(dict(case_id=qa['id'],task_id='squad_train_json_v1',split_role=role,context_group_id=g['component_id'],source_article_index=ai,source_paragraph_index=pi,source_title=data['data'][ai]['title'],context=context,question=qa['question'],answers=qa['answers'],prompt=prompt,prompt_sha256=sha(json.dumps(prompt,ensure_ascii=False,separators=(',',':')).encode()),gold_sha256=sha(json.dumps(qa['answers'],ensure_ascii=False,separators=(',',':')).encode()),question_start_user_character=len(prefix),context_words=len(context.split()),provisional_cross_task_overlap=True))
        check(len({x['case_id'] for x in selected})==64,'duplicate selected id')
        for role in cfg['target']:
            aa=[x for x in selected if x['split_role']==role];bb=[x for x in selected if x['split_role']!=role]
            for key in ['case_id','context_group_id']:check(not({x[key] for x in aa}&{x[key] for x in bb}),'crossroleoverlap')
        (o/'selected_provisional.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=True)+'\n' for x in selected))
        save(o/'split_manifest.json',dict(total_components=len(groups),eligible_components=len(eligible),excluded_historical_groups=excluded,selected_components=eligible[:64],not_selected_count=len(eligible)-64,roles=cfg['target'],historical_article_count=len(old['data']),old48_title_or_paragraph_overlaps=0,source_links=links,cross_task_BoolQ_audit_complete=False,inference_allowed=False))
        check(sha((r/cfg['historical_data']).read_bytes())==cfg['historical_data_sha256'],'historical changed')
        s.update(status='complete',stage='complete',source_sha256=sha(b),source_counts=counts,eligible_components=len(eligible),excluded_components=len(excluded),selected=64,cross_task_split_final=False,BoolQ_source_access=False,model_inference_allowed=False)
    except BaseException as exc:
        s.update(status='failed',error=repr(exc));(o/'failure.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0);s['elapsed_seconds']=time.monotonic()-start;save(o/'summary.json',s)
        files=[p for p in o.iterdir() if p.is_file()];check(len(files)<32 and sum(p.stat().st_size for p in files)<83886080,'archive cap')
        save(o/'manifest.json',{p.name:sha(p.read_bytes()) for p in files});print(json.dumps(s),flush=True)
    return 0 if s['status']=='complete' else 1


if __name__=='__main__':raise SystemExit(main())
