"""Native-domain expansions (2026-10-24): broader canvases/objects keep each rule.

Each family's original fixtures must still replay exactly. Fresh broadened
samples must agree with the archived verifier and with the standalone factory
program under every D4 transform and a non-identity palette.
"""
import importlib
import json
import random

import pytest

from .augmentation import transformed
from .program_targets import audit_target
from .runtime import call, grid, reference, verification_solver

FAMILIES = ['31adaf00', '84db8fc4', 'ce039d91', '137f0df0',
            'd282b262', 'a406ac07', 'f45f5ca7']
PALETTE = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
# Fixed canvas of every original fixture/generator, before this change.
ORIGINAL_SHAPE = {'d282b262': (15, 15)}


def module(tid):
    return importlib.import_module('tasks.task_' + tid)


def solvers(tid):
    factory = importlib.import_module('arc_agi2.direct_factories.task_' + tid)
    out = []
    for d4 in range(8):
        source = factory.build_program(d4, PALETTE)
        audit_target(tid, source)
        scope = {}
        exec(source, scope)
        out.append(scope['solve'])
    return out


def shape(g):
    return len(g), len(g[0])


def check_pairs(tid, pairs):
    """Verifier agreement plus D4/palette program agreement on 4-pair episodes."""
    checker = verification_solver(tid)
    programs = solvers(tid)
    for pair in pairs:
        assert grid(call(checker, pair['input'])) == pair['output']
    for start in range(0, len(pairs) - 3, 4):
        episode = pairs[start:start + 4]
        for d4, solve in enumerate(programs):
            demos = [{k: transformed(p[k], d4, PALETTE) for k in ('input', 'output')}
                     for p in episode[:3]]
            query = transformed(episode[3]['input'], d4, PALETTE)
            assert solve(demos, query) == transformed(episode[3]['output'], d4, PALETTE)


def sample(tid, count, seed):
    random.seed(seed)
    return [module(tid).generate() for _ in range(count)]


@pytest.mark.parametrize('tid', FAMILIES)
def test_original_fixtures_replay(tid):
    fixture = reference(tid)['canonical']
    replay = module(tid).validate()
    for split in ('train', 'test'):
        assert (sorted(json.dumps(p, sort_keys=True) for p in replay[split])
                == sorted(json.dumps(p, sort_keys=True) for p in fixture[split]))


@pytest.mark.parametrize('tid', FAMILIES)
def test_broadened_canvas_is_rectangular_and_verified(tid):
    pairs = sample(tid, 48, 20261024)
    shapes = {shape(p['input']) for p in pairs}
    original = ORIGINAL_SHAPE.get(tid, (10, 10))
    assert len(shapes) >= 12, shapes
    assert any(h != w for h, w in shapes)
    assert any(s != original for s in shapes)
    assert max(max(s) for s in shapes) >= 20
    check_pairs(tid, pairs)


def test_31adaf00_larger_holes_on_rectangular_canvas():
    width, height = 23, 7
    cells = [[5] * width for _ in range(height)]
    for r in range(1, 5):
        for c in range(2, 6):
            cells[r][c] = 0          # 4x4 hole: impossible on the old 10x10 sampler
    for r, c in ((4, 15), (4, 16), (5, 15), (5, 16), (0, 20), (6, 0)):
        cells[r][c] = 0
    p = module('31adaf00').generate(colors=sum(cells, []), width=width, height=height)
    out = p['output']
    assert shape(p['input']) == (7, 23)
    assert all(out[r][c] == 1 for r in range(1, 5) for c in range(2, 6))
    assert all(out[r][c] == 1 for r in (4, 5) for c in (15, 16))
    assert out[0][20] == 0 and out[6][0] == 0
    check_pairs('31adaf00', [p] * 4)
    holes = set()
    for pair in sample('31adaf00', 120, 7):
        holes.add(sum(row.count(1) for row in pair['output']) >= 16)
    assert True in holes


def test_d282b262_rectangular_boxes_and_counts():
    pairs = sample('d282b262', 120, 11)
    counts, rectangles = set(), 0
    from .helpers import objects
    import numpy as np
    for p in pairs:
        objs = objects(np.array(p['input']), bg=0, multicolour=True)
        counts.add(len(objs))
        for o in objs:
            y0, x0, y1, x1 = o['box']
            rectangles += (y1 - y0) != (x1 - x0)
    assert rectangles > 50
    assert min(counts) <= 2 and max(counts) >= 7
    check_pairs('d282b262', pairs[:40])


def test_a406ac07_colour_count_range_and_unequal_axes():
    pairs = sample('a406ac07', 200, 13)
    colours = {len(set(sum(p['input'], [])) - {0}) for p in pairs}
    assert {2, 9} <= colours
    gen = module('a406ac07').generate
    p = gen(colors=[4, 7], widths=[5, 2], heights=[1, 11])
    assert shape(p['input']) == (12, 7)
    assert p['output'][0] == [4, 4, 4, 4, 4, 0, 4]
    assert all(p['output'][r][5:] == [7, 7] for r in range(1, 12))
    check_pairs('a406ac07', pairs[:40])


def test_137f0df0_block_shapes_and_single_axis_lattices():
    pairs = sample('137f0df0', 200, 17)
    from .helpers import objects
    import numpy as np
    boxes = set()
    for p in pairs:
        for o in objects(np.array(p['input']), bg=0):
            y0, x0, y1, x1 = o['box']
            boxes.add((y1 - y0 + 1, x1 - x0 + 1))
    assert {(1, 1), (3, 3), (1, 3), (3, 1), (2, 2)} <= boxes
    p = module('137f0df0').generate(rows=[2], cols=[1, 5, 8], width=12, height=7, wide=2, tall=3)
    assert p['output'][0][3] == 1 and p['output'][3][3] == 2
    check_pairs('137f0df0', pairs[:40])


def test_f45f5ca7_heights_and_widths_vary():
    pairs = sample('f45f5ca7', 200, 19)
    heights = {len(p['input']) for p in pairs}
    widths = {len(p['input'][0]) for p in pairs}
    assert min(heights) == 5 and max(heights) == 30
    assert min(widths) == 5 and max(widths) == 30


def test_ce039d91_keeps_even_mirror_width_with_free_height():
    pairs = sample('ce039d91', 100, 23)
    assert all(len(p['input'][0]) % 2 == 0 for p in pairs)
    assert any(len(p['input']) % 2 for p in pairs)
    for p in pairs:
        flat = sum(p['output'], [])
        assert 1 in flat and 5 in flat  # symmetric and asymmetric pixels both shown


def test_137f0df0_narrow_canvases_terminate():
    gen = module('137f0df0').generate
    with pytest.raises(ValueError):
        random.seed(0)
        gen(width=5, height=5, wide=3, tall=3)  # only one block fits: no gap line
    for width in (5, 6, 30):
        for height in (5, 6, 30):
            random.seed(width * 31 + height)
            p = gen(width=width, height=height)
            assert shape(p['input']) == (height, width)
            assert any(2 in row for row in p['output'])
