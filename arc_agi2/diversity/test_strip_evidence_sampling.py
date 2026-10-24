import random

from arc_agi2.diversity.prepare import evidence_query_support, select_task_demonstrations
from arc_agi2.episode_shape_policy import VERSION, describe
from arc_agi2.feca6190_evidence import require_strip_count_evidence


PROFILE = {'version': VERSION, 'patterns': [
    {'demo_input_shapes': 'uniform', 'query_input_shape': 'seen'}]}


def pair(identity, cells):
    n = sum(c != 0 for c in cells)
    side = len(cells) * n
    return {'input': [cells], 'output': [[0] * side for _ in range(side)], 'id': identity}


def test_repeated_query_needs_an_independent_witness():
    query = pair('q', [1, 1, 0, 0])
    pool = [query, pair('a', [1, 0, 0, 0]), pair('b', [1, 2, 0, 0]), pair('c', [1, 2, 3, 0])]
    support = evidence_query_support('feca6190', pool, PROFILE, 'id')
    assert 'q' not in support
    assert set(support) == {'a', 'b', 'c'}
    pool.append(pair('w', [1, 0, 1, 0]))
    assert 'q' in evidence_query_support('feca6190', pool, PROFILE, 'id')


def test_selector_supplies_evidence_without_relaxing_shapes_or_identity():
    query = pair('q', [1, 1, 0, 0])
    candidates = [pair('a', [1, 0, 0, 0]), pair('b', [1, 2, 0, 0]),
                  pair('c', [1, 2, 3, 0]), pair('w', [1, 0, 1, 0])]
    for seed in range(100):
        demos, report = select_task_demonstrations('feca6190', candidates, query,
                                                   random.Random(seed), PROFILE, 'id')
        assert report['matched']
        assert describe(demos, query['input']) == PROFILE['patterns'][0]
        assert len({p['id'] for p in demos} | {'q'}) == 4
        require_strip_count_evidence(demos, [query], list(range(10)))
