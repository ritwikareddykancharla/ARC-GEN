import random
import pytest
from tasks.task_973e499e import generate
from arc_agi2.self_match_evidence import predict, surviving_rules, require_self_match_evidence
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.augmentation import transformed
from arc_agi2.runtime import reference


def pair(g):
    return generate(height=len(g),width=len(g[0]),colors=sum(g,[]))


def witness():
    return [pair(g) for g in (
        [[1,2,1],[2,1,2]], [[1,1,1],[2,3,2]], [[1,3,1],[2,3,2]],
        [[1,2,3],[2,3,1]])]


@pytest.mark.parametrize('d4', range(8))
@pytest.mark.parametrize('palette', [list(range(10)),[3,9,0,7,2,8,1,6,4,5]])
def test_symmetry_ambiguity_and_query_fixed_resolution(d4,palette):
    pairs=witness()
    assert len({input_orbit(p['input']) for p in pairs}) == 4
    change=lambda p:{k:transformed(g,d4,palette) for k,g in p.items()}
    changed=list(map(change,pairs));q={'input':changed[-1]['input']}
    with pytest.raises(MissingColourEvidence):require_self_match_evidence(changed[:3],[q])
    # Keep query fixed. An asymmetric demonstration exposes tile orientation.
    demos=[*pairs[:2],pair([[1,2,2],[3,1,2]])]
    require_self_match_evidence(list(map(change,demos)),[q])
    # Even a bogus query answer cannot change admission.
    require_self_match_evidence(list(map(change,demos)),[{**q,'output':[[9]],'solutions':[[1]]}])


@pytest.mark.parametrize('d4',range(8))
def test_canonical_context(d4):
    palette=[3,9,0,7,2,8,1,6,4,5]
    f=reference('973e499e')['canonical']
    demos=[{k:transformed(g,d4,palette) for k,g in p.items()} for p in f['train']]
    queries=[{'input':transformed(p['input'],d4,palette)} for p in f['test']]
    require_self_match_evidence(demos,queries)


def test_rule_prediction_and_survivors():
    random.seed(13)
    for h,w in ((2,5),(5,2),(2,2),(5,5)):
        ps=[generate(height=h,width=w) for _ in range(4)]
        for p in ps:
            assert predict(p['input'],('equal',0,0,'outer',0)) == tuple(map(tuple,p['output']))
        assert ('equal',0,0,'outer',0) in surviving_rules(ps[:3])
