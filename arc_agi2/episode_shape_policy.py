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


def select_demonstrations(candidates, query_input, rng, profile):
    """Return (three demonstrations, report), or (None, report) if fewer exist.

    Candidates must already satisfy split, distinct-input and reuse restrictions.
    Missing shape support falls back to the same candidates, never to another
    query or another split. The caller must log reports and apply semantic gates.
    """
    if profile.get('version') != VERSION or not profile.get('patterns'):
        raise ValueError('Unsupported or empty episode shape profile')
    wanted = dict(rng.choice(profile['patterns']))
    if wanted.get('demo_input_shapes') not in ('uniform', 'mixed') or wanted.get('query_input_shape') not in ('seen', 'novel'):
        raise ValueError('Invalid episode shape pattern')
    report = {'policy': VERSION, 'requested': wanted, 'matched': False,
              'fallback': None, 'observed': None}
    if len(candidates) < 3:
        report['fallback'] = 'insufficient_candidate_demonstrations'
        return None, report
    groups = defaultdict(list)
    for pair in candidates:
        groups[input_shape(pair['input'])].append(pair)
    query_shape = input_shape(query_input)
    demos = None
    if wanted['demo_input_shapes'] == 'uniform':
        feasible = [shape for shape, pairs in groups.items() if len(pairs) >= 3
                    and ((shape == query_shape) == (wanted['query_input_shape'] == 'seen'))]
        if feasible:
            demos = rng.sample(groups[rng.choice(feasible)], 3)
    else:
        if wanted['query_input_shape'] == 'seen':
            other_shapes = [shape for shape in groups if shape != query_shape]
            if query_shape in groups and other_shapes:
                first = rng.choice(groups[query_shape])
                second = rng.choice(groups[rng.choice(other_shapes)])
                rest = [pair for pair in candidates if pair is not first and pair is not second]
                if rest:
                    demos = [first, second, rng.choice(rest)]
        else:
            shapes = [shape for shape in groups if shape != query_shape]
            eligible = [pair for shape in shapes for pair in groups[shape]]
            if len(shapes) >= 2 and len(eligible) >= 3:
                a, b = rng.sample(shapes, 2)
                first, second = rng.choice(groups[a]), rng.choice(groups[b])
                rest = [pair for pair in eligible if pair is not first and pair is not second]
                demos = [first, second, rng.choice(rest)]
    if demos is None:
        demos = rng.sample(candidates, 3)
        report['fallback'] = 'requested_shape_pattern_unavailable_in_candidate_pool'
    rng.shuffle(demos)
    report['observed'] = describe(demos, query_input)
    report['matched'] = report['observed'] == wanted
    return demos, report
