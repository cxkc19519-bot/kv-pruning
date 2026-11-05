"""Fixed CPU fixtures. Run only under registered launcher; no real tokenizer or KV."""
import sys
sys.dont_write_bytecode = True
import json
import math
from pathlib import Path


def fixtures():
    grammar = dict(outputs=['{"answer":"A"}', '{"answer":"B"}', '{"answer":"é"}', '{"answer":"A-long"}'],
                   vocabulary={str(i): bytes([i]).hex() for i in range(256)}, eos_id=1000)
    grammar['vocabulary'].update({'300': b'{"answer":"'.hex(), '301': b'A"}'.hex(),
                                  '302': 'é'.encode().hex(), '303': b'-long'.hex(), '304': b'"}'.hex()})
    long_p = [float(300 - i) / 50 for i in range(300)]
    long_p[127] = long_p[128] = long_p[129] = 3.44
    masks = dict(prefix_length=146, budget=73, scores=[float((i * 7) % 19) for i in range(146)],
                 seeds=[3101, 3102, 3103, 3104, 3105, 3106], layout=[28, 4, 128, 2])
    result = [
        dict(id='C01', action='compare', p=[math.log(.09), math.log(.01), math.log(.9)],
             qs=[[math.log(.01), math.log(.09), math.log(.9)], [math.log(.45), math.log(.05), math.log(.5)]], allowed=[0, 1], topks=[1, 2]),
        dict(id='C02', action='compare', p=[1., 2., 3.], qs=[[3., 2., 1.]], allowed=[0, 1, 2], topks=[3]),
        dict(id='C03', action='compare', p=[1., 2., 3.], qs=[[3., 2., 1.]], allowed=[1], topks=[1]),
        dict(id='C04', action='compare', p=[-1000., -1001., 0.], qs=[[-1002., -1000., 0.]], allowed=[0, 1], topks=[1, 2]),
        dict(id='C05', action='compare', p=[1000000., 999999., 999998.], qs=[[999998., 1000000., 999999.]], allowed=[0, 2], topks=[2]),
        dict(id='C06', action='kl', p=[0., 0.], q=['NEG_INF', 0.], support=[0, 1]),
        dict(id='C07', action='kl', p=['NEG_INF', 0.], q=[0., 0.], support=[0, 1]),
        dict(id='C08', action='compare', p=long_p, qs=[list(reversed(long_p))], allowed=[270, 280, 290], topks=[128, 256]),
        dict(id='C09', action='reject_kl', variants=[
            dict(p=[0., 1.], q=[0., 1.], support=[]),
            dict(p=[0., 1.], q=[0., 1.], support=[0, 0]),
            dict(p=[0., 1.], q=[0., 1.], support=[True]),
            dict(p=[0., 1.], q=[0., 1.], support=[2]),
            dict(p=['NAN', 1.], q=[0., 1.], support=[0, 1]),
            dict(p=['POS_INF', 1.], q=[0., 1.], support=[0, 1]),
            dict(p=[True, 1.], q=[0., 1.], support=[0, 1]),
            dict(p=[0., 1.], q=[0.], support=[0]),
            dict(p=['NEG_INF', 0.], q=[0., 1.], support=[0]),
            dict(p=[0., 1.], q=['NEG_INF', 0.], support=[0])]),
        dict(id='G01', action='grammar', **grammar),
        dict(id='G02', action='path', **grammar, tokens=[300, 195, 169, 304, 1000]),
        dict(id='G03', action='path', **grammar, tokens=[123, 34, 97, 110, 115, 119, 101, 114, 34, 58, 34, 301, 1000]),
        dict(id='G04', action='reject_grammar', **grammar),
        dict(id='M01', action='masks', **masks),
        dict(id='M02', action='masks', **dict(masks, scores=[0.] * 146)),
        dict(id='M03', action='masks', **dict(masks, prefix_length=136, budget=68, scores=[0.] * 136)),
        dict(id='M04', action='masks', **dict(masks, prefix_length=134, budget=67, scores=[0.] * 134)),
        dict(id='M05', action='reject_masks', **masks)]
    return result


def numbers(values):
    return [dict(NEG_INF=-math.inf, POS_INF=math.inf, NAN=math.nan).get(v, v) if isinstance(v, str) else v for v in values]


def rejected(call):
    try:
        call()
    except ValueError as error:
        return str(error)
    raise AssertionError('invalid_input_was_accepted')


def grammar_for(module, spec, **updates):
    args = dict(outputs=spec['outputs'], vocabulary={int(k): bytes.fromhex(v) for k, v in spec['vocabulary'].items()}, eos_id=spec['eos_id'])
    args.update(updates)
    return module.FiniteByteGrammar(**args)


def run(module, spec):
    action = spec['action']
    if action == 'compare':
        return [module.compare(spec['p'], q, spec['allowed'], spec['topks']) for q in spec['qs']]
    if action == 'kl':
        return module.distribution_kl(numbers(spec['p']), numbers(spec['q']), spec['support'])
    if action == 'reject_kl':
        return [rejected(lambda v=v: module.distribution_kl(numbers(v['p']), numbers(v['q']), v['support'])) for v in spec['variants']]
    if action == 'grammar':
        return grammar_for(module, spec).reachable()
    if action == 'path':
        g = grammar_for(module, spec)
        prefix, states = b'', []
        for token in spec['tokens']:
            states.append(dict(prefix_hex=prefix.hex(), allowed=g.allowed(prefix), chosen=token))
            prefix = g.advance(prefix, token)
        assert prefix is None
        return states
    if action == 'reject_grammar':
        g = grammar_for(module, spec)
        return [rejected(lambda: g.advance(b'', g.eos_id)), rejected(lambda: g.advance(b'', 999)),
                rejected(lambda: g.allowed(b'{"answer":"Z')), rejected(lambda: g.advance(g.outputs[0], 65)),
                rejected(lambda: grammar_for(module, spec, outputs=spec['outputs'] * 2)),
                rejected(lambda: grammar_for(module, spec, vocabulary={0: b''})),
                rejected(lambda: grammar_for(module, spec, vocabulary={g.eos_id: b'x'})),
                rejected(lambda: grammar_for(module, spec, vocabulary={0: b'x'}).reachable())]
    args = {k: spec[k] for k in ('prefix_length', 'budget', 'scores', 'seeds', 'layout')}
    if action == 'masks':
        first = module.candidate_masks(**args)
        assert first == module.candidate_masks(**args)
        return first
    if action == 'reject_masks':
        changes = [dict(budget=True), dict(budget=147), dict(scores=[0.]), dict(seeds=[1] * 6), dict(layout=[28, 4, 128, True])]
        return [rejected(lambda c=c: module.candidate_masks(**dict(args, **c))) for c in changes]
    raise ValueError('unknown_fixture')


def main():
    # Launcher has already set CPU alarm, import/file/network guards and pins.
    out = Path(sys.argv[1])
    import decoder_objective as module
    specs = fixtures()
    (out / 'software_fixtures.json').write_text(json.dumps(specs, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    results = []
    for spec in specs:
        value = run(module, spec)
        results.append(dict(id=spec['id'], passed=True, output=value))
        (out / 'software_results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    assert [x['id'] for x in specs] == ['C01', 'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09',
                                       'G01', 'G02', 'G03', 'G04', 'M01', 'M02', 'M03', 'M04', 'M05']
    print(json.dumps(dict(cases=len(results), stage='worker_complete', model_answers=0)), flush=True)


if __name__ == '__main__':
    main()
