"""Native batch B: broader canvases for seven NO-REARC constructors.

Each family keeps its original fixtures byte-for-byte and its archived
independent verifier. These tests add boundary scenes (30-cell sides, extreme
aspect ratios), structural properties of the sampled domain, reachability of
the new parameter ranges and bounded failure of every rejection loop.
"""

import importlib
import json
import random
from collections import Counter

import numpy as np
import pytest

import common
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import audit_target, verify
from arc_agi2.runtime import BASE, call, grid, reference, verification_solver

FAMILIES = ("03560426", "0becf7df", "0f63c0b9", "14b8e18c", "21f83797",
            "2685904e", "2a28add5")
PALETTE = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]


def module(tid):
    return importlib.import_module("tasks.task_" + tid)


def check_pairs(tid, pairs, palettes=(PALETTE,)):
    """Independent verifier on each pair; factory program on all D4 maps."""
    checker = verification_solver(tid)
    factory = importlib.import_module("arc_agi2.direct_factories.task_" + tid)
    pairs = [{k: grid(p[k]) for k in ("input", "output")} for p in pairs]
    for pair in pairs:
        assert grid(call(checker, pair["input"])) == pair["output"]
    for palette in palettes:
        for d4 in range(8):
            source = factory.build_program(d4, list(palette))
            audit_target(tid, source)
            verify(source, episode(pairs, d4, palette))


def seeded(fn, seed, **kw):
    random.seed(seed)
    return call(fn, seconds=10, **kw)


@pytest.mark.parametrize("tid", FAMILIES)
def test_original_fixtures_unchanged(tid):
    fixture = reference(tid)["canonical"]
    replay = module(tid).validate()
    for split in ("train", "test"):
        assert (sorted(json.dumps(p, sort_keys=True) for p in replay[split])
                == sorted(json.dumps(p, sort_keys=True) for p in fixture[split]))
    check_pairs(tid, fixture["train"] + fixture["test"],
                palettes=(list(range(10)), PALETTE))


@pytest.mark.parametrize("tid", FAMILIES)
def test_certificate_matches_final_sources(tid):
    from arc_agi2.direct_certificates import certified_factory_source
    cert = json.loads((BASE / "direct_factories" / (tid + ".json")).read_text())
    native = json.loads(
        (BASE / "reports/diversity-v1/native-certificates" / (tid + ".json")).read_text())
    assert cert == native and cert["passed"] is True
    assert cert["fresh_pairs_checked"] >= 1000
    assert cert["augmented_pair_checks"] >= 8000
    assert cert["fixture_variants_checked"] == 16
    assert cert["fixture_basis"] == "canonical"
    assert certified_factory_source(tid, 5, PALETTE) is not None


# Boundary canvases: (height, width) keyword arguments per family.
BOUNDARY = {
    # Fixed widths are built from feasible compositions, including short wide
    # canvases (five 5-wide, 2-tall boxes span 6x30).
    "03560426": [dict(height=30), dict(height=6), dict(height=30, width=30),
                 dict(height=6, width=30), dict(height=12, width=30),
                 dict(height=6, width=5), dict(height=30, width=5),
                 dict(height=6, width=14)],
    "0becf7df": [dict(height=30, width=30), dict(height=7, width=30),
                 dict(height=30, width=7), dict(height=7, width=7)],
    "0f63c0b9": [dict(height=30, width=30), dict(height=7, width=30),
                 dict(height=30, width=9), dict(height=7, width=9)],
    "14b8e18c": [dict(height=30, width=30), dict(height=6, width=30),
                 dict(height=30, width=6), dict(height=6, width=6)],
    "21f83797": [dict(grid_height=30, grid_width=30), dict(grid_height=5, grid_width=30),
                 dict(grid_height=30, grid_width=5), dict(grid_height=5, grid_width=5)],
    "2685904e": [dict(height=30), dict(height=6)],
    "2a28add5": [dict(height=30, width=30), dict(height=5, width=30),
                 dict(height=30, width=5), dict(height=5, width=5)],
}


@pytest.mark.parametrize("tid", FAMILIES)
def test_boundary_canvases_verify_under_all_transforms(tid):
    for k, kw in enumerate(BOUNDARY[tid]):
        pairs = [seeded(module(tid).generate, 1000 * k + i, **kw) for i in range(4)]
        for pair in pairs:
            shape = np.asarray(pair["input"]).shape
            assert shape == np.asarray(pair["output"]).shape
            want = (kw.get("height", kw.get("grid_height")),
                    kw.get("width", kw.get("grid_width")))
            assert all(w is None or s == w for s, w in zip(shape, want))
        check_pairs(tid, pairs)


def sample(tid, n, seed=0):
    return [seeded(module(tid).generate, seed + i) for i in range(n)]


def shapes(pairs):
    return Counter(np.asarray(p["input"]).shape for p in pairs)


