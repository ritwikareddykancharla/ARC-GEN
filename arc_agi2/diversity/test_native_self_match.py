"""Rectangular colour-match self-tiling preserves the rule and canonical labels."""
import random
import pytest
from tasks.task_973e499e import generate, validate
from arc_agi2.runtime import reference, verification_solver, grid
from arc_agi2.diversity.recertify import episode
from arc_agi2.direct_factories.task_973e499e import build_program
from arc_agi2.program_targets import verify


def test_canonical_replay():
    assert validate() == reference('973e499e')['canonical']


@pytest.mark.parametrize('h', range(2, 6))
@pytest.mark.parametrize('w', range(2, 6))
@pytest.mark.parametrize('style', ['lines', 'blocks', 'pixels'])
def test_rectangles_all_styles(h, w, style):
    random.seed(100*h+w)
    pairs = [generate(height=h, width=w, style=style) for _ in range(4)]
    for p in pairs:
        g, out = p['input'], p['output']
        assert len(g) == h and len(g[0]) == w
        assert len(out) == h*h and len(out[0]) == w*w
        # Separate closed-form reference, plus archived verifier and factory.
        expected = [[g[y//h][x//w] if g[y//h][x//w] == g[y%h][x%w] else 0
                     for x in range(w*w)] for y in range(h*h)]
        assert out == expected == grid(verification_solver('973e499e')(g))
    pal = [3,9,0,7,2,8,1,6,4,5]
    for d4 in range(8):
        verify(build_program(d4,pal), episode(pairs,d4,pal))


@pytest.mark.parametrize('n',range(2,10))
def test_requested_palette(n):
    random.seed(n)
    p = generate(height=4,width=5,num_colors=n)
    assert len({c for r in p['input'] for c in r}) == n


@pytest.mark.parametrize('kwargs', [dict(size=6),dict(height=True),dict(width=1),
    dict(size=3,height=3),dict(colors=[1]*9),dict(size=3,colors=[1]*8),
    dict(size=3,colors=[10]*9),dict(size=3,colors=[1]*9,style='lines'),
    dict(height=2,width=2,num_colors=5),dict(style='invalid')])
def test_invalid_requests(kwargs):
    with pytest.raises(ValueError): generate(**kwargs)


def test_default_breadth_and_repeatability():
    random.seed(42)
    first=[generate() for _ in range(200)]
    random.seed(42)
    assert first == [generate() for _ in range(200)]
    assert {(len(p['input']),len(p['input'][0])) for p in first} == {
        (h,w) for h in range(2,6) for w in range(2,6)}
