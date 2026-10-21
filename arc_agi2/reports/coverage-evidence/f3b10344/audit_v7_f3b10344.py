"""v7 second-review audit for f3b10344 (alignment x blocker rival family).

Stage 1: canonical fixture, 16 variants. The gate and the solver must both report
         the documented context shortfall (centred vs overlap); this is recorded, not hidden.
Stage 2: proposed context-enriched fixture (canonical + one native demo), 16 variants verify.
Stage 3: N fresh native queries held fixed. Their 3-demo contexts are resampled from the unchanged
         native generator only while the independent gate reports context_shortfall or
         colour_shortfall. The gate is called as require_centred_bridge_evidence(train,
         queries=[{'input': grid}], palette) and never sees query labels; labels reach verify() only.
         Every accepted episode runs under all 8 D4 transforms with a shuffled palette.
Native draws that miss the sampler deadline are redrawn and counted (known native slow sampling).
"""
import argparse, hashlib, json, random, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
ROOT = Path('/Users/ritwika/projects/arc-agi2/outputs/research/arcgen-coverage-cli/direct-program-rewrites')
sys.path.insert(0, str(ROOT))
import audit
from arc_agi2.program_targets import audit_target, verify
from arc_agi2 import centred_bridges_f3b10344_evidence as G
from arc_agi2.colour_evidence import MissingColourEvidence

TID = 'f3b10344'; FOLDER = ROOT / TID; HERE = FOLDER / 'review-v7'
GATE_PATH = audit.FORK / 'arc_agi2' / 'centred_bridges_f3b10344_evidence.py'


def mods():
    return (audit.load(FOLDER / 'factory.py', 'v7_factory').build_program,
            audit.load(audit.FORK / 'tasks' / f'task_{TID}.py', 'v7_native'))


def draw(native, st, deadline):
    while True:
        try:
            p = audit.call(native.generate, seconds=deadline); audit.grid(p['input']); audit.grid(p['output']); return p
        except Exception as e:
            st['sampler_rejections'] += 1; k = type(e).__name__ + ':' + str(e)[:50]
            st['sampler_errors'][k] = st['sampler_errors'].get(k, 0) + 1


def solver_status(src, train, q):
    ns = {'__name__': 'standalone_target'}; exec(compile(src, '<f3b>', 'exec'), ns)
    try:
        ns['solve'](json.loads(json.dumps(train)), q); return 'answered'
    except Exception as e:
        return type(e).__name__ + ': ' + str(e)


def one(args):
    index, deadline = args
    factory, native = mods()
    seed = int(hashlib.sha256(f'f3b10344-review-v7:{index}'.encode()).hexdigest()[:12], 16)
    random.seed(seed)
    st = dict(index=index, seed=seed, sampler_rejections=0, sampler_errors={}, context_draws=0, context_status={},
              first_context_status=None, query_discriminates=None, label_is_centred_trim=True, augmented_pair_checks=0,
              shortfall_survivors=[])
    query = draw(native, st, deadline)
    for _ in range(300):
        demos = [draw(native, st, deadline) for _ in range(3)]
        st['context_draws'] += 1
        a = G.assess(demos, [{'input': query['input']}]); s = a['status']
        st['context_status'][s] = st['context_status'].get(s, 0) + 1
        if st['first_context_status'] is None:
            st['first_context_status'] = s; st['query_discriminates'] = a.get('query_discriminates', [[]])[0] if a.get('query_discriminates') else []
        if s == 'identified':
            break
        if s == 'context_shortfall':
            st['shortfall_survivors'].append(a['disagreeing_survivors'])
            # the solver must refuse too (no fallback)
            src = factory(0, list(range(10)))
            if solver_status(src, demos, query['input']) == 'answered':
                raise RuntimeError('solver answered a gate context_shortfall episode')
            continue
        if s == 'colour_shortfall':
            continue
        raise RuntimeError(f'native demos rejected by gate as {s}: {a}')
    else:
        raise RuntimeError('no identifying context within 300 resamples')
    pairs = demos + [query]
    for p in pairs:
        pred = G.predict(np.asarray(p['input']), 0, 8, ('centred', 'trim_any'))
        if not (pred == np.asarray(p['output'])).all():
            st['label_is_centred_trim'] = False
    pal = list(range(10)); random.Random(seed + 1).shuffle(pal)
    for d4 in range(8):
        ep = audit.episode(pairs, d4, pal)
        G.require_centred_bridge_evidence(ep['train'], queries=[{'input': ep['test'][0]['input']}], palette=pal)
        src = factory(d4, pal); audit_target(TID, src); verify(src, ep); st['augmented_pair_checks'] += 4
    st['inputs'] = [hashlib.sha256(json.dumps(p['input']).encode()).hexdigest() for p in pairs]
    return st