def assert_broad(pairs, low_h, low_w):
    """Sampled sides reach 30 and come within one cell of their lower bounds."""
    s = shapes(pairs)
    assert len(s) > 50
    assert any(h > w for h, w in s) and any(h < w for h, w in s)
    assert min(h for h, _ in s) - low_h in (0, 1) and max(h for h, _ in s) == 30
    assert min(w for _, w in s) - low_w in (0, 1) and max(w for _, w in s) == 30
    assert min(min(h for h, _ in s), min(w for _, w in s)) >= min(low_h, low_w)


def test_03560426_chain_layout():
    pairs = sample("03560426", 300)
    counts, heights = Counter(), set()
    for pair in pairs:
        g = np.asarray(pair["input"])
        H, W = g.shape
        cols = [c for c in range(W) if g[:, c].any()]
        assert cols[0] == 0 and cols[-1] in (W - 1, W - 2)
        runs, boxes = [], []
        for c in cols:
            if runs and runs[-1][-1] == c - 1 and g[H - 1, c] == g[H - 1, c - 1]:
                runs[-1].append(c)
            else:
                runs.append([c])
        for run in runs:
            colour = g[H - 1, run[0]]
            h = int((g[:, run[0]] == colour).sum())
            # A solid rectangle resting on the floor.
            assert (g[H - h:, run[0]:run[-1] + 1] == colour).all()
            assert not g[:H - h, run[0]:run[-1] + 1].any()
            boxes.append((h, len(run)))
            heights.add(h)
        # Exactly one blank column between neighbours.
        assert all(b[0] - a[-1] == 2 for a, b in zip(runs, runs[1:]))
        assert len({g[H - 1, r[0]] for r in runs}) == len(runs)
        assert sum(h for h, _ in boxes) - len(boxes) + 1 <= H
        counts[len(boxes)] += 1
    assert set(counts) == set(range(3, 9))
    assert heights == set(range(2, 9))
    s = shapes(pairs)
    assert len(s) > 50 and any(h > w for h, w in s) and any(h < w for h, w in s)
    assert min(h for h, _ in s) == 6 and max(h for h, _ in s) == 30
    assert min(w for _, w in s) <= 8 and max(w for _, w in s) == 30
    check_pairs("03560426", pairs[:4])


FIXED_03560426 = [(6, 30), (12, 30), (6, 5), (30, 5), (30, 30), (6, 14),
                  (9, 17), (7, 29)]


@pytest.mark.parametrize("height, width", FIXED_03560426)
def test_03560426_fixed_width_compositions_never_reject(height, width):
    m = module("03560426")
    checker = verification_solver("03560426")
    counts = set()
    for seed in range(40):
        pair = seeded(m.generate, 7_000 + seed, height=height, width=width)
        g = np.asarray(pair["input"])
        assert g.shape == (height, width)
        assert grid(call(checker, pair["input"])) == pair["output"]
        counts.add(sum(1 for c in range(width)
                       if g[-1, c] and (c == 0 or not g[-1, c - 1])))
    # Five boxes are the only way to span 30 columns in six rows.
    if (height, width) == (6, 30):
        assert counts == {5}
    if (height, width) == (12, 30):
        assert counts == {5, 6, 7, 8}
    check_pairs("03560426", [seeded(m.generate, 9_000 + i, height=height,
                                    width=width) for i in range(4)])


def test_03560426_short_wide_explicit_scene():
    pair = module("03560426").generate(widths=[5] * 5, heights=[2] * 5,
                                       colors=[1, 2, 3, 4, 5], width=30, height=6)
    check_pairs("03560426", [pair] * 4)


def test_0becf7df_legend_scene():
    pairs = sample("0becf7df", 200)
    for pair in pairs:
        g = np.asarray(pair["input"])
        H, W = g.shape
        legend = [g[0, 0], g[0, 1], g[1, 0], g[1, 1]]
        assert len(set(legend)) == 4 and 0 not in legend
        canvas = g.copy()
        canvas[:2, :2] = 0
        ink = set(canvas[canvas != 0].tolist())
        assert ink == set(int(v) for v in legend)
        rows, cols = np.nonzero(canvas)
        assert rows.min() >= 1 and rows.max() <= H - 2
        assert cols.min() >= 2 and cols.max() <= W - 3
        assert not (canvas[0, 2] or canvas[1, 2] or canvas[2, 2])
        cells = set(zip(rows.tolist(), cols.tolist()))
        stack, seen = [min(cells)], {min(cells)}
        while stack:
            r, c = stack.pop()
            for q in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if q in cells and q not in seen:
                    seen.add(q)
                    stack.append(q)
        assert seen == cells
    assert_broad(pairs, 7, 7)


def test_0f63c0b9_seed_rows_and_counts():
    pairs = sample("0f63c0b9", 300)
    counts = Counter()
    for pair in pairs:
        g = np.asarray(pair["input"])
        H, W = g.shape
        rows, cols = np.nonzero(g)
        assert len(set(rows.tolist())) == len(rows) == len(set(cols.tolist()))
        assert rows.min() >= 1 and rows.max() <= H - 2
        assert cols.min() >= 3 and cols.max() <= W - 4
        assert all(b - a >= 2 for a, b in zip(sorted(rows), sorted(rows)[1:]))
        assert len(set(g[rows, cols].tolist())) == len(rows)
        counts[len(rows)] += 1
    assert set(counts) == set(range(3, 7))
    assert_broad(pairs, 7, 9)


