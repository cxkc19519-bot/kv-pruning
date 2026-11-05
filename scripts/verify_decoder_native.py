"""Independent stdlib-only replay: no tokenizer, template or project imports."""
import sys
sys.dont_write_bytecode = True
from collections import Counter
import hashlib
import json
from pathlib import Path
import unicodedata


def read(p):
    return json.loads(p.read_text())


def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def main():
    out = Path(sys.argv[1])
    cfg = read(out / 'registration_snapshot.json')
    directory = Path(cfg['model']['path'])
    tj = read(directory / 'tokenizer.json')
    assert read(directory / 'vocab.json') == tj['model']['vocab']
    tc, ac = read(directory / 'tokenizer_config.json'), read(directory / 'config.json')
    assert tj['normalizer'] == dict(type='NFC') and tj['decoder']['type'] == 'ByteLevel'
    # Construct the byte alphabet by direct per-byte membership, independently of helper loop order.
    direct = set(range(33, 127)) | set(range(161, 173)) | set(range(174, 256))
    escaped = {b: chr(256 + sum(j not in direct for j in range(b))) for b in range(256) if b not in direct}
    inversion = {chr(b) if b in direct else escaped[b]: b for b in range(256)}
    vocab = {idx: bytes(inversion[c] for c in s) for s, idx in tj['model']['vocab'].items()}
    added = {t['id']: t['content'].encode() for t in tj['added_tokens']}
    assert len(vocab) == 151643 and len(added) == 22 and not set(vocab) & set(added)
    table = dict(vocab, **{})
    table.update(added)
    audit = read(out / 'vocabulary_audit.json')
    assert audit['raw_byte_table_digest'] == digest({str(i): b.hex() for i, b in vocab.items()})
    assert len({v for v in vocab.values() if len(v) == 1}) == 256
    assert ac['model_type'] == 'qwen2' and ac['num_hidden_layers'] == ac['num_attention_heads'] == 28
    assert ac['num_key_value_heads'] == 4 and ac['use_sliding_window'] is False and ac['hidden_size'] == 3584
    assert ac['vocab_size'] == 152064 and not set(range(len(table), ac['vocab_size'])) & set(vocab)
    cases, rows = read(out / 'selected_cases.json'), read(out / 'native_inputs.json')
    assert len(cases) == len(rows) == 14 and len({x['context_group_id'] for x in cases}) == 14
    assert Counter(x['role'] for x in cases) == dict(engineering=2, development=12)
    counts = Counter()
    for n, (c, row) in enumerate(zip(cases, rows)):
        role, ordinal = ('engineering', n) if n < 2 else ('development', n - 2)
        group = role + '_' + str(ordinal).zfill(2)
        assert c['case_id'] == c['context_group_id'] == row['case_id'] == row['context_group_id'] == 'decoder_' + group
        assert c['role'] == row['role'] == role
        target = ([0, 23][ordinal] if role == 'engineering' else [0, 12, 23][ordinal // 4])
        assert c['target_record'] == target and c['gold'] == 'ABCD'[ordinal % 4]
        content, question = c['user'].split('\n\n')
        facts = content.splitlines()[1:]
        assert len(facts) == 24 and content.startswith('Records:\n')
        for j, fact in enumerate(facts):
            label = c['gold'] if j == target else 'ABCD'[(n * 7 + j * 3 + 1) % 4]
            assert fact == 'Record ' + group + '_item_' + str(j).zfill(2) + ' has route ' + label + '.'
        assert question == 'Question: What is the route of ' + group + '_item_' + str(target).zfill(2) + '?'
        assert c['user'][c['question_start']:] == question and c['question'] == question
        assert c['prompt_digest'] == row['prompt_digest'] == digest(dict(system=c['system'], user=c['user']))
        assert c['gold_digest'] == row['gold_digest'] == digest(c['gold'])
        header = '<|im_start|>system\n' + c['system'] + '<|im_end|>\n<|im_start|>user\n'
        rendered = header + c['user'] + '<|im_end|>\n<|im_start|>assistant\n'
        assert row['rendered'] == rendered and row['branch_text'] == rendered + '{"answer":"'
        assert unicodedata.normalize('NFC', rendered) == rendered
        for field, text in [('full_input_ids', rendered), ('branch_input_ids', row['branch_text'])]:
            assert b''.join(table[i] for i in row[field]).decode() == text
        ids = row['branch_input_ids']
        assert ids == row['prefix_ids'] + row['suffix_ids']
        assert row['prefix_ids_sha256'] == digest(row['prefix_ids']) and row['branch_ids_sha256'] == digest(ids)
        boundary = len((header + c['user'][:c['question_start']]).encode())
        assert boundary == row['question_byte_start']
        end, prefix_ends = 0, []
        for i in ids:
            end += len(table[i])
            prefix_ends.append(end)
        cut = next((i for i, pos in enumerate(prefix_ends) if pos > boundary), len(ids))
        assert row['prefix_tokens'] == cut and row['suffix_tokens'] == len(ids) - cut
        assert row['prefix_ids'] == row['full_input_ids'][:cut]
        crossing = cut if cut < len(ids) and (prefix_ends[cut - 1] if cut else 0) < boundary < prefix_ends[cut] else None
        assert row['crossing_query_token'] == crossing
        anchors = [i for i in range(cut) if i < 4 or i >= cut - 64]
        assert row['anchors'] == anchors and row['budget_slots'] == cut // 2 >= len(anchors)
        assert row['budget_state'] == 'feasible_index_plan' and row['actual_GPU_bytes_validated'] is False and row['model_called'] is False
        assert row['predicted_bytes_per_slot'] == 2 * 28 * 4 * 128 * 2 == 57344
        if role == 'development':
            counts[(target, c['gold'])] += 1
    assert len(counts) == 12 and set(counts.values()) == {1}
    contract, graph = read(out / 'grammar_contract.json'), read(out / 'grammar_graph.json')
    outputs = {x.encode() for x in contract['outputs']}
    assert outputs == {('{"answer":"' + l + '"}').encode() for l in 'ABCD'}
    eos = next(t['id'] for t in tj['added_tokens'] if t['content'] == tc['eos_token'])
    assert eos == contract['eos_id'] == 151645
    # Independently enumerate all full-vocabulary legal edges at every reachable byte prefix.
    seen, edges, pending = {b''}, [], [b'']
    while pending:
        prefix = pending.pop()
        for token, chunk in vocab.items():
            nxt = prefix + chunk
            if any(o.startswith(nxt) for o in outputs):
                edges.append(dict(prefix_hex=prefix.hex(), token=token, next_hex=nxt.hex()))
                if nxt not in seen:
                    seen.add(nxt)
                    pending.append(nxt)
        if prefix in outputs:
            edges.append(dict(prefix_hex=prefix.hex(), token=eos, next_hex=None))
    assert outputs <= seen
    assert graph == dict(states=sorted(x.hex() for x in seen), accepted=sorted(x.hex() for x in outputs),
                         edges=sorted(edges, key=lambda e: (e['prefix_hex'], e['token'])))
    branch = b'{"answer":"'
    allowed = sorted(e['token'] for e in edges if e['prefix_hex'] == branch.hex())
    assert contract['branch_allowed'] == allowed
    for token in allowed:
        labels = [chr(o[len(branch)]) for o in outputs if o.startswith(branch + vocab[token])]
        assert contract['token_to_labels'][str(token)] == labels and len(labels) == 1
    assert {v[0] for v in contract['token_to_labels'].values()} == set('ABCD')
    assert contract['excluded_added_token_ids'] == sorted(added) and not set(allowed) & set(added)
    for p in read(out / 'adapter_probes.json'):
        assert p['NFC'] == unicodedata.normalize('NFC', p['input']) == p['decoded']
        assert b''.join(table[i] for i in p['ids']).hex() == p['bytes_hex'] == p['NFC'].encode().hex()
    summary = read(out / 'native_summary.json')
    assert summary['tokenizer_encodes'] == 34 and summary['development_groups'] == 12 and summary['half_budget_feasible'] == 14
    assert not any(x.split('.')[0] in ('torch', 'transformers', 'tokenizers', 'jinja2', 'decoder_native_inputs', 'decoder_objective') for x in sys.modules)
    result = dict(passed=True, native_inputs=14, development_groups=12, engineering_groups=2, tokenizer_encodes_observed=34,
                  additional_verifier_encodes=0, base_tokens_audited=151643, excluded_added_tokens=22,
                  forbidden_non_tokenizer_model_ids=ac['vocab_size'] - len(table), grammar_edges=len(edges),
                  legal_branch_tokens=len(allowed), half_budget_feasible=14, native_input_bytes_reconstructed=True,
                  native_canonical_BPE_reencoded_by_verifier=False, model_answers=0, GPU_queries=0)
    (out / 'independent_verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