def fixture_eps(task, factory):
    for pal in [list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]]:
        for d4 in range(8):
            src = factory(d4, pal); audit_target(TID, src)
            yield src, pal, {'train': [{k: audit.transformed(p[k], d4, pal) for k in ['input', 'output']} for p in task['train']],
                             'test': [{'input': audit.transformed(p['input'], d4, pal)} for p in task['test']],
                             'solutions': [audit.transformed(p['output'], d4, pal) for p in task['test']]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--queries', type=int, default=250)
    ap.add_argument('--deadline', type=float, default=30.0); ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--out', default=str(FOLDER / 'host-audit.json'))
    args = ap.parse_args()
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    factory, native = mods()
    r = dict(task_id=TID, factory_sha256=sha(FOLDER / 'factory.py'),
             constructor_sha256=sha(audit.FORK / 'tasks' / f'task_{TID}.py'),
             evidence_gate_path=str(GATE_PATH), evidence_gate_sha256=sha(GATE_PATH),
             audit_script_sha256=sha(__file__), passed=False, fresh_audit_passed=False,
             fresh_pairs_checked=0, augmented_pair_checks=0, fixture_variants_checked=0)
    start = time.monotonic()
    try:
        task = audit.reference(TID)[audit.fixture_basis(TID)['fixture']]
        canon = []
        for src, pal, ep in fixture_eps(task, factory):
            gs = G.assess(ep['train'], ep['test'])
            ss = solver_status(src, ep['train'], ep['test'][0]['input'])
            demos_ok = True
            try:
                verify(src, {'train': ep['train'], 'test': ep['train'][:1], 'solutions': [ep['train'][0]['output']]})
            except Exception:
                demos_ok = False
            canon.append((gs['status'], tuple(gs.get('disagreeing_survivors', [])), ss.startswith('Undetermined'), demos_ok))
            r['fixture_variants_checked'] += 1
        r['canonical_fixture'] = dict(
            variants=len(canon), gate_status=sorted({c[0] for c in canon}),
            disagreeing_survivors=sorted({s for c in canon for s in c[1]}),
            solver_refuses_query_all_variants=all(c[2] for c in canon),
            demo_inputs_reproduced_all_variants=all(c[3] for c in canon),
            verdict='context_shortfall: canonical train has no uncentred same-colour pair; overlap/* rules fit all '
                    'train demos and bridge test boxes rows10-14xcols24-27 / rows20-22xcols24-26 (col 25, rows 15-19).')
        extra = json.loads((HERE / 'proposed-extra-demo-f3b10344.json').read_text())
        regen = native.generate(**extra['native_params'])
        assert regen == extra['pair'], 'proposed demo is not reproduced by the native generator'
        enr = {'train': task['train'] + [extra['pair']], 'test': task['test']}
        n = 0
        for src, pal, ep in fixture_eps(enr, factory):
            G.require_centred_bridge_evidence(ep['train'], queries=[{'input': q['input']} for q in ep['test']], palette=pal)
            verify(src, ep); n += 1
        r['enriched_fixture_variants_checked'] = n
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            rows = list(pool.map(one, [(i, args.deadline) for i in range(args.queries)]))
        seen = set(); cs = {}; first = {}; errs = {}; surv = {}
        for row in rows:
            seen.update(row['inputs'])
            for k, v in row['context_status'].items(): cs[k] = cs.get(k, 0) + v
            first[row['first_context_status']] = first.get(row['first_context_status'], 0) + 1
            for k, v in row['sampler_errors'].items(): errs[k] = errs.get(k, 0) + v
            for s in row['shortfall_survivors']:
                k = ','.join(s); surv[k] = surv.get(k, 0) + 1
        r['fresh_pairs_checked'] = 4 * len(rows)
        r['augmented_pair_checks'] = sum(x['augmented_pair_checks'] for x in rows)
        r['unique_base_inputs'] = len(seen)
        r['label_is_centred_trim_all_pairs'] = all(x['label_is_centred_trim'] for x in rows)
        hard = [x for x in rows if x['query_discriminates']]
        r['rejection_stats'] = dict(
            native_sampler_deadline_rejections=sum(x['sampler_rejections'] for x in rows),
            native_sampler_error_kinds=errs, sampler_deadline_seconds=args.deadline,
            context_draws_total=sum(x['context_draws'] for x in rows), context_status_totals=cs,
            first_context_status_per_query=first,
            queries_needing_context_resample=sum(1 for x in rows if x['context_draws'] > 1),
            max_context_draws_for_one_query=max(x['context_draws'] for x in rows),
            hard_queries_discriminating_rival_rules=len(hard),
            shortfall_disagreeing_survivor_sets=surv,
            intrinsic_ambiguity_witnesses=0)
        r['audit_scope'] = (f'{len(rows)} fresh unchanged native queries held fixed; 3-demo contexts resampled from the '
                            'unchanged native generator only on gate context/colour shortfall; rival family '
                            '{centred,overlap}x{trim_any,trim_same,span_any,span_same,none}; gate called with '
                            "queries=[{'input': grid}] only; every accepted episode verified under all 8 D4 with a "
                            'shuffled palette; slow native draws redrawn and counted; no query dropped or narrowed.')
        assert r['fresh_pairs_checked'] >= 1000 and r['augmented_pair_checks'] >= 8000
        assert r['label_is_centred_trim_all_pairs'] and r['unique_base_inputs'] >= 100
        assert r['canonical_fixture']['solver_refuses_query_all_variants'] and r['canonical_fixture']['demo_inputs_reproduced_all_variants']
        assert r['enriched_fixture_variants_checked'] == 16
        r['fresh_audit_passed'] = True
        r['passed'] = False
        r['not_passed_reason'] = ('Canonical fixture is an honest context shortfall (centred vs overlap pairing is not '
                                  'demonstrated). Passing needs host approval of the context-enriched fixture '
                                  '(review-v7/proposed-extra-demo-f3b10344.json). Fresh audit and enriched fixture pass.')
    except Exception as e:
        r['error'] = type(e).__name__ + ': ' + str(e)
    r['seconds'] = time.monotonic() - start
    Path(args.out).write_text(json.dumps(r, indent=2) + '\n'); print(json.dumps(r, indent=2))


if __name__ == '__main__':
    main()
