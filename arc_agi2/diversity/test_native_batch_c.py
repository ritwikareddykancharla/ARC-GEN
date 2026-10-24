"""Native batch C: orientation sampling and finite-geometry expansion.

* 7e2bad24, 7e576d6e: each random pair samples its own orientation (the
  canonical episodes mix orientations); explicit True/False is respected.
* 7e2bad24: pair labels are checked by the reviewed native side-contact
  replay; the unchanged colour-evidence gate still demands demonstrations.
* 94414823: canvas, even square side and position vary; quadrant rule and
  adjacent marker corners are kept.
* 50c07299: canvas varies; the segment stays on the bottom-left corner
  anti-diagonal like every fixture.
* 782b5218: deferred; the canonical fixture itself clips the line at the
  bottom, so no bottom guard is added.
"""

import importlib
import json
import random
from pathlib import Path

import pytest

import common
from arc_agi2.beam_endpoint_evidence import RULES, beam_predictions
from arc_agi2.colour_evidence import MissingColourEvidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import audit_target, compile_target, make_record, verify
from arc_agi2.runtime import BASE, call, grid, reference, solver, verification_solver

CHANGED = ("7e2bad24", "7e576d6e", "94414823", "50c07299")
PALETTE = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
REPORT = BASE / "reports/diversity-v1/native-batch-c"


def module(tid):
    return importlib.import_module("tasks.task_" + tid)


def seeded(fn, seed, **kw):
    random.seed(seed)
    return call(fn, seconds=20, **kw)


def check_pairs(tid, pairs, palettes=(PALETTE,)):
    """Registered verifier per pair; production target program on all D4 maps."""
    checker = verification_solver(tid)
    pairs = [{k: grid(p[k]) for k in ("input", "output")} for p in pairs]
    for pair in pairs:
        assert grid(call(checker, pair["input"])) == pair["output"]
    for palette in palettes:
        for d4 in range(8):
            source, _ = compile_target(tid, d4, list(palette))
            audit_target(tid, source)
            verify(source, episode(pairs, d4, palette))


def wall_axis(g, colours=(2, 3)):
    walls = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v in colours}
    return "h" if any((r, c + 1) in walls for r, c in walls) else "v"


@pytest.mark.parametrize("tid", CHANGED + ("782b5218",))
def test_original_fixtures_unchanged(tid):
    fixture = reference(tid)["canonical"]
    replay = module(tid).validate()
    for split in ("train", "test"):
        assert (sorted(json.dumps(p, sort_keys=True) for p in replay[split])
                == sorted(json.dumps(p, sort_keys=True) for p in fixture[split]))
    if tid in CHANGED:
        check_pairs(tid, fixture["train"] + fixture["test"],
                    palettes=(list(range(10)), PALETTE))


# ---------------------------------------------------------------- orientation

def test_7e2bad24_explicit_orientation_respected():
    gen = module("7e2bad24").generate
    for seed in range(12):
        upright = seeded(gen, seed, flip=False, flop=False, xpose=False)["input"]
        assert wall_axis(upright) == "h"
        assert any(upright[0][c] == 1 for c in range(16)) or any(
            upright[r][0] == 1 for r in range(16))
        assert wall_axis(seeded(gen, seed, flip=False, flop=False, xpose=True)["input"]) == "v"
        flipped = seeded(gen, seed, flip=True, flop=True, xpose=False)["input"]
        assert any(flipped[15][c] == 1 for c in range(16)) or any(
            flipped[r][15] == 1 for r in range(16))


def test_7e2bad24_random_pairs_mix_orientation():
    gen = module("7e2bad24").generate
    axes = [wall_axis(seeded(gen, 100 + i)["input"]) for i in range(24)]
    assert set(axes) == {"h", "v"}
    episodes = [axes[i:i + 4] for i in range(0, 24, 4)]
    assert any(len(set(e)) > 1 for e in episodes)


def full_lines(g):
    bg = max({v for row in g for v in row}, key=lambda v: sum(r.count(v) for r in g))
    rows = sum(all(v != bg for v in row) for row in g)
    cols = sum(all(row[c] != bg for row in g) for c in range(len(g[0])))
    return rows, cols


def test_7e576d6e_explicit_and_random_orientation():
    gen = module("7e576d6e").generate
    for seed in range(8):
        rows, cols = full_lines(seeded(gen, seed, xpose=False)["input"])
        assert rows in (3, 4) and cols == 0
        rows, cols = full_lines(seeded(gen, seed, xpose=True)["input"])
        assert cols in (3, 4) and rows == 0
    kinds = {full_lines(seeded(gen, 50 + i)["input"])[0] > 0 for i in range(16)}
    assert kinds == {True, False}


