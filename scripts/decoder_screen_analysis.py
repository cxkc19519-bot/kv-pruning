"""Frozen exploratory12-group analysis; ties/near-ties are not claimed as gains."""
import math
from decoder_objective import distribution_kl,top_support

OBJECTIVES=('global','top128','top256','legal')
TOL=1e-8


def measurements(full,logits):
    supports={'global':list(range(len(full))),'top128':top_support(full,128),'top256':top_support(full,256),'legal':[32,33,34,35]}
    peak=max(logits[i] for i in supports['legal'])
    return dict(scores={k:distribution_kl(full,logits,ids)['kl'] for k,ids in supports.items()},
                legal_argmax_ids=[i for i in supports['legal'] if logits[i]==peak])


def summarize(groups):
    reports=[]
    for group in groups:
        candidates=group['candidates'];names=[x['name'] for x in candidates]
        assert len(names)==len(set(names))==8
        selected={}
        for objective in OBJECTIVES:
            scores=[r['scores'][objective] for r in candidates];assert all(type(x) in (int,float) and math.isfinite(x) and x>=0 for x in scores)
            best=min(scores);tied=[i for i,x in enumerate(scores) if x<=best+TOL]
            i=tied[0];pred=candidates[i]['legal_argmax_ids']
            fidelity=[candidates[j]['legal_argmax_ids']==group['Full_legal_argmax_ids'] for j in tied]
            selected[objective]=dict(chosen=names[i],within_tolerance=[names[j] for j in tied],
                legal_argmax_ids=pred,Full_argmax_fidelity=pred==group['Full_legal_argmax_ids'],
                tied_fidelity_unambiguous=len(set(fidelity))==1,
                gold_correct=pred==[32+'ABCD'.index(group['gold'])])
        inversions={}
        transitions={}
        for objective in OBJECTIVES[:-1]:
            inv=[]
            for a in range(8):
                for b in range(a+1,8):
                    d=candidates[a]['scores'][objective]-candidates[b]['scores'][objective]
                    e=candidates[a]['scores']['legal']-candidates[b]['scores']['legal']
                    if abs(d)>TOL and abs(e)>TOL and d*e<0:inv.append([names[a],names[b]])
            inversions[objective]=inv
            p,q=selected[objective],selected['legal']
            if not(p['tied_fidelity_unambiguous'] and q['tied_fidelity_unambiguous']):state='ambiguous_tie'
            elif not p['Full_argmax_fidelity'] and q['Full_argmax_fidelity']:state='legal_win'
            elif p['Full_argmax_fidelity'] and not q['Full_argmax_fidelity']:state='legal_loss'
            else:state='tie'
            transitions[objective]=state
        reports.append(dict(case_id=group['case_id'],Full_gold_correct=group['Full_legal_argmax_ids']==[32+'ABCD'.index(group['gold'])],
            selections=selected,inversions=inversions,fidelity_transitions=transitions))
    counts={o:{state:sum(r['fidelity_transitions'][o]==state for r in reports) for state in ['legal_win','legal_loss','tie','ambiguous_tie']} for o in OBJECTIVES[:-1]}
    mismatch=sum(any(r['inversions'][o] for o in OBJECTIVES[:-1]) for r in reports)
    # Require improvement beyond both generic TopK controls, not just an arbitrary score permutation.
    go=(mismatch>=3 and all(v['legal_win']>=2 and v['legal_win']>v['legal_loss'] for v in counts.values()))
    return dict(groups=len(groups),score_tolerance=TOL,ranking_mismatch_groups=mismatch,transitions=counts,group_reports=reports,
                development_go=go,statistical_confirmation=False,novelty_established=False,
                decision='signal_warrants_separate_independent_review' if go else 'stop_current_H3_candidate_no_expansion')
