"""Match a family's demonstrated input-shape pattern without editing grids.

This is a sampling preference, not a correctness check or a difficulty claim.
Semantic evidence gates must still validate the selected demonstrations. Only
input dimensions are examined; query answers are never required.
"""
from collections import defaultdict

VERSION = 'input-shape-pattern-v1'


def input_shape(grid):
    return (len(grid), len(grid[0]))


def describe(demonstrations, query_input):
    shapes = {input_shape(pair['input']) for pair in demonstrations}
    return {
        'demo_input_shapes': 'uniform' if len(shapes) == 1 else 'mixed',
        'query_input_shape': 'seen' if input_shape(query_input) in shapes else 'novel',
    }


def profile_from_task(task):
    """One pattern per original query; repeated patterns retain their frequency."""
    if not task.get('train') or not task.get('test'):
        raise ValueError('Shape profiling requires original demonstrations and queries')
    return {'version': VERSION,
            'patterns': [describe(task['train'], query['input']) for query in task['test']]}


def select_demonstrations(candidates, query_input, rng, profile, identity_key=None):
    """Return (three demonstrations, report), or (None, report) if fewer exist.

    Candidates must already satisfy split, query-class exclusion and reuse
    restrictions. Pass identity_key='canonical_input_hash' to sample distinct
    equivalence classes, or 'input_hash' for the mask-legend exception. Without
    an explicit key, identity is the exact input grid. Palette aliases must not
    make an otherwise impossible shape pattern appear feasible.
    Missing shape support falls back to the same candidates, never to another
    query or another split. The caller must log reports and apply semantic gates.
    """
    if profile.get('version') != VERSION or not profile.get('patterns'):
        raise ValueError('Unsupported or empty episode shape profile')
    wanted = dict(rng.choice(profile['patterns']))
    if wanted.get('demo_input_shapes') not in ('uniform', 'mixed') or wanted.get('query_input_shape') not in ('seen', 'novel'):
        raise ValueError('Invalid episode shape pattern')
    report = {'policy': VERSION, 'requested': wanted, 'matched': False,
              'fallback': None, 'observed': None, 'identity_key': identity_key or 'exact_input_grid'}
    def identity(pair):
        if identity_key is not None:
            return pair[identity_key]
        return tuple(tuple(row) for row in pair['input'])
    def by_identity(pairs):
        result = defaultdict(list)
        for pair in pairs:result[identity(pair)].append(pair)
        return result
    def distinct_sample(pairs, count):
        identities = by_identity(pairs)
        return [rng.choice(identities[key]) for key in rng.sample(list(identities), count)]
    if len(candidates) < 3:
        report['fallback'] = 'insufficient_candidate_demonstrations'
        return None, report
    if len(by_identity(candidates)) < 3:
        report['fallback'] = 'insufficient_distinct_candidate_demonstrations'
        return None, report
    groups = defaultdict(list)
    for pair in candidates:
        groups[input_shape(pair['input'])].append(pair)
    query_shape = input_shape(query_input)
    demos = None
    if wanted['demo_input_shapes'] == 'uniform':
        feasible = [shape for shape, pairs in groups.items() if len(by_identity(pairs)) >= 3
                    and ((shape == query_shape) == (wanted['query_input_shape'] == 'seen'))]
        if feasible:
            demos = distinct_sample(groups[rng.choice(feasible)], 3)
    else:
        if wanted['query_input_shape'] == 'seen':
            eligible = candidates
            first_candidates = groups.get(query_shape, [])
        else:
            eligible = [pair for pair in candidates if input_shape(pair['input']) != query_shape]
            first_candidates = eligible
        if len(by_identity(eligible)) >= 3:
            # Keep both shape and identity here: one equivalence class can span
            # rotated shapes, so collapsing it globally would lose valid options.
            first_groups = defaultdict(list)
            for pair in first_candidates:
                first_groups[(identity(pair), input_shape(pair['input']))].append(pair)
            first_options = list(first_groups)
            rng.shuffle(first_options)
            for key in first_options:
                first = rng.choice(first_groups[key])
                second_options = [pair for pair in eligible
                                  if identity(pair) != identity(first)
                                  and input_shape(pair['input']) != input_shape(first['input'])]
                if not second_options:continue
                second = distinct_sample(second_options, 1)[0]
                rest = [pair for pair in eligible
                        if identity(pair) not in (identity(first), identity(second))]
                if rest:
                    demos = [first, second, distinct_sample(rest, 1)[0]]
                    break
    if demos is None:
        demos = distinct_sample(candidates, 3)
        report['fallback'] = 'requested_shape_pattern_unavailable_in_candidate_pool'
    rng.shuffle(demos)
    report['observed'] = describe(demos, query_input)
    report['matched'] = report['observed'] == wanted
    return demos, report