def test_7e576d6e_zigzag_kept():
    # Horizontal travel direction alternates between consecutive walls.
    gen = module("7e576d6e").generate
    for seed in range(20):
        p = seeded(gen, seed, xpose=False)
        g, o = p["input"], p["output"]
        bg = g[0][0]
        walls = [r for r, row in enumerate(g) if all(v != bg for v in row)]
        col = next(c for c in range(30) if g[1][c] != bg)  # start pixel
        path = g[1][col]
        dirs = []
        for w in walls:
            # Row w - 1 holds exactly the slide from col to the marker column.
            run = [c for c in range(30) if o[w - 1][c] == path]
            assert col in (run[0], run[-1]) and len(run) > 1
            target = run[-1] if run[0] == col else run[0]
            dirs.append(1 if target > col else -1)
            col = target
        assert all(a != b for a, b in zip(dirs, dirs[1:]))


@pytest.mark.parametrize("tid,bound", [("7e2bad24", 20000), ("7e576d6e", 1000)])
def test_rejection_loops_are_bounded(tid, bound, monkeypatch):
    # Always drawing the lower (7e2bad24) or upper (7e576d6e) end makes every
    # layout infeasible; the loop must stop with an error, not hang.
    original = common.randint
    pick = (lambda a, b: a) if tid == "7e2bad24" else (lambda a, b: b)
    calls = {"n": 0}

    def forced(a, b):
        calls["n"] += 1
        return pick(a, b)

    monkeypatch.setattr(common, "randint", forced)
    with pytest.raises(RuntimeError, match="retry bound"):
        module(tid).generate()
    monkeypatch.setattr(common, "randint", original)
    assert calls["n"] >= bound


# ----------------------------------------------------- 7e2bad24 pair verifier

def test_7e2bad24_side_verifier_counterexample():
    witness = json.loads((REPORT / "7e2bad24-archived-verifier-counterexample.json").read_text())
    side = verification_solver("7e2bad24")
    assert side(witness["input"]) == witness["constructor_output"]
    assert grid(call(solver("7e2bad24"), witness["input"])) == witness["archived_solver_output"]
    assert witness["archived_solver_output"] != witness["constructor_output"]
    preds = {p for p in beam_predictions(witness["input"], list(range(10))) if p is not None}
    assert len(preds) > 1  # endpoint-sensitive


def _sensitive(g):
    return len({p for p in beam_predictions(g, list(range(10))) if p is not None}) > 1


def test_7e2bad24_prepare_keeps_endpoint_sensitive_pairs():
    """prepare.prepare's native pool check is verification_solver == label."""
    gen = module("7e2bad24").generate
    checker = verification_solver("7e2bad24")
    sensitive = 0
    for i in range(60):
        p = seeded(gen, 300 + i)
        assert grid(call(checker, p["input"])) == p["output"]
        sensitive += _sensitive(p["input"])
    assert sensitive >= 5


def _episode(pairs, d4, palette, eid="batch-c-test"):
    ep = episode(pairs, d4, palette)
    ep.update(episode_id=eid, task_id="7e2bad24", d4_transform=d4, color_permutation=palette)
    return ep


def test_7e2bad24_sensitive_query_exports_only_with_demonstrated_evidence():
    gen = module("7e2bad24").generate
    query = next(p for p in (seeded(gen, 500 + i) for i in range(80)) if _sensitive(p["input"]))
    accepted = rejected = 0
    for attempt in range(64):
        random.seed(9000 + attempt)
        demos = [call(gen, seconds=20) for _ in range(3)]
        ep = _episode(demos + [query], attempt % 8, PALETTE)
        try:
            record = make_record(ep)
        except MissingColourEvidence:
            rejected += 1
            continue
        assert record["verification"]["all_exact"]
        accepted += 1
        if accepted and rejected:
            break
    assert accepted >= 1, "bounded context search found no informative demonstrations"
    assert rejected >= 1, "weak contexts must still be rejected by the unchanged gate"


# ------------------------------------------------------------------- 50c07299

def anti_diagonal_cells(g):
    h = len(g)
    return [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 2]


def test_50c07299_random_on_corner_diagonal():
    gen = module("50c07299").generate
    shapes = set()
    for seed in range(60):
        p = seeded(gen, seed)
        g, o = p["input"], p["output"]
        h, w = len(g), len(g[0])
        shapes.add((h, w))
        assert 5 <= h <= 30 and 5 <= w <= 30
        cells = anti_diagonal_cells(g)
        assert cells and all(r + c == h - 1 for r, c in cells)
        assert all(r + c == h - 1 for r, c in anti_diagonal_cells(o))
        assert len(anti_diagonal_cells(o)) == len(cells) + 1
    assert len(shapes) > 20