def test_0f63c0b9_even_gap_tie_goes_to_upper_seed():
    pair = call(module("0f63c0b9").generate, prows=[2, 6, 20], pcols=[3, 5, 7],
                colors=[1, 2, 3], width=11, height=24)
    left = [row[0] for row in pair["output"]]
    assert left[:5] == [1] * 5 and left[5:14] == [2] * 9 and left[14:] == [3] * 10
    check_pairs("0f63c0b9", [pair] * 4)


def test_14b8e18c_boxes_are_separated_and_marked():
    pairs = sample("14b8e18c", 300)
    nested = big = 0
    for pair in pairs:
        g, out = np.asarray(pair["input"]), np.asarray(pair["output"])
        assert (out == 2).any()
        assert ((g == out) | (out == 2)).all() and not (g == 2).any()
        colours = set(g.ravel().tolist()) - {7}
        assert len(colours) == 1
        H, W = g.shape
        from arc_agi2.helpers import objects
        for o in objects(g, bg=7):
            y0, x0, y1, x1 = o["box"]
            if y1 - y0 == x1 - x0 >= 1:
                big += y1 - y0 >= 4
                inner = g[y0 + 1:y1, x0 + 1:x1]
                nested += bool((inner != 7).any())
    assert nested and big
    assert_broad(pairs, 6, 6)


def test_14b8e18c_rejects_merged_diagonals():
    # Two diagonals sharing a 2x2 box draw a solid square. Explicit scenes are
    # unchanged, but random scenes never produce such overlapping boxes.
    m = module("14b8e18c")
    pair = m.generate(wides=[2, 2, 3], talls=[2, 2, 3], brows=[1, 1, 5],
                      bcols=[1, 1, 5], styles=[1, 2, 0], color=4)
    assert grid(call(verification_solver("14b8e18c"), pair["input"])) != pair["output"]
    checker = verification_solver("14b8e18c")
    for i in range(400):
        p = seeded(m.generate, 50_000 + i)
        assert grid(call(checker, p["input"])) == p["output"]


def test_21f83797_box_margin_and_extremes():
    pairs = sample("21f83797", 400)
    sides = set()
    for pair in pairs:
        g = np.asarray(pair["input"])
        H, W = g.shape
        (r0, r1), (c0, c1) = np.nonzero(g)
        assert g[r0, c0] == g[r1, c1] == 2 and (g != 0).sum() == 2
        assert 1 <= r0 and r1 <= H - 2 and 1 <= c0 and c1 <= W - 2
        assert r1 - r0 >= 2 and c1 - c0 >= 2
        sides.add((r1 - r0 + 1 == 3, r1 - r0 + 1 == H - 2))
    assert (True, False) in sides and (False, True) in sides
    assert_broad(pairs, 5, 5)


def test_2685904e_layout_and_counts():
    pairs = sample("2685904e", 300)
    lengths = Counter()
    for pair in pairs:
        g = np.asarray(pair["input"])
        H, W = g.shape
        divs = [y for y in range(H) if (g[y] == 5).all()]
        assert len(divs) == 1
        d = divs[0]
        n = int((g[0] == 8).sum())
        assert (g[0, :n] == 8).all() and 1 <= n < W and n <= d - 1
        assert not g[1:d].any()
        data = [y for y in range(d + 1, H) if g[y].any()]
        assert len(data) == 1 and data[0] >= d + 2 and (g[data[0]] != 0).all()
        assert n in Counter(g[data[0]].tolist()).values()
        lengths[n] += 1
    assert max(lengths) >= 8
    assert_broad(pairs, 6, 4)


def test_2a28add5_anchor_rows():
    pairs = sample("2a28add5", 300)
    for pair in pairs:
        g = np.asarray(pair["input"])
        assert (g == 6).any() and ((g == 6).sum(axis=1) <= 1).all()
        counts = Counter(g.ravel().tolist())
        assert counts[7] > max(v for k, v in counts.items() if k != 7)
    assert_broad(pairs, 5, 5)


@pytest.mark.parametrize("tid, patch", [
    ("03560426", ("randint", lambda a, b: b)),
    ("0becf7df", ("choice", lambda seq: 0)),
    ("14b8e18c", ("get_pixel", lambda g, r, c: -2)),
    ("2685904e", ("choices", lambda seq, k=1: [seq[0]] * k)),
    ("2a28add5", ("randint", lambda a, b: b)),
])
def test_rejection_loops_are_bounded(tid, patch, monkeypatch):
    monkeypatch.setattr(common, patch[0], patch[1])
    with pytest.raises(RuntimeError):
        call(module(tid).generate, seconds=10)
