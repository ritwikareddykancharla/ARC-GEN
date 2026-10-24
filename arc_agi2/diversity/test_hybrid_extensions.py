"""Regression checks for reviewed colour roles and cyclic room graphs."""

import json
import random
from collections import Counter
from pathlib import Path

import pytest

from arc_agi2.diversity.colour_roles import ROLE_ALIGNED, align_pair
from arc_agi2.diversity.rearc import generators, utils, verifiers
from arc_agi2.runtime import call, grid
from arc_agi2.verified_rules import nested_frame_band
from tasks import task_00dbd492 as boxes
from tasks import task_09c534e7 as rooms
from tasks import task_3a301edc as frames
from tasks import task_45bbe264 as crosses


@pytest.mark.parametrize("tid", sorted(ROLE_ALIGNED))
def test_alignment_preserves_constructor_relation(tid):
    """Alignment must be invertible, geometry-preserving and verifier-correct."""
    for seed in range(30):
        random.seed(seed)
        utils.rng.clear()
        raw = call(getattr(generators, "generate_" + tid), 0., 1., seconds=2)
        raw = {k: grid(v) for k, v in raw.items()}
        counts = Counter(c for row in raw["input"] for c in row).most_common()
        if len(counts) < 2 or counts[0][1] == counts[1][1]:
            with pytest.raises(ValueError):
                align_pair(tid, raw)
            continue
        aligned, palette = align_pair(tid, raw)
        assert sorted(palette) == list(range(10))
        for key in ("input", "output"):
            restored = [[palette.index(c) for c in row] for row in aligned[key]]
            assert restored == raw[key]
        assert grid(call(getattr(verifiers, "verify_" + tid),
                         tuple(map(tuple, aligned["input"])))) == aligned["output"]


def test_cycle_closure_preserves_block_interiors(monkeypatch):
    boxes = [(1, 1, 3, 3), (1, 7, 3, 9), (7, 7, 9, 9), (7, 1, 9, 3)]
    corridors = [(2, 4, 2, 6), (4, 8, 6, 8), (8, 4, 8, 6)]
    scene = [{"boxes": boxes, "corridors": corridors, "seed": (2, 2), "color": 3}]
    owner = [[-1] * 14 for _ in range(14)]
    for rect in boxes + corridors:
        for r, c in rooms._rect_cells(rect):
            owner[r][c] = 0
    monkeypatch.setattr(rooms.random, "random", lambda: 0.)
    assert rooms._close_cycles(owner, 14, 14, scene) == 1
    assert (4, 2, 6, 2) in scene[0]["corridors"]
    pair = rooms.generate(width=14, height=14, structures=scene)
    # Only the four block interiors change; corridors and walls stay blue.
    changed = {(r, c) for r in range(14) for c in range(14)
               if pair["input"][r][c] != pair["output"][r][c]}
    assert changed == {(2, 8), (8, 8), (8, 2)}
    for r, c in rooms._rect_cells((4, 2, 6, 2)):
        assert pair["input"][r][c] == pair["output"][r][c] == 1


def test_thin_frame_larger_interior_and_original_fixtures():
    path = Path(__file__).parents[1] / "reports/diversity-v1/3a301edc-broader-counterexample.json"
    evidence = json.loads(path.read_text())
    pair = evidence["pair"]
    assert nested_frame_band(pair["input"]) == pair["output"]
    for pairs in frames.validate().values():
        for pair in pairs:
            assert nested_frame_band(pair["input"]) == pair["output"]


def test_rectangle_and_seed_count_reachability():
    sizes, counts = set(), set()
    for seed in range(200):
        random.seed(seed)
        pair = crosses.generate()
        sizes.add((len(pair["input"]), len(pair["input"][0])))
        counts.add(sum(c != 0 for row in pair["input"] for c in row))
    assert any(h < w for h, w in sizes)
    assert any(h > w for h, w in sizes)
    assert min(h for h, _ in sizes) == 6
    assert max(w for _, w in sizes) == 30
    assert counts == set(range(2, 7))


def test_box_rectangular_boundary_and_palette():
    from arc_agi2.diversity.recertify import episode
    from arc_agi2.program_targets import compile_target, verify
    pair = boxes.generate(width=20, height=9, rows=[0, 0], cols=[0, 11], thicks=[3, 1])
    assert len(pair['input']) == 9 and len(pair['input'][0]) == 20
    palette = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
    for d4 in range(8):
        source, _ = compile_target('00dbd492', d4, palette)
        verify(source, episode([pair] * 4, d4, palette))