def test_50c07299_explicit_dimensions():
    gen = module("50c07299").generate
    p = seeded(gen, 1, height=8, width=20)
    assert (len(p["input"]), len(p["input"][0])) == (8, 20)
    legacy = gen(row=1, length=2)
    assert gen(row=1, length=7)["input"][0][15] == 7  # legacy maximum still fits
    assert (len(legacy["input"]), len(legacy["input"][0])) == (16, 16)
    assert gen(row=1, length=2, height=16, width=16) == legacy
    extremes = [gen(row=0, length=14, height=30, width=30),   # longest segment
                gen(row=0, length=2, height=5, width=5),      # smallest canvas
                gen(row=0, length=2, height=5, width=30),
                gen(row=1, length=1, height=30, width=5),
                gen(row=12, length=8, height=30, width=29)]   # last fitting row
    check_pairs("50c07299", extremes[:4])
    check_pairs("50c07299", extremes[4:] + extremes[:3])
    for bad in (dict(row=0, length=3, height=6, width=6), dict(row=2, length=7),
                dict(row=13, length=8, height=30, width=29)):
        with pytest.raises(ValueError):
            gen(**bad)
    with pytest.raises(ValueError):
        seeded(gen, 2, length=3, height=6, width=30)


# ------------------------------------------------------------------- 94414823

def frame_geometry(g):
    cells = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 5]
    rs, cs = [r for r, _ in cells], [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def check_square_rule(p):
    g, o = p["input"], p["output"]
    r0, c0, r1, c1 = frame_geometry(g)
    side = r1 - r0 + 1
    assert side == c1 - c0 + 1 and side % 2 == 0 and side >= 4
    markers = {(r, c): v for r, row in enumerate(g) for c, v in enumerate(row) if v not in (0, 5)}
    assert len(markers) == 2
    corners = {(r0 - 1, c0 - 1): (r0 + 1, c0 + 1), (r0 - 1, c1 + 1): (r0 + 1, c1 - 1),
               (r1 + 1, c0 - 1): (r1 - 1, c0 + 1), (r1 + 1, c1 + 1): (r1 - 1, c1 - 1)}
    assert set(markers) <= set(corners)
    (a, b) = sorted(markers)
    assert a[0] == b[0] or a[1] == b[1]  # adjacent corners, never diagonal
    half = side // 2 - 1
    for pos, colour in markers.items():
        qr, qc = corners[pos]
        # nearest quadrant and its opposite carry the marker colour
        assert o[qr][qc] == colour
        assert o[r0 + r1 - qr][c0 + c1 - qc] == colour
    inner = [o[r][c] for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
    assert sorted(set(inner)) == sorted(markers.values())
    assert inner.count(inner[0]) == len(inner) // 2 and half >= 1


def test_94414823_random_geometry():
    gen = module("94414823").generate
    sides, shapes = set(), set()
    for seed in range(60):
        p = seeded(gen, seed)
        check_square_rule(p)
        shapes.add((len(p["input"]), len(p["input"][0])))
        r0, _, r1, _ = frame_geometry(p["input"])
        sides.add(r1 - r0 + 1)
    assert len(shapes) > 20 and len(sides) > 4


def test_94414823_explicit_geometry_and_extremes():
    gen = module("94414823").generate
    p = seeded(gen, 3, height=12, width=20, flip=False, xpose=False)
    assert (len(p["input"]), len(p["input"][0])) == (12, 20)
    p = seeded(gen, 3, height=12, width=20, flip=False, xpose=True)
    assert (len(p["input"]), len(p["input"][0])) == (20, 12)
    legacy = gen(colors=[4, 8], flip=False, xpose=False)
    assert gen(colors=[4, 8], flip=False, xpose=False, height=10, width=10,
               size=6, brow=2, bcol=2) == legacy
    extremes = [gen(colors=[1, 2], height=30, width=30, size=28, brow=1, bcol=1),
                gen(colors=[3, 4], height=5, width=6, size=4, brow=1, bcol=1),
                gen(colors=[6, 7], height=5, width=30, size=4, brow=1, bcol=25, flip=True),
                gen(colors=[8, 9], height=30, width=6, size=4, brow=26, bcol=1, xpose=True)]
    for p in extremes:
        check_square_rule(p)
    check_pairs("94414823", extremes)
    for bad in (dict(colors=[1, 2], size=5), dict(colors=[1, 2], height=6, width=6, size=4),
                dict(colors=[1, 2], brow=0), dict(colors=[1, 2], height=31, width=10)):
        with pytest.raises(ValueError):
            gen(**bad)


# ------------------------------------------------------------------- 782b5218

def test_782b5218_canonical_clips_line_at_bottom():
    """Deferral evidence: the proposed bottom guard would contradict train[2]."""
    pair = reference("782b5218")["canonical"]["train"][2]
    g, o = pair["input"], pair["output"]
    assert all(g[r][9] != 2 for r in range(10))
    assert all(o[r][9] == 0 for r in range(10))
    assert [c for c in range(10) if g[9][c] == 2] == [7, 8]
