"""Independent stdlib reconstruction of native profile curves and tables."""
import argparse
import bisect
import collections
import json
import math
from pathlib import Path
import statistics


def table(curve, limit, graph_limit, floor):
    xs = [p[0] for p in curve]
    ys = []
    for _, y in curve:
        ys.append(max(y, ys[-1] if ys else y))
    result = []
    for x in range(limit+1):
        y = ys[min(bisect.bisect_left(xs, x), len(xs)-1)]
        above = [(a, b) for a, b in zip(xs, ys) if a > graph_limit]
        if graph_limit and x > graph_limit and above:
            if x <= above[0][0]:
                y = above[0][1]
            elif x >= above[-1][0]:
                y = above[-1][1]
            else:
                j = bisect.bisect_left([p[0] for p in above], x)
                a, b = above[j-1]; c, d = above[j]
                y = d if x == c else b + (d-b)/(c-a)*(x-a)
        if len(xs) > 1 and x > xs[-1]:
            y = ys[-1] + (ys[-1]-ys[-2])/(xs[-1]-xs[-2])*(x-xs[-1])
        result.append(max(y, floor))
    return result


def curve(rows, key, value, full_only=False):
    groups = collections.defaultdict(list)
    for row in rows:
        s = row['sample']
        if not full_only or s['full_cudagraph']:
            groups[s[key]].append(s[value])
    return [[k, statistics.median(v)] for k, v in sorted(groups.items())]


def dispersion(values):
    med = statistics.median(values)
    return dict(n=len(values), median=med, min=min(values), max=max(values),
        mad=statistics.median([abs(x-med) for x in values]))


def analyze(run):
    rows = [json.loads(x) for x in (run/'profile_events.jsonl').read_text().splitlines()]
    samples = [x for x in rows if x['event'] == 'raw_sample']
    assert 0 < len(samples) <= 130
    blocks = sorted({x['block'] for x in samples})
    assert len(blocks) <= 2
    output = dict(status='complete', total_samples=len(samples), blocks=[],
        complete_real_cycle_cost_measured=False, latency_harm_measured=False)
    for block in blocks:
        data = [x for x in samples if x['block'] == block]
        cs = [x for x in rows if x['event'] == 'cost_curves' and x['block'] == block]
        ends = [x for x in rows if x['event'] == 'capture_end' and x['block'] == block]
        assert len(cs) == len(ends) == 1
        c = cs[0]
        for i, row in enumerate(data):
            s, m = row['sample'], row['metadata']
            assert m['ordinal'] == i
            assert all(math.isfinite(s[x]) and s[x] > 0 for x in ['forward_ms','drafter_ms'])
            assert m['requested_context'] == 8192
            assert len(m['computed_context']) == s['num_reqs']
            assert all(0 <= x <= 512 for x in m['seq_lens_cpu_upper_bound'])
            q = m['max_query_len'] or max(m['scheduled_tokens'])
            ctx = max(min(8192, 512-q), 0)
            assert m['computed_context'] == [ctx] * s['num_reqs']
            assert sum(m['scheduled_tokens']) == s['num_target_tokens']
        d = curve(data, 'num_reqs', 'drafter_ms', True)
        v = curve(data, 'num_target_tokens', 'forward_ms')
        assert d == c['draft_curve'] and v == c['verify_curve'], 'Native median curves mismatch'
        expected = [table(d, c['max_num_reqs'], c['cudagraph_limit'], 0),
                    table(v, c['max_num_batched_tokens'], c['cudagraph_limit'], 1e-6)]
        diffs = [abs(a-b) for aa, bb in zip(expected, c['cost_tables']) for a,b in zip(aa,bb)]
        assert expected == c['cost_tables'], ('Table not exact', max(diffs))
        shapes = collections.defaultdict(list)
        for row in data:
            shapes[row['metadata']['requested_tokens']].append(row['sample'])
        assert all(len(group) == 5 for group in shapes.values())
        item = dict(block=block, profile_only=c['profile_only'], samples=len(data),
            captured_token_counts=ends[0]['captured_token_counts'],
            measured_draft_request_keys=[p[0] for p in d],
            draft_curve=d, verify_curve=v, curves_exact=True, tables_exact=True,
            max_table_difference=max(diffs), shapes={str(k):{
                'forward_ms':dispersion([s['forward_ms'] for s in group]),
                'drafter_ms':dispersion([s['drafter_ms'] for s in group])}
                for k,group in sorted(shapes.items())},cost_tables=c['cost_tables'])
        if not c['profile_only']:
            assert ends[0]['captured_token_counts'] == [1,2,4,5,8,10]
            assert sorted(shapes) == [1,2,4,5,8,10,15,20,40,80,160,320,512]
            assert len(data) == 65 and [p[0] for p in d] == [1,2]
        output['blocks'].append(item)
    final = [x for x in output['blocks'] if not x['profile_only']]
    assert len(final) == 1
    output['final_block'] = final[0]['block']
    output['N1_native_samples_present'] = True
    output['final_verify_first11'] = final[0]['cost_tables'][1][:11]
    output['final_draft_first3'] = final[0]['cost_tables'][0]
    output['single_request_verify_1to5_flat'] = len(set(output['final_verify_first11'][1:6])) == 1
    return output


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--run-dir', required=True)
    args = ap.parse_args(); run = Path(args.run_dir)
    result = analyze(run)
    (run/'independent_profile_analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'blocks'}, indent=2))
