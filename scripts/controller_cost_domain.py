"""Offline reduced-case cost boundary, not a model or traffic experiment."""
import argparse
import json
import math
from pathlib import Path


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-dir',required=True);a=ap.parse_args()
    run=Path(a.run_dir).resolve();out=run/'cost_sensitivity_domain.json';assert not out.exists()
    s=json.loads((run/'summary.json').read_text())
    actual=json.loads((run/'real_feature_selector_replay.json').read_text())
    draft,verify=s['boundaries']['common']['cost_tables']
    assert all(verify[i]==verify[2] for i in range(2,6))
    assert all(verify[i]==verify[6] for i in range(6,11))
    low,high=draft[2]+verify[5],draft[2]+verify[10]
    assert high>low>0
    # Two identical requests, cold calibration with equal per-position p.
    # At a fixed cost plateau all positive extra slots help, so compare 3 vs 8.
    def difference(p):
        return low*(2+2*p+2*p*p+2*p**3+2*p**4)-high*(2+2*p+p*p)
    lo,hi=0.0,1.0
    for _ in range(64):
        mid=(lo+hi)/2
        if difference(mid)>0:hi=mid
        else:lo=mid
    p=(lo+hi)/2;x=(math.log(p/(1-p))+0.2)/0.5
    q=1/(1+math.exp(-x))
    report=dict(kind='posthoc_analytic_reduced_case',N1_cost_plateau=True,
        N2_assumptions=['Two identical requests','All four draft positions share the same max-q feature',
                        'Cold slope0.5 and intercepts-0.2','Reuse this run native cost table, no new profile'],
        N2_cost_for_budget0_to3=low,N2_cost_for_budget4_to8=high,
        N2_probability_boundary_3_vs8=p,proxy_feature_boundary=x,proxy_max_q_boundary=q,
        observed_feature_min=actual['feature_min'],observed_max_q_min=actual['max_q_min'],
        observed_to_proxy_max_q_ratio=actual['max_q_min']/q,
        observed_N2_disagreements=actual['N2_disagreements_from_common'],
        conclusion='Saved natural contexts are far from this reduced-case low-confidence boundary. Do not justify a batched GPU rerun using the uniform-logit example alone.',
        qualifications=['This proxy is not a necessary threshold for arbitrary nonuniform per-position features',
                        'It is not a measured latency, traffic frequency, batched execution or attack result'])
    out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (run/'cost_domain_source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
