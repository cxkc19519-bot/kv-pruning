"""Frozen synthetic development inputs and byte-level Qwen grammar adapter.

This is a controlled retrieval diagnostic, not an independent public benchmark.
The adapter requires the exact pinned BPE/ByteLevel metadata and NFC inputs.
"""
import hashlib
import json
import unicodedata


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def build_cases():
    system = ('Read the records and find the route of the exact item named in the question. '
              'Return exactly one JSON object with only the key "answer". '
              'The answer must be one of "A", "B", "C", "D". Do not add explanation.')
    cases = []
    for index in range(14):
        engineering = index < 2
        ordinal = index if engineering else index - 2
        group = ('engineering_' if engineering else 'development_') + str(ordinal).zfill(2)
        target = [0, 12, 23][(ordinal // 4) % 3] if not engineering else [0, 23][ordinal]
        label = 'ABCD'[ordinal % 4]
        lines = []
        for j in range(24):
            item = group + '_item_' + str(j).zfill(2)
            route = label if j == target else 'ABCD'[(index * 7 + j * 3 + 1) % 4]
            lines.append('Record ' + item + ' has route ' + route + '.')
        context = 'Records:\n' + '\n'.join(lines) + '\n\n'
        question = 'Question: What is the route of ' + group + '_item_' + str(target).zfill(2) + '?'
        user = context + question
        cases.append(dict(case_id='decoder_' + group, context_group_id='decoder_' + group,
                          role='engineering' if engineering else 'development', system=system, user=user,
                          question=question, question_start=len(context), gold=label, target_record=target,
                          source='synthetic_generator_frozen_before_tokenizer_or_model_results',
                          prompt_digest=digest(dict(system=system, user=user)), gold_digest=digest(label)))
    return cases


def byte_vocabulary(tokenizer_json):
    model = tokenizer_json['model']
    assert tokenizer_json['normalizer'] == dict(type='NFC')
    assert tokenizer_json['decoder']['type'] == 'ByteLevel'
    assert tokenizer_json['decoder'].get('add_prefix_space') is False
    assert model['type'] == 'BPE' and model['byte_fallback'] is False
    assert model['continuing_subword_prefix'] == model['end_of_word_suffix'] == ''
    assert model['dropout'] is None and model['unk_token'] is None
    alphabet = list(range(ord('!'), ord('~') + 1)) + list(range(ord('¡'), ord('¬') + 1)) + list(range(ord('®'), ord('ÿ') + 1))
    chars, extra = list(alphabet), 0
    for b in range(256):
        if b not in alphabet:
            alphabet.append(b)
            chars.append(256 + extra)
            extra += 1
    inverse = {chr(c): b for b, c in zip(alphabet, chars)}
    vocab = {i: bytes(inverse[ch] for ch in token) for token, i in model['vocab'].items()}
    assert len(vocab) == len(model['vocab']) and all(vocab.values())
    added = {t['id']: t['content'].encode() for t in tokenizer_json['added_tokens']}
    assert not set(vocab) & set(added)
    assert len({b for b in vocab.values() if len(b) == 1}) == 256
    return vocab, added


def grammar_vocabulary(outputs, vocab):
    # Every token that could occur at any valid byte prefix is a substring.
    substrings = {s[i:j] for text in outputs for s in [text.encode()] for i in range(len(s)) for j in range(i + 1, len(s) + 1)}
    return {i: b for i, b in vocab.items() if b in substrings}


def reconstruct(ids, vocab, added):
    return b''.join(vocab[i] if i in vocab else added[i] for i in ids)


def native_rows(cases, backend, template, vocab, added):
    rows, encodes = [], 0
    for case in cases:
        messages = [dict(role='system', content=case['system']), dict(role='user', content=case['user'])]
        rendered = template.render(messages=messages, add_generation_prompt=True, tools=None)
        header = '<|im_start|>system\n' + case['system'] + '<|im_end|>\n'
        before_user = header + '<|im_start|>user\n'
        expected = before_user + case['user'] + '<|im_end|>\n<|im_start|>assistant\n'
        assert rendered == expected and unicodedata.normalize('NFC', rendered) == rendered
        full = backend.encode(rendered, add_special_tokens=False).ids
        branch_text = rendered + '{"answer":"'
        branch = backend.encode(branch_text, add_special_tokens=False).ids
        encodes += 2
        assert reconstruct(full, vocab, added).decode() == rendered
        assert reconstruct(branch, vocab, added).decode() == branch_text
        # Do not assume encode(prompt)+encode(wrapper) equals encode(prompt+wrapper).
        boundary = len((before_user + case['user'][:case['question_start']]).encode())
        ends, pos = [], 0
        for i in branch:
            pos += len(vocab[i] if i in vocab else added[i])
            ends.append(pos)
        n = sum(end <= boundary for end in ends)
        assert n > 0 and all(end > boundary for end in ends[n:])
        assert branch[:n] == full[:n]
        prefix_bytes = reconstruct(branch[:n], vocab, added)
        assert (before_user + case['user'][:case['question_start']]).encode().startswith(prefix_bytes)
        slots = n // 2
        anchors = sorted(set(range(min(4, n))) | set(range(max(0, n - 64), n)))
        rows.append(dict(case_id=case['case_id'], context_group_id=case['context_group_id'], role=case['role'],
                         rendered=rendered, branch_text=branch_text, full_input_ids=full, branch_input_ids=branch,
                         prefix_ids=branch[:n], suffix_ids=branch[n:], prefix_tokens=n, suffix_tokens=len(branch) - n,
                         prefix_ids_sha256=digest(branch[:n]), branch_ids_sha256=digest(branch),
                         prompt_digest=case['prompt_digest'], gold_digest=case['gold_digest'], question_byte_start=boundary,
                         crossing_query_token=(n if n < len(ends) and (ends[n - 1] if n else 0) < boundary < ends[n] else None),
                         native_prompt_prefix_stable=branch[:len(full)] == full,
                         anchors=anchors, budget_slots=slots, predicted_bytes_per_slot=57344,
                         budget_state='feasible_index_plan' if len(anchors) <= slots else 'infeasible_anchor_capacity',
                         actual_GPU_bytes_validated=False, model_called=False))
    return rows, encodes
