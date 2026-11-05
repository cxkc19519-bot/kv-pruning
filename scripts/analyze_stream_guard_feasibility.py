"""Audit released onset labels and static architecture without executing model code."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import time
import traceback


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-run', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (root/'source.py').write_bytes(source)
    manifest = dict(status='running', args=vars(args), start_unix=time.time(), rows=0,
                    new_model_outputs=0, source_sha256=hashlib.sha256(source).hexdigest(), upstream_executed=False)
    save(root/'manifest.json', manifest)
    try:
        origin = Path(args.source_run)
        inputs = json.loads((origin/'manifest.json').read_text())
        assert inputs['status'] == 'complete'
        for f in inputs['files']:
            assert hashlib.sha256((origin/'upstream'/f['path']).read_bytes()).hexdigest() == f['sha256']
        config = json.loads((origin/'upstream/model/config.json').read_text())
        assert config['use_sliding_window'] is False and config['sliding_window'] is None
        summary = dict(static_config_full_attention_layers=config['num_hidden_layers'],
                       runtime_model_instantiated=False, max_position_embeddings=config['max_position_embeddings'],
                       bf16_kv_bytes_per_token=2*2*config['num_hidden_layers']*config['num_key_value_heads']*config['head_dim'],
                       splits={}, gate='no_go_for_late_onset_at_budget_512',
                       gate_reason='No released first unsafe sentence begins at or after token 512; all records have only two messages.',
                       caveats=['Human sentence-level annotations are intervals, not exact token-level semantic truth.',
                                'Unsafe-only localization splits cannot estimate benign false positives.',
                                'Long unsafe continuations after an early onset do not test late first-risk detection.',
                                'This rejects this dataset/design pairing, not all streaming-guard research.'])
        split_rows = {}
        for name in ['thinking', 'thinking_loc', 'response_loc']:
            rows = [json.loads(l) for l in (origin/'upstream/dataset'/f'{name}.jsonl').read_text().splitlines()]
            split_rows[name] = rows
            assert len({r['unique_id'] for r in rows}) == len(rows)
            lengths, starts, ends, assistant_starts = [], [], [], []
            end_equal_length = 0
            for r in rows:
                ids = r.get('input_ids')
                if not ids:
                    continue
                s,e = r['unsafe_start_index'],r['unsafe_end_index']
                assert isinstance(s,int) and isinstance(e,int) and 0 <= s <= e <= len(ids) and s < len(ids)
                end_equal_length += e == len(ids)
                markers = [i+3 for i in range(len(ids)-2) if ids[i:i+3] == [151644,77091,198]]
                assert len(markers) == 1 and s >= markers[0]
                lengths.append(len(ids));starts.append(s);ends.append(e);assistant_starts.append(markers[0])
            summary['splits'][name] = dict(n=len(rows), labels=dict(Counter(r['label'] for r in rows)),
                message_counts=dict(Counter(len(r['message']) for r in rows)),
                annotated_n=len(lengths), token_length_min_median_max=[min(lengths),statistics.median(lengths),max(lengths)] if lengths else None,
                end_equal_length_count=end_equal_length,
                end_convention_note='Some release endpoints equal sequence length, compatible with exclusive endpoints; exact scorer convention requires separate review.',
                onset_min_median_max=[min(starts),statistics.median(starts),max(starts)] if starts else None,
                onset_at_or_after={str(b):sum(s>=b for s in starts) for b in [128,256,512,1024,2048]},
                response_relative_onset_max=max(s-a for s,a in zip(starts,assistant_starts)) if starts else None)
        thinking = {r['unique_id']:r for r in split_rows['thinking']}
        for r in split_rows['thinking_loc']:
            assert thinking[r['unique_id']] == r
        summary['thinking_loc_exact_subset_of_thinking'] = True
        assert summary['splits']['thinking_loc']['onset_at_or_after']['512'] == 0
        save(root/'summary.json', summary)
        manifest.update(status='complete', end_unix=time.time(), input_manifest_sha256=hashlib.sha256((origin/'manifest.json').read_bytes()).hexdigest())
    except Exception as error:
        manifest.update(status='failed', end_unix=time.time(), error_type=type(error).__name__, error_message=str(error),traceback=traceback.format_exc())
        raise
    finally:
        save(root/'manifest.json', manifest)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
