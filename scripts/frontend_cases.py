"""Fixed role/position controls. No query or answer is used for alignment."""
import copy
import json
import re


def messages(text):
    result=[dict(role=r,content=c) for r,c in re.findall(r'<\|im_start\|>(system|user)\n(.*?)<\|im_end\|>\n',text,re.S)]
    assert [m['role'] for m in result]==['system','system','user']
    return result


def spans(tok,prefix):
    enc=tok(prefix,add_special_tokens=False,return_offsets_mapping=True)
    rows=[];objects=[];cursor=0
    for line in prefix.splitlines(keepends=True):
        if line.startswith('{'):
            obj=json.loads(line);objects.append(obj.get('record_id',obj.get('member_id')))
            rows.append([i for i,(a,b) in enumerate(enc['offset_mapping']) if b>cursor and a<cursor+len(line)])
        cursor+=len(line)
    assert rows
    return enc,rows,objects


def first_fact(tok,prefix):return spans(tok,prefix)[1][0][0]


def aligned_content(tok,case,target):
    body=messages(case['requests'][0]['full_text'])[0]['content']
    n=len(case['prefix_ids']);current=first_fact(tok,case['prefix_text'])
    if current==target:return body
    assert current<target
    at=body.index('\n{')+1;k=max(0,target-current-1)
    for _ in range(12):
        inserted=body[:at]+' neutral'*k+'\n'+body[at:]
        prefix=tok.apply_chat_template([dict(role='system',content=inserted)],tokenize=False,add_generation_prompt=False)
        delta=target-first_fact(tok,prefix)
        if delta==0:break
        k+=delta;assert k>=0
    assert first_fact(tok,prefix)==target
    # Move the padding budget from after the directory to before it.
    pattern=r'\nPadding:(?: neutral)*\n$';assert re.search(pattern,inserted)
    tail=case['padding_tokens']
    for _ in range(12):
        content=re.sub(pattern,lambda _: '\nPadding:'+' neutral'*tail+'\n',inserted)
        prefix=tok.apply_chat_template([dict(role='system',content=content)],tokenize=False,add_generation_prompt=False)
        delta=n-len(tok.encode(prefix,add_special_tokens=False))
        if delta==0:break
        tail+=delta;assert tail>=0
    assert len(tok.encode(prefix,add_special_tokens=False))==n and first_fact(tok,prefix)==target
    return content


def transform(tok,case,variant,target):
    assert variant in ['original','single_matched','two_aligned','single_aligned','row_given']
    result=copy.deepcopy(case)
    aligned=variant in ['two_aligned','single_aligned'];single=variant in ['single_matched','single_aligned']
    body=aligned_content(tok,case,target) if aligned else messages(case['requests'][0]['full_text'])[0]['content']
    closed=tok.apply_chat_template([dict(role='system',content=body)],tokenize=False,add_generation_prompt=False)
    open_prefix='<|im_start|>system\n'+body
    reference_facts=[json.loads(line) for line in case['prefix_text'].splitlines() if line.startswith('{')]
    assert [json.loads(line) for line in closed.splitlines() if line.startswith('{')]==reference_facts
    bridge_count=1
    for qi,request in enumerate(result['requests']):
        old=case['requests'][qi];m=messages(old['full_text'])
        assert tok.apply_chat_template(m,tokenize=False,add_generation_prompt=True)==old['full_text']
        m[0]['content']=body
        if variant=='row_given':
            gold=next(r for r in reference_facts if r.get('record_id')==request['object'])
            assert gold['payload']==request['value'] and gold['record_group']==request['expected_record_group']
            m[1]['content']+='\nTrusted requested row (diagnostic): '+json.dumps(gold)
        if single:
            if qi==0:
                for _ in range(12):
                    merged=[dict(role='system',content=body+' neutral'*bridge_count+'\n'+m[1]['content']),m[2]]
                    text=tok.apply_chat_template(merged,tokenize=False,add_generation_prompt=True)
                    delta=len(case['prefix_ids'])+len(old['suffix_ids'])-len(tok.encode(text,add_special_tokens=False))
                    if delta==0:break
                    bridge_count+=delta;assert bridge_count>=1
                assert delta==0
            m=[dict(role='system',content=body+' neutral'*bridge_count+'\n'+m[1]['content']),m[2]]
        text=tok.apply_chat_template(m,tokenize=False,add_generation_prompt=True)
        ids=tok.encode(text,add_special_tokens=False)
        if variant!='row_given':assert len(ids)==len(case['prefix_ids'])+len(old['suffix_ids'])
        if qi==0:
            # A conservative cut in context-only trailing padding avoids BPE
            # boundary merges; runtime identity and all future questions follow.
            context=tok.encode(open_prefix,add_special_tokens=False);cut=len(context)-4
            assert ids[:cut]==context[:cut]
            prefix=tok.decode(ids[:cut],skip_special_tokens=False,clean_up_tokenization_spaces=False)
            enc,rows,objects=spans(tok,prefix)
            assert enc['input_ids']==ids[:cut] and len(rows)==case['record_count']+2
            assert objects==case['fact_row_objects']
            rule_start=prefix.index('You are a');rule_end=prefix.index('\n{')+1
            rule_ids=[i for i,(a,b) in enumerate(enc['offset_mapping']) if b>rule_start and a<rule_end]
            result.update(prefix_text=prefix,prefix_ids=enc['input_ids'],rule_ids=rule_ids,
                          fact_row_ids=rows,fact_row_objects=objects,target_length=cut,frontend=variant)
        assert ids[:cut]==result['prefix_ids']
        request.update(full_text=text,suffix_ids=ids[cut:])
    if not aligned:assert result['fact_row_ids']==case['fact_row_ids']
    else:assert result['fact_row_ids'][0][0]==target
    for a,b in zip(result['fact_row_ids'],case['fact_row_ids']):
        assert [result['prefix_ids'][i] for i in a]==[case['prefix_ids'][i] for i in b]
    n=len(result['prefix_ids']);base=set(result['rule_ids'])|set(range(4))|set(range(n-64,n))
    all_facts=base|{i for row in result['fact_row_ids'] for i in row}
    assert len(base)<=n//2 and len(all_facts)>n//2
    result['capacity_audit']=dict(prefix_tokens=n,half_budget=n//2,rules_anchors_tokens=len(base),
        all_facts_rules_anchors_tokens=len(all_facts),all_fact_pinning_feasible_at_half=False)
    result['frontend_audit']=dict(source_prefix_tokens=len(case['prefix_ids']),new_prefix_tokens=len(result['prefix_ids']),
        first_fact=result['fact_row_ids'][0][0],aligned_target=target,bridge_neutral_words=bridge_count if single else 0,
        gold_row_provided=variant=='row_given',all_directory_tokens_preserved=True,
        source_full_lengths=[len(case['prefix_ids'])+len(q['suffix_ids']) for q in case['requests']],
        new_full_lengths=[len(result['prefix_ids'])+len(q['suffix_ids']) for q in result['requests']])
    return result
