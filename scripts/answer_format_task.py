"""Project reading/JSON task contract. Standard library only; no model I/O."""
import hashlib
import json
import re
import string
import unicodedata
from collections import Counter
from decimal import Decimal


class TaskError(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise TaskError(reason)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_key')
        result[key] = value
    return result


def reject_constant(value):
    raise TaskError('nonfinite_constant')


def check_unicode(value):
    if isinstance(value, str):
        try:
            value.encode('utf-8', errors='strict')
        except UnicodeEncodeError as exc:
            raise TaskError('invalid_unicode') from exc
    elif isinstance(value, dict):
        for key, item in value.items():
            check_unicode(key)
            check_unicode(item)
    elif isinstance(value, list):
        for item in value:
            check_unicode(item)


def strict_json(text):
    check_unicode(text)
    require(not text.lstrip(' \t\r\n').startswith('\ufeff'), 'bom')
    value = json.loads(text, object_pairs_hook=no_duplicates,
                       parse_constant=reject_constant, parse_float=Decimal)
    check_unicode(value)
    return value


def extract_candidate(raw):
    """No gold/context arguments: extraction must not know any correct answer."""
    require(isinstance(raw, str), 'raw_not_string')
    stripped = raw.strip(' \t\r\n')
    try:
        value = strict_json(raw)
    except TaskError as exc:
        return dict(format=False, candidate=None, reason=str(exc))
    except json.JSONDecodeError:
        if stripped.startswith(('{', '[', '"', '```')):
            return dict(format=False, candidate=None, reason='structured_parse_failure')
        return dict(format=False, candidate=stripped, reason='whole_plain_text')
    if isinstance(value, dict):
        answer = value.get('answer')
        if not isinstance(answer, str):
            return dict(format=False, candidate=None, reason='no_string_answer')
        good = set(value) == {'answer'} and bool(answer.strip())
        return dict(format=good, candidate=answer, reason='object_answer')
    if isinstance(value, str):
        return dict(format=False, candidate=value, reason='json_string')
    if isinstance(value, list):
        return dict(format=False, candidate=None, reason='unsupported_json_root')
    return dict(format=False, candidate=stripped, reason='json_scalar_as_plain_text')


def normalize_answer(text):
    # Independently implemented from the frozen, statically read definition.
    lowered = text.lower()
    unpunctuated = ''.join(c for c in lowered if c not in string.punctuation)
    unarticled = re.sub(r'\b(a|an|the)\b', ' ', unpunctuated)
    return ' '.join(unarticled.split())


def task_scores(candidate, golds):
    require(golds and all(isinstance(g, str) for g in golds), 'invalid_golds')
    p = normalize_answer(candidate)
    tokens = p.split()
    exact, f1 = False, 0.0
    for gold in golds:
        g = normalize_answer(gold)
        exact = exact or p == g
        gt = g.split()
        common = sum((Counter(tokens) & Counter(gt)).values())
        # This preserves the pinned v1.1 zero-overlap/empty-normalization rule.
        score = 2.0 * common / (len(tokens) + len(gt)) if common else 0.0
        f1 = max(f1, score)
    return exact, f1


def score_response(raw, golds):
    result = extract_candidate(raw)
    candidate = result['candidate']
    if candidate is None:
        result.update(em=None, f1=None, candidate_status='unavailable')
    else:
        em, f1 = task_scores(candidate, golds)
        result.update(em=em, f1=f1, candidate_status='available')
    result['joint_success'] = bool(result['format'] and result['em'])
    return result


def normalized_paragraph(context):
    return ' '.join(unicodedata.normalize('NFC', context).split())


def normalized_title(title):
    return ' '.join(unicodedata.normalize('NFC', title).casefold().split())


def validate_dataset(dataset):
    require(isinstance(dataset, dict) and dataset.get('version') == '1.1', 'wrong_version')
    articles = dataset.get('data')
    require(isinstance(articles, list) and articles, 'invalid_articles')
    ids, paragraphs, questions, answers, lengths = set(), 0, 0, 0, []
    for ai, article in enumerate(articles):
        where = f'article:{ai}'
        require(isinstance(article, dict), where + ':invalid_article')
        require(isinstance(article.get('title'), str) and article['title'].strip(), where + ':empty_title')
        require(isinstance(article.get('paragraphs'), list) and article['paragraphs'], where + ':empty_paragraphs')
        for pi, paragraph in enumerate(article['paragraphs']):
            where = f'article:{ai}/paragraph:{pi}'
            require(isinstance(paragraph, dict), where + ':invalid_paragraph')
            context = paragraph.get('context')
            require(isinstance(context, str) and context.strip(), where + ':empty_context')
            require(isinstance(paragraph.get('qas'), list) and paragraph['qas'], where + ':empty_qas')
            paragraphs += 1
            lengths.append(len(context.split()))
            for qi, qa in enumerate(paragraph['qas']):
                where = f'article:{ai}/paragraph:{pi}/question:{qi}'
                require(isinstance(qa, dict), where + ':invalid_qa')
                ident = qa.get('id')
                require(isinstance(ident, str) and ident.strip(), where + ':empty_id')
                require(ident not in ids, where + ':duplicate_question_id')
                ids.add(ident)
                require(isinstance(qa.get('question'), str) and qa['question'].strip(), where + ':empty_question')
                require(isinstance(qa.get('answers'), list) and qa['answers'], where + ':missing_answers')
                questions += 1
                for ri, answer in enumerate(qa['answers']):
                    label = where + f'/answer:{ri}'
                    require(isinstance(answer, dict), label + ':invalid_answer')
                    text, start = answer.get('text'), answer.get('answer_start')
                    require(isinstance(text, str) and text.strip(), label + ':empty_answer')
                    require(type(start) is int and start >= 0, label + ':invalid_offset')
                    require(context[start:start+len(text)] == text, label + ':source_slice_mismatch')
                    answers += 1
    return dict(articles=len(articles), paragraphs=paragraphs, questions=questions,
                answer_spans=answers, unique_question_ids=len(ids), all_source_slices_exact=True,
                paragraph_words_min=min(lengths), paragraph_words_max=max(lengths))


def article_components(articles, traversal_order=None):
    n = len(articles)
    order = list(range(n)) if traversal_order is None else list(traversal_order)
    require(sorted(order) == list(range(n)), 'invalid_traversal_order')
    parent = list(range(n))

    def root(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def join(a, b):
        a, b = root(a), root(b)
        if a != b:
            parent[max(a, b)] = min(a, b)

    seen_title, seen_context = {}, {}
    title_links, paragraph_links = 0, 0
    for ai in order:
        article = articles[ai]
        title = normalized_title(article['title'])
        if title in seen_title:
            join(ai, seen_title[title])
            title_links += 1
        else:
            seen_title[title] = ai
        context_keys = {sha256(normalized_paragraph(p['context']).encode('utf-8'))
                        for p in article['paragraphs']}
        for key in sorted(context_keys):
            if key in seen_context:
                join(ai, seen_context[key])
                paragraph_links += 1
            else:
                seen_context[key] = ai
    groups = {}
    for ai in range(n):
        groups.setdefault(root(ai), []).append(ai)
    components = []
    for indices in groups.values():
        component_id = sha256(json.dumps(indices, separators=(',', ':')).encode('utf-8'))
        components.append(dict(component_id=component_id, article_indices=indices))
    return sorted(components, key=lambda x:x['component_id']), dict(
        title_link_events=title_links, paragraph_link_events=paragraph_links)


def select_cases(dataset, config, traversal_order=None):
    articles = dataset['data']
    components, links = article_components(articles, traversal_order)
    seed = config['split']['seed_bytes_utf8_with_final_NUL'].encode('utf-8')
    require(seed == b'kv-pruning/squad-v1.1/article-split/v1\0', 'unexpected_split_seed')
    ranked = sorted(components, key=lambda x:(sha256(seed+x['component_id'].encode('ascii')), x['component_id']))
    roles = [x['role'] for x in config['split']['roles_in_rank_order'] for _ in range(x['groups'])]
    require(len(roles) == 34 and len(ranked) >= 34, 'insufficient_article_components')
    cases = []
    for rank, component in enumerate(ranked):
        component['rank'] = rank
        component['rank_sha256'] = sha256(seed+component['component_id'].encode('ascii'))
        component['split_role'] = roles[rank] if rank < 34 else 'not_selected'
        component['reason'] = 'fixed_first34' if rank < 34 else 'outside_fixed_first34'
        if rank >= 34:
            continue
        choices = [(len(p['context'].split()), sha256(p['context'].encode('utf-8')), ai, pi)
                   for ai in component['article_indices'] for pi,p in enumerate(articles[ai]['paragraphs'])]
        _, context_sha, ai, pi = min(choices, key=lambda x:(-x[0],x[1],x[2],x[3]))
        paragraph = articles[ai]['paragraphs'][pi]
        qa = min(paragraph['qas'], key=lambda x:(sha256(x['id'].encode('utf-8')),x['id']))
        context, question = paragraph['context'], qa['question']
        prefix = 'Passage:\n'+context+'\n\nQuestion:\n'
        user = prefix+question
        prompt = dict(system=config['prompt']['system'], user=user)
        cases.append(dict(case_id=qa['id'], split_role=roles[rank], context_group_id=component['component_id'],
            source_article_index=ai, source_paragraph_index=pi, source_title=articles[ai]['title'],
            context=context, question=question, answers=qa['answers'],
            context_sha256=context_sha,
            normalized_context_sha256=sha256(normalized_paragraph(context).encode('utf-8')),
            question_sha256=sha256(question.encode('utf-8')),
            gold_sha256=sha256(json.dumps(qa['answers'],ensure_ascii=False,separators=(',',':')).encode('utf-8')),
            prompt=prompt, prompt_sha256=sha256(json.dumps(prompt,ensure_ascii=False,separators=(',',':')).encode('utf-8')),
            question_start_user_character=len(prefix), context_start_user_character=len('Passage:\n'),
            context_end_user_character=len('Passage:\n')+len(context),
            context_words=len(context.split()), context_characters=len(context),
            tokenizer_checked=False, kv_budget_checked=False))
    for role in set(roles):
        a = [x for x in cases if x['split_role']==role]
        b = [x for x in cases if x['split_role']!=role]
        for field in ['case_id','context_group_id','normalized_context_sha256']:
            require(not ({x[field] for x in a} & {x[field] for x in b}), 'cross_role_overlap:'+field)
    return cases, dict(algorithm='article_components_v1', components=ranked, link_events=links,
        total_components=len(ranked), selected_cases=len(cases), roles=dict(Counter(roles)),
        cross_role_exact_overlaps=0, semantic_near_duplicate_audit=False,
        source_selection='one longest raw paragraph per article component, one hash-ranked question',
        statistical_confirmation=False)
