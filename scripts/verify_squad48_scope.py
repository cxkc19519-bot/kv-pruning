"""Independent stdlib graph/BFS source/selection audit of CPU SQuAD48 freeze."""
import sys
sys.dont_write_bytecode=True
from collections import Counter,defaultdict,deque
import datetime
import hashlib
import json
from pathlib import Path
import unicodedata


def read(p):return json.loads(p.read_text())
def rows(p):return list(map(json.loads,p.read_text().splitlines()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hbytes(b):return hashlib.sha256(b).hexdigest()
def title(s):return ' '.join(unicodedata.normalize('NFC',s).casefold().split())
def paragraph(s):return ' '.join(unicodedata.normalize('NFC',s).split())


def main():
    r=Path(__file__).resolve().parent.parent;assert str(r)=='/home/user/jhk/project/Directional Exploration/kv-pruning'
    d=r/'results/20261030-squad48-scope-freeze-v1';cfg=read(d/'proposal_snapshot.json');s=read(d/'summary.json')
    assert s['status']=='complete' and s['reserved_groups']==48 and s['planned_cells']==144
    for name,w in read(d/'manifest.json').items():assert sha(d/name)==w,name
    snap=read(d/'execution_snapshot.json');assert sha(d/'proposal_snapshot.json')==snap['proposal_sha256']
    assert sha(d/'source_runner.py')==snap['runner_sha256']==sha(r/cfg['runner'])
    assert sha(d/'source_validator.py')==snap['validator_sha256']==sha(Path(__file__))
    for name,w in read(d/'input_manifest.json')['files'].items():assert sha(r/name)==w,name
    train=read(r/cfg['train_source']['path']);old=read(r/cfg['historical_source']['path']);articles=train['data']
    assert train['version']=='1.1' and len(articles)==442 and len(old['data'])==48
    # Build adjacency via shared normalized keys, then BFS rather than runner union-find.
    index=defaultdict(list);allids=set();spans=questions=0;edges=[set() for _ in articles]
    for ai,a in enumerate(articles):
        index[('title',title(a['title']))].append(ai)
        for p in a['paragraphs']:
            index[('paragraph',paragraph(p['context']))].append(ai)
            for q in p['qas']:
                assert q['id'] not in allids;allids.add(q['id']);questions+=1
                for answer in q['answers']:
                    start=answer['answer_start'];assert type(start) is int and p['context'][start:start+len(answer['text'])]==answer['text'];spans+=1
    for members in index.values():
        unique=sorted(set(members))
        for ai in unique[1:]:edges[unique[0]].add(ai);edges[ai].add(unique[0])
    unseen=set(range(len(articles)));components=[]
    while unseen:
        first=min(unseen);q=deque([first]);unseen.remove(first);group=[]
        while q:
            node=q.popleft();group.append(node)
            for nxt in edges[node]:
                if nxt in unseen:unseen.remove(nxt);q.append(nxt)
        group.sort();components.append(dict(component_id=hbytes(json.dumps(group,separators=(',',':')).encode()),article_indices=group))
    components.sort(key=lambda x:x['component_id']);parent=r/Path(cfg['parent_split']).parent;pp=read(parent/'proposal_snapshot.json');split=read(r/cfg['parent_split'])
    oldtitles={title(a['title']) for a in old['data']};oldparagraphs={paragraph(p['context']) for a in old['data'] for p in a['paragraphs']}
    ranked=[];excluded=[]
    for group in components:
        conflict=any(title(articles[ai]['title']) in oldtitles or any(paragraph(p['context']) in oldparagraphs for p in articles[ai]['paragraphs']) for ai in group['article_indices'])
        group['rank_sha256']=hbytes(pp['selection_seed'].encode()+group['component_id'].encode());(excluded if conflict else ranked).append(group)
    ranked.sort(key=lambda x:(x['rank_sha256'],x['component_id']));assert ranked[:64]==split['selected_components'] and excluded==split['excluded_historical_groups']
    archived=read(d/'component_revalidation.json');assert components==archived['all_components'] and archived['exact_original_selection']
    original=rows(r/cfg['selection']['source']);assert Counter(x['split_role'] for x in original)=={'engineering':4,'development':12,'sealed_descriptive_evaluation':48}
    roles=[role for role,n in pp['target'].items() for _ in range(n)];byid={};system=original[0]['prompt']['system']
    for row,group,role in zip(original,ranked[:64],roles):
        possible=[]
        for ai in group['article_indices']:
            for pi,p in enumerate(articles[ai]['paragraphs']):
                for q in p['qas']:possible.append((hbytes(q['id'].encode()),q['id'],ai,pi,q))
        _,qid,ai,pi,q=min(possible,key=lambda x:x[:4]);p=articles[ai]['paragraphs'][pi];prefix='Passage:\n'+p['context']+'\n\nQuestion:\n';prompt=dict(system=system,user=prefix+q['question'])
        assert row['case_id']==qid and row['context_group_id']==group['component_id'] and row['split_role']==role
        assert row['source_article_index']==ai and row['source_paragraph_index']==pi and row['source_title']==articles[ai]['title'] and row['context']==p['context'] and row['question']==q['question'] and row['answers']==q['answers']
        assert row['prompt']==prompt and row['question_start_user_character']==len(prefix) and row['context_words']==len(p['context'].split())
        assert row['prompt_sha256']==hbytes(json.dumps(prompt,ensure_ascii=False,separators=(',',':')).encode())
        assert row['gold_sha256']==hbytes(json.dumps(q['answers'],ensure_ascii=False,separators=(',',':')).encode())
        byid[qid]=row
    selected=rows(d/'selected48.jsonl');expected=[x for x in original if x['split_role']=='sealed_descriptive_evaluation'];assert selected==expected and len(selected)==48
    assert len({x['case_id'] for x in original})==len({x['context_group_id'] for x in original})==64
    # Full-article titles/passages are disjoint across the64selected components, not just question paragraphs.
    selectedarticle_sets=[]
    for group in ranked[:64]:
        titles={title(articles[i]['title']) for i in group['article_indices']};texts={paragraph(p['context']) for i in group['article_indices'] for p in articles[i]['paragraphs']}
        assert not(titles&oldtitles or texts&oldparagraphs)
        for t,c in selectedarticle_sets:assert not(titles&t or texts&c)
        selectedarticle_sets.append((titles,texts))
    contract=read(r/cfg['decision_contract']);conditions=contract['candidate_conditions'];cells=rows(d/'planned_cells.jsonl')
    assert len(cells)==144 and len({(x['case_id'],x['condition_id']) for x in cells})==144
    assert [(x['case_id'],x['condition_id']) for x in cells]==[(c['case_id'],condition['id']) for c in selected for condition in conditions]
    for cell in cells:
        c=byid[cell['case_id']];condition=next(x for x in conditions if x['id']==cell['condition_id'])
        assert cell['condition_contract']==condition and cell['context_group_id']==c['context_group_id'] and cell['prompt_sha256']==c['prompt_sha256'] and cell['gold_sha256']==c['gold_sha256']
        assert cell['plan_state']=='planned' and cell['execution_state']=='not_run' and not cell['model_called'] and cell['budget_state']=='not_checked'
        assert all(x is None for x in cell['metrics'].values()) and cell['engineering_evidence_state']=='not_registered_for_new_cohort'
    scope=read(d/'scope_manifest.json');assert scope['question_ids']==[x['case_id'] for x in selected] and not scope['model_inference_enabled'] and scope['oldcross_task_BoolQ_audit_complete'] is False
    assert not scope['Full_support'] and not scope['engineering_pass'] and not scope['tokenizer_checked']
    guard=read(d/'CPU_guard_observations.json');assert not any(guard.values())
    assert questions==spans==87599 and s['source_input_bytes']<=cfg['resource_bounds']['max_source_bytes']
    launch=read(Path(str(d)+'.launch.json'));assert launch['exit_code']==0 and not launch.get('watchdog_expired',False)
    for pid in [s['pid'],launch['launcher_pid']]:assert not Path('/proc/'+str(pid)).exists()
    assert not any(name.split('.')[0] in ['torch','transformers','tokenizers','vllm'] for name in sys.modules)
    result=dict(status='passed',checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verifier_sha256=sha(Path(__file__)),independent_BFS_components=len(components),source_questions=questions,source_gold_spans_revalidated=spans,original64_selection_and_prompt_gold_exact=True,exact48_ids_order_and_groups=True,all64_article_level_title_context_sets_disjoint=True,entire_historical_articles_excluded=48,planned_cells=144,source_input_files_rehashed=len(read(d/'input_manifest.json')['files']),all_metrics_unmeasured=True,model_or_tokenizer_imports=False,model_answers=0,tokenizer_encodes=0,GPU_queries=0,network_requests=0,own_worker_and_launcher_exited=True,scientific_confirmation=False)
    p=d/'independent_verification.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':main()
