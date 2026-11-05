"""Offline tokenizers-only worker for the registered14-input CPU preflight."""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.metadata
import json
from pathlib import Path
import unicodedata


def save(out, name, value):
    (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    out = Path(sys.argv[1])
    cfg = json.loads((out / 'registration_snapshot.json').read_text())
    for name, version in cfg['versions'].items():
        assert importlib.metadata.version(name) == version
    from tokenizers import Tokenizer
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    import decoder_native_inputs as helper
    from decoder_objective import FiniteByteGrammar
    directory = Path(cfg['model']['path'])
    meta = {name: json.loads((directory / name).read_text()) for name in ('config.json', 'tokenizer.json', 'tokenizer_config.json')}
    ac, tj, tc = [meta[k] for k in ('config.json', 'tokenizer.json', 'tokenizer_config.json')]
    assert ac['model_type'] == 'qwen2' and ac['num_hidden_layers'] == ac['num_attention_heads'] == 28
    assert ac['num_key_value_heads'] == 4 and not ac['use_sliding_window']
    assert 'layer_types' not in ac or set(ac['layer_types']) == {'full_attention'}
    assert 2 * 28 * 4 * (ac['hidden_size'] // 28) * 2 == 57344
    assert hashlib.sha256(tc['chat_template'].encode()).hexdigest() == cfg['model']['chat_template_sha256']
    assert tc['clean_up_tokenization_spaces'] is False
    vocab, added = helper.byte_vocabulary(tj)
    backend = Tokenizer.from_file(str(directory / 'tokenizer.json'))
    template = ImmutableSandboxedEnvironment().from_string(tc['chat_template'])
    cases = helper.build_cases()
    assert len(cases) == 14 and len({c['context_group_id'] for c in cases}) == 14
    save(out, 'selected_cases.json', cases)
    outputs = ['{"answer":"' + letter + '"}' for letter in 'ABCD']
    eos = next(t['id'] for t in tj['added_tokens'] if t['content'] == tc['eos_token'])
    relevant = helper.grammar_vocabulary(outputs, vocab)
    grammar = FiniteByteGrammar(outputs, relevant, eos)
    graph = grammar.reachable()
    branch_prefix = b'{"answer":"'
    allowed = grammar.allowed(branch_prefix)
    mapping = {str(i): [label for label, text in zip('ABCD', outputs) if text.encode().startswith(branch_prefix + relevant[i])] for i in allowed}
    assert len(allowed) >= 4 and all(len(labels) == 1 for labels in mapping.values())
    assert set(x[0] for x in mapping.values()) == set('ABCD')
    assert not set(allowed) & set(added)
    save(out, 'grammar_graph.json', graph)
    save(out, 'grammar_contract.json', dict(outputs=outputs, eos_id=eos, wrapper=branch_prefix.decode(),
         relevant_vocabulary={str(i): b.hex() for i, b in relevant.items()}, branch_allowed=allowed, token_to_labels=mapping,
         excluded_added_token_ids=sorted(added), non_base_model_logit_ids_forbidden=True,
         EOS_only_at_complete_string=True, local_mask_not_sequence_conditioning=True))
    # Decoding the concatenated real IDs is checked, never decode isolated UTF8 fragments.
    probes = []
    for text in ['{"answer":"A"}', '{"answer":"é"}', 'e\u0301', 'é', '汉字', '🙂']:
        ids = backend.encode(text, add_special_tokens=False).ids
        raw = helper.reconstruct(ids, vocab, added)
        expected = unicodedata.normalize('NFC', text)
        assert raw.decode() == expected and backend.decode(ids, skip_special_tokens=False) == expected
        probes.append(dict(input=text, NFC=expected, ids=ids, decoded=raw.decode(), bytes_hex=raw.hex()))
    rows, encodes = helper.native_rows(cases, backend, template, vocab, added)
    for row in rows:
        assert len(row['branch_input_ids']) <= cfg['bounds']['max_input_tokens']
        assert row['budget_state'] == 'feasible_index_plan'
        assert backend.decode(row['branch_input_ids'], skip_special_tokens=False) == row['branch_text']
    save(out, 'native_inputs.json', rows)
    save(out, 'adapter_probes.json', probes)
    save(out, 'vocabulary_audit.json', dict(base_tokens=len(vocab), added_tokens=len(added),
         raw_byte_table_digest=helper.digest({str(i): b.hex() for i, b in vocab.items()}),
         normalizer=tj['normalizer'], pre_tokenizer=tj['pre_tokenizer'], decoder=tj['decoder'],
         restricted_grammar_tokens=len(relevant), native_eos=eos))
    save(out, 'native_summary.json', dict(status='complete', cases=14, engineering_groups=2, development_groups=12,
         tokenizer_encodes=encodes + len(probes), semantic_branch_tokens=len(allowed),
         prefix_range=[min(r['prefix_tokens'] for r in rows), max(r['prefix_tokens'] for r in rows)],
         half_budget_feasible=14, model_answers=0, actual_GPU_cache_validated=False, real_KV_signal_observed=False))
    assert not any(m.split('.')[0] in ('torch', 'transformers', 'vllm', 'tensorflow', 'jax') for m in sys.modules)
    print(json.dumps(dict(worker_status='complete', tokenizer_encodes=encodes + len(probes))), flush=True)


if __name__ == '__main__':
    main()
