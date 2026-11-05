"""Independent stdlib binary KV gather, logit and trace audit; no Torch imports."""
import sys
sys.dont_write_bytecode = True
from array import array
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read(p):
    return json.loads(p.read_text())


def metrics(p, q, allowed):
    def kl(a, b):
        pa, pb = max(a), max(b)
        za = math.log(math.fsum(math.exp(x - pa) for x in a))
        zb = math.log(math.fsum(math.exp(x - pb) for x in b))
        return max(0.0, math.fsum(math.exp(x - pa - za) * ((x - pa - za) - (y - pb - zb)) for x, y in zip(a, b)))
    def maxima(a):
        peak = max(a)
        return [i for i, v in enumerate(a) if v == peak]
    ap, aq = [p[i] for i in allowed], [q[i] for i in allowed]
    return dict(max_abs=max(abs(x - y) for x, y in zip(p, q)), global_KL=kl(p, q), allowed_KL=kl(ap, aq),
                global_argmax_equal=maxima(p) == maxima(q), allowed_argmax_equal=maxima(ap) == maxima(aq))


def main():
    out = Path(sys.argv[1]);cfg = read(out / 'registration_snapshot.json');root = Path(cfg['root'])
    assert sys.byteorder == 'little'
    for p, h in {**cfg['input_sha256'], **cfg['source_sha256']}.items():
        assert sha(root / p) == h
    directory = Path(cfg['model_path'])
    for name, h in {**cfg['model_metadata_files'], **cfg['weights']}.items():
        assert sha(directory / name) == h
    summary = read(out / 'engineering_summary.json')
    assert summary['passed'] and summary['archived_logit_vectors'] == 14 and summary['forward_calls'] == 112
    assert summary['teacher_forced_input_tokens'] == 2574 and summary['development_model_calls'] == 0 and summary['generated_tokens'] == 0
    cases = read(out / 'engineering_inputs.json');assert [c['case_id'] for c in cases] == cfg['engineering_case_ids']
    original = {c['case_id']: c for c in read(root / cfg['native_inputs'])}
    assert all(c == original[c['case_id']] and c['role'] == 'engineering' for c in cases)
    actual = read(out / 'actual_runtime.json')
    assert actual['Full_layers'] == 28 and actual['KV_heads'] == 4 and actual['bytes_per_slot'] == 57344
    assert actual['model_config']['layer_types'] == ['full_attention'] * 28 and actual['parameter_dtypes'] == ['torch.bfloat16']
    assert actual['attention'] == 'sdpa' and actual['tf32'] is False and actual['tokenizer_encodes'] == 4
    snapshots = read(out / 'cache_snapshots.json');assert len(snapshots) == 6
    tensors_checked = gathered_tokens = 0
    for case in cases:
        n, b = case['prefix_tokens'], case['budget_slots']
        records = {r['name']: r for r in snapshots if r['case_id'] == case['case_id']}
        assert set(records) == {'reference', 'recency', 'uniform_random'}
        raw = {}
        for name, record in records.items():
            assert sha(out / record['file']) == record['sha256']
            data = (out / record['file']).read_bytes();raw[name] = data
            slots = n if name == 'reference' else b
            assert len(data) == record['bytes'] == slots * 57344
            assert record['indices'] == sorted(set(record['indices'])) and len(record['indices']) == slots
            offset = 0
            for i, t in enumerate(record['tensors']):
                assert t['layer'] == i // 2 and t['kind'] == ['K', 'V'][i % 2]
                assert t['shape'] == [1, 4, slots, 128] and t['offset'] == offset and t['bytes'] == 4 * slots * 256
                piece = data[offset:offset + t['bytes']]
                assert hashlib.sha256(piece).hexdigest() == t['sha256']
                offset += t['bytes'];tensors_checked += 1
            assert len(record['tensors']) == 56 and offset == len(data)
        anchors = case['anchors'];free = [i for i in range(n) if i not in anchors]
        expected = dict(recency=sorted(anchors + sorted(free, reverse=True)[:b-len(anchors)]),
                        uniform_random=sorted(anchors + random.Random(cfg['random_seeds'][0]).sample(free,b-len(anchors))))
        for name, indices in expected.items():
            assert records[name]['indices'] == indices and set(anchors) <= set(indices)
            for ref, compact in zip(records['reference']['tensors'], records[name]['tensors']):
                reference = raw['reference'][ref['offset']:ref['offset'] + ref['bytes']]
                wanted = b''.join(reference[(head*n+i)*256:(head*n+i+1)*256] for head in range(4) for i in indices)
                got = raw[name][compact['offset']:compact['offset'] + compact['bytes']]
                assert got == wanted
                gathered_tokens += 4 * len(indices)
        integrity = next(x for x in read(out / 'reference_integrity.json') if x['case_id'] == case['case_id'])
        assert integrity['reference_sha256_before'] == integrity['reference_sha256_after'] == records['reference']['sha256']
    vectors = read(out / 'vectors.json');assert len(vectors) == 14
    all_vectors = {}
    for row in vectors:
        p = out / row['file'];assert sha(p) == row['sha256'] and p.stat().st_size == row['bytes'] == 152064 * 4
        a = array('f');a.frombytes(p.read_bytes());assert len(a) == row['entries'] == 152064 and all(math.isfinite(x) for x in a)
        all_vectors[(row['case_id'],row['name'])] = a
    comparisons = read(out / 'comparisons.json');assert len(comparisons) == 8
    for c in cases:
        for label, a, b in [('whole_vs_full_batch','whole','full_batch'), ('whole_vs_split_full_batch','whole','split_full_batch'),
                            ('recency_batch_vs_tokenwise','recency_batch','recency_tokenwise'),
                            ('uniform_random_batch_vs_tokenwise','uniform_random_batch','uniform_random_tokenwise')]:
            value = metrics(all_vectors[c['case_id'],a], all_vectors[c['case_id'],b], [32,33,34,35])
            row = next(r for r in comparisons if r['case_id']==c['case_id'] and r['name']==label)
            for key, got in value.items():
                if isinstance(got,bool):assert row['metrics'][key] == got
                else:assert abs(row['metrics'][key]-got)<1e-8
            assert value['max_abs']<=cfg['numeric']['max_abs_logit'] and value['global_KL']<=cfg['numeric']['global_KL']
            assert value['allowed_KL']<=cfg['numeric']['allowed_KL'] and value['global_argmax_equal'] and value['allowed_argmax_equal'] and row['passed']
    trace = [json.loads(line) for line in (out / 'forward_trace.jsonl').read_text().splitlines()]
    assert len(trace) == 112 and sum(len(t['input_ids']) for t in trace) == 2574
    assert [t['call'] for t in trace] == list(range(1,113))
    for case in cases:
        cid=case['case_id'];prefix=case['prefix_ids'];suffix=case['suffix_ids'];n=len(prefix);b=case['budget_slots']
        plans=[('whole',prefix+suffix,0,0),('prefix',prefix,0,0),('full_batch',suffix,n,n),
               ('split_prefix',prefix[:128],0,0),('split_prefix',prefix[128:],128,128),('split_full_batch',suffix,n,n)]
        for name in ['recency','uniform_random']:
            plans.append((name+'_batch',suffix,n,b))
            plans.extend((name+'_tokenwise',[token],n+i,b+i) for i,token in enumerate(suffix))
        rows=[t for t in trace if t['case_id']==cid];assert len(rows)==len(plans)==56
        for t,(name,ids,logical,physical) in zip(rows,plans):
            assert t['path']==name and t['input_ids']==ids and t['physical_before']==physical
            assert t['logical_positions']==list(range(logical,logical+len(ids)))
            assert t['cache_positions']==list(range(physical,physical+len(ids)))
            assert t['physical_after_expected']==physical+len(ids) and t['attention_shape']==[1,physical+len(ids)]
    assert not any(n.split('.')[0] in ('torch','transformers','decoder_kv_backend','engineer_decoder_kv','numpy') for n in sys.modules)
    report=dict(passed=True,logit_vectors=14,comparisons=8,cache_tensors_rehashed=tensors_checked,
                gathered_head_token_vectors_compared=gathered_tokens,trace_forwards=112,teacher_forced_tokens=2574,
                weight_shards_rehashed=4,metadata_files_rehashed=len(cfg['model_metadata_files']),
                method='Independent stdlib BF16 byte gather and float32 logit KL/argmax recomputation; no Torch or worker imports',
                model_answers=0,development_model_calls=0,H3_misranking_tested=False)
    (out / 'independent_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    main()
