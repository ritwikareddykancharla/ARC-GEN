"""PROPOSED separate production-gate audit. Does not overwrite the active worker audit.

Uses input-only evidence for context selection; query labels are used only by
verify() after admission. Run after the native pool has sufficient records.
"""
import hashlib, importlib.util, json, random, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TID = '1b8318e3'
FORK = Path('/Users/ritwika/projects/ARC-GEN')
sys.path.insert(0, str(FORK))
from arc_agi2.runtime import reference, call, grid
from arc_agi2.fixture_policy import fixture_basis
from arc_agi2.program_targets import audit_target, verify, TargetError
from arc_agi2.augmentation import transformed
from arc_agi2.pixel_docking_evidence import require_evidence, DockingContextAmbiguity


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def episode(pairs, d4, pal):
    return {'train': [{k: transformed(p[k], d4, pal) for k in ['input', 'output']} for p in pairs[:-1]],
            'test': [{'input': transformed(pairs[-1]['input'], d4, pal)}],
            'solutions': [transformed(pairs[-1]['output'], d4, pal)]}


def main():
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    fpath = HERE / 'factory.py'
    audit_target(TID, fpath.read_text())
    factory = load(fpath, 'factory_' + TID).build_program
    nat = load(FORK / 'tasks' / f'task_{TID}.py', 'gen_' + TID)
    gate = load(HERE / 'gate_1b8318e3.py', 'gate1b')
    r = {'task_id': TID, 'factory_sha256': sha(fpath), 'constructor_sha256': sha(Path(nat.__file__)),
         'gate_sha256': sha(FORK / 'arc_agi2/pixel_docking_evidence.py'),
         'native_pool_gate_sha256': sha(HERE / 'gate_1b8318e3.py'),
         'query_label_used_for_context_selection': False, 'pool_script_sha256': sha(HERE / 'pool_1b8318e3.py'),
         'passed': False, 'fresh_pairs_checked': 0, 'augmented_pair_checks': 0, 'fixture_variants_checked': 0}
    start = time.monotonic(); stage = 'fixtures'; ep = None; pal = None; d4 = None
    try:
        basis = fixture_basis(TID)
        r['fixture_basis'] = basis
        task = reference(TID)[basis['fixture']]
        for pal in [list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]]:
            for d4 in range(8):
                src = call(factory, d4, pal); audit_target(TID, src)
                ep = {'train': [{k: transformed(p[k], d4, pal) for k in ['input', 'output']} for p in task['train']],
                      'test': [{'input': transformed(p['input'], d4, pal)} for p in task['test']],
                      'solutions': [transformed(p['output'], d4, pal) for p in task['test']]}
                require_evidence(ep['train'], ep['test'], pal)
                verify(src, ep); r['fixture_variants_checked'] += 1
        stage = 'pool'
        pool_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'production-gate-pool-snapshot.jsonl'
        if not pool_path.exists():
            pool_path = HERE / 'fresh_pool_1b8318e3.jsonl'
        pool_text = pool_path.read_text()
        r['pool_input_path'] = str(pool_path)
        r['pool_input_sha256'] = hashlib.sha256(pool_text.encode()).hexdigest()
        recs = [json.loads(l) for l in pool_text.splitlines()]
        recs.sort(key=lambda x: x['index'])
        status = {}
        for x in recs:
            status[x['status']] = status.get(x['status'], 0) + 1
        r['pool_draws'] = len(recs); r['pool_status_counts'] = status
        bad = [x['index'] for x in recs if x['status'] not in ('unique', 'ambiguous')]
        if bad:
            raise RuntimeError('pool has non-gated records: %s' % bad[:10])
        r['sampler_rejections'] = []
        r['ambiguity_rejections'] = [{'index': x['index'], 'seed': x['seed'],
                                      'distinct_outputs': x['witness']['distinct_outputs'],
                                      'cells_differing': x['witness']['cells_differing']}
                                     for x in recs if x['status'] == 'ambiguous']
        (HERE / 'production-gate-ambiguity-witnesses.json').write_text(json.dumps(
            [{'index': x['index'], 'seed': x['seed'], 'input': x['pair']['input'],
              'native_label': x['pair']['output'], 'witness': x['witness']}
             for x in recs if x['status'] == 'ambiguous'], separators=(',', ':')))
        queue = [x for x in recs if x['status'] == 'unique']
        r['gen_seconds_total'] = round(sum(x['gen_seconds'] for x in recs), 1)
        pos = 0; seen = set(); retries = []; base_src = call(factory, 0, list(range(10)))
        episodes = 0; accepted_indices = []; accepted_query_indices = []
        while r['fresh_pairs_checked'] < 1000:
            stage = 'base_check'
            if pos + 4 > len(queue):
                raise RuntimeError('pool exhausted after %d pairs' % r['fresh_pairs_checked'])
            query = queue[pos]; pos += 1
            for attempt in range(12):
                if pos + 3 > len(queue):
                    raise RuntimeError('pool exhausted while resampling demos')
                demos = queue[pos:pos + 3]; pos += 3
                pairs = [d['pair'] for d in demos] + [query['pair']]
                pal, d4 = list(range(10)), 0
                ep = episode(pairs, 0, pal)
                try:
                    # This admission call has only demo labels and query input.
                    # Expected query output is reserved for verify() below.
                    require_evidence(ep['train'], ep['test'], pal)
                except DockingContextAmbiguity as e:
                    retries.append({'query_index': query['index'],
                                    'demo_indices': [d['index'] for d in demos],
                                    'input_only_reason': str(e)})
                    queue.extend(demos)
                    continue
                # A mismatch after evidence acceptance is an audit failure,
                # never a reason to redraw context with query-label feedback.
                verify(base_src, ep)
                break
            else:
                raise RuntimeError('context shortfall persisted for query %d' % query['index'])
            stage = 'fresh_program'
            seed = query['seed']
            pal = list(range(10)); random.Random(seed + 1).shuffle(pal)
            for d4 in range(8):
                ep = episode(pairs, d4, pal); src = call(factory, d4, pal); audit_target(TID, src)
                require_evidence(ep['train'], ep['test'], pal)
                verify(src, ep); r['augmented_pair_checks'] += 4
            r['fresh_pairs_checked'] += 4; episodes += 1
            accepted_indices.extend(d['index'] for d in demos)
            accepted_indices.append(query['index']); accepted_query_indices.append(query['index'])
            seen.update(json.dumps(p['input']) for p in pairs)
        r['episodes'] = episodes
        r['accepted_pool_indices'] = accepted_indices
        r['accepted_query_indices'] = accepted_query_indices
        r['intrinsic_ambiguity_rejections'] = len(r['ambiguity_rejections'])
        r['all_context_retry_queries_retained'] = all(x['query_index'] in accepted_query_indices for x in retries)
        assert len(seen) == 1000, 'accepted input duplicates'
        assert len(set(accepted_indices)) == 1000, 'accepted pool-index duplicates'
        assert sha(fpath) == r['factory_sha256'], 'factory changed during audit'
        assert sha(FORK / 'arc_agi2/pixel_docking_evidence.py') == r['gate_sha256'], 'gate changed during audit'
        assert sha(Path(nat.__file__)) == r['constructor_sha256'], 'constructor changed during audit'
        r['context_retries'] = len(retries); r['context_retry_details'] = retries
        r['passed'] = True
        ep = None
    except Exception as e:
        r.update(failure_stage=stage, error=type(e).__name__ + ': ' + str(e))
        if ep is not None:
            (HERE / 'production-gate-counterexample.json').write_text(json.dumps({'palette': pal, 'd4': d4, 'episode': ep}, separators=(',', ':')))
    if 'retries' in dir():
        r['context_retries'] = len(retries); r['context_retry_details'] = retries
    r['unique_base_inputs'] = len(seen) if 'seen' in dir() else 0
    r['seconds'] = time.monotonic() - start
    r['audit_scope'] = ('Canonical fixture (immutable) 16 variants (2 palettes x 8 D4) via verify(). '
                        'Fresh: seeded unmodified native generate() draws (300 s deadline), each base input gated by the '
                        'independent pairwise-order enumerator with native replay; intrinsically ambiguous draws rejected '
                        '(hidden pixel-list tie-break, witnesses in production-gate-ambiguity-witnesses.json); every other draw kept. '
                        '250 query-fixed episodes of 4 distinct accepted pairs; verify() checks all 4 pairs as queries under all 8 D4 '
                        'with a seeded shuffled palette. Demos redrawn (query kept) only on independently diagnosed context shortfall '
                        '(production input-only gate diagnoses surviving-rule ambiguity, without querying expected answers). Native generator unchanged.')
    (HERE / 'host-production-gate-audit.json').write_text(json.dumps(r, indent=2))
    print(json.dumps({k: v for k, v in r.items() if k not in ('ambiguity_rejections', 'context_retry_details', 'accepted_pool_indices', 'accepted_query_indices')}, indent=1))
    return r


if __name__ == '__main__':
    main()
