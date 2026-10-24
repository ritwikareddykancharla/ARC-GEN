"""Native batch E: incidental size/count/density expansion for four families.

* 0c786b71  four-way mirror tiling, unflipped input bottom-right (3-colour pool).
* e0fb7511  black cells with a 4-adjacent black cell become 8 (blue field).
* f0df5ff0  black cells in each blue seed's 3x3 window turn blue (confetti).
* f3cdc58f  bottom-aligned bars of colours 1..4 in columns 0..3.

Rules, colour roles, fixtures and the direct factories are unchanged. Only the
fixed canvas size and the per-scene counts/densities are now sampled. Explicit
arguments are never replaced; explicit colours with omitted dimensions use the
legacy canvas.
"""
import hashlib
import importlib
import json
import random

import pytest

from arc_agi2 import test_mirror_neighbourhood_evidence as witnesses
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import compile_target, verify
from arc_agi2.runtime import BASE, call, grid, reference, verification_solver

FAMILIES = ("0c786b71", "e0fb7511", "f0df5ff0", "f3cdc58f")
PALETTE = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
REPORT = BASE / "reports/diversity-v1/native-batch-e"
LEGACY_SHA = {"0c786b71": "7fc6d170003af1a888887129b02bf336afb967f350691ae23e6551c102e0d8e8",
              "e0fb7511": "3857588ff73d8b3866193818d618dc323c66986853ee719a64ee247ff18c48f4",
              "f0df5ff0": "df76beda51cd578c92874de3457086aa71845949a4ca3f6b77e69dea34205dba",
              "f3cdc58f": "763478e511a8fd9bd9ec13580b1bd30bfa19642e3a8f356018efa81c7c328f94"}
LEGACY_DIMS = {"0c786b71": (4, 3), "e0fb7511": (13, 13), "f0df5ff0": (15, 15),
               "f3cdc58f": (10, 10)}


def mod(tid):
    return importlib.import_module("tasks.task_" + tid)


def gen(tid, **kw):
    return call(mod(tid).generate, seconds=3, **kw)


def certify(tid, pairs):
    """Independent checker labels plus the direct factory on all eight D4."""
    checker = verification_solver(tid)
    for p in pairs:
        assert grid(checker(p["input"])) == p["output"]
    for d4 in range(8):
        verify(compile_target(tid, d4, PALETTE)[0], episode(pairs, d4, PALETTE))


# ------------------------------------------------------------- legacy replay
def _legacy_0c(colors=None):
    import common
    if colors is None:
        raw = common.random_colors(3)
        colors = [raw[common.randint(0, 2)] for _ in range(12)]
    return colors


def _legacy_f3(colors=None):
    import common
    if colors is None:
        while True:
            colors = [0] * 100
            for color in range(1, 5):
                for _ in range(common.randint(2, 8)):
                    colors[common.randint(0, 99)] = color
            if all(colors.count(c) for c in range(1, 5)):
                break
    return colors


@pytest.mark.parametrize("tid,legacy,dims", (("0c786b71", _legacy_0c, (4, 3)),
                                             ("f3cdc58f", _legacy_f3, (10, 10))))
def test_explicit_legacy_dims_replay_legacy_stream(tid, legacy, dims):
    for seed in range(40):
        random.seed(seed)
        colors = legacy()
        after = random.random()
        random.seed(seed)
        pair = mod(tid).generate(width=dims[0], height=dims[1])
        assert random.random() == after
        assert pair == mod(tid).generate(colors=colors)


@pytest.mark.parametrize("tid", FAMILIES)
def test_fixtures_replay_and_explicit_colours_use_legacy_canvas(tid):
    fx = reference(tid)["canonical"]
    replay = mod(tid).validate()
    for split in ("train", "test"):
        assert sorted(map(json.dumps, replay[split])) == sorted(map(json.dumps, fx[split]))
    w, h = LEGACY_DIMS[tid]
    for p in replay["train"]:
        assert (len(p["input"]), len(p["input"][0])) == (h, w)


# ------------------------------------------------------- random domain shape
def _draws(tid, n=150):
    out = []
    for i in range(n):
        random.seed(hashlib.sha256(f"batch-e-test:{tid}:{i}".encode()).digest()[:8])
        out.append(gen(tid))
    return out


def test_0c_random_domain():
    shapes = set()
    for p in _draws("0c786b71"):
        a, o = p["input"], p["output"]
        h, w = len(a), len(a[0])
        assert 2 <= h <= 15 and 2 <= w <= 15 and (len(o), len(o[0])) == (2 * h, 2 * w)
        assert [r[w:] for r in o[h:]] == a                    # unflipped bottom-right
        colours = {v for r in a for v in r}
        assert len(colours) <= 3 and 0 not in colours
        shapes.add((h, w))
    assert len(shapes) > 60


def test_e0_random_domain():
    dens = []
    for p in _draws("e0fb7511"):
        a, o = p["input"], p["output"]
        h, w = len(a), len(a[0])
        assert 6 <= h <= 30 and 6 <= w <= 30
        assert {v for r in a for v in r} <= {0, 1}
        assert sum(r.count(8) for r in o) >= mod("e0fb7511").default_min_marked(w, h)
        dens.append(sum(r.count(0) for r in a) / (h * w))
    assert min(dens) < 0.2 and max(dens) > 0.3


def test_f0_random_domain():
    counts = set()
    for p in _draws("f0df5ff0"):
        a, o = p["input"], p["output"]
        h, w = len(a), len(a[0])
        seeds = [(r, c) for r in range(h) for c in range(w) if a[r][c] == 1]
        assert 6 <= h <= 30 and 6 <= w <= 30
        assert 2 <= len(seeds) <= mod("f0df5ff0").default_max_boxes(w, h)
        assert all(1 <= r < h - 1 and 1 <= c < w - 1 for r, c in seeds)
        assert all(max(abs(r - y), abs(c - x)) >= 3 for i, (r, c) in enumerate(seeds)
                   for y, x in seeds[:i])
        for r, c in seeds:
            assert sum(o[r + i][c + j] == 1 for i in (-1, 0, 1) for j in (-1, 0, 1)) >= 3
        counts.add(len(seeds))
    assert max(counts) > 8


def test_f3_random_domain():
    tall = 0
    for p in _draws("f3cdc58f"):
        a = p["input"]
        h, w = len(a), len(a[0])
        assert 4 <= h <= 30 and 4 <= w <= 30
        flat = [v for r in a for v in r]
        assert all(1 <= flat.count(c) <= h for c in (1, 2, 3, 4))
        tall += max(flat.count(c) for c in (1, 2, 3, 4)) > 8
    assert tall > 0


@pytest.mark.parametrize("tid", FAMILIES)
def test_random_pairs_certify(tid):
    draws = _draws(tid, 40)
    for i in range(0, 40, 4):
        certify(tid, draws[i:i + 4])


# ------------------------------------------------ explicit / partial params
def test_partial_dimensions_respected():
    for tid, w in (("0c786b71", 15), ("e0fb7511", 30), ("f0df5ff0", 7), ("f3cdc58f", 4)):
        random.seed(5)
        p = gen(tid, width=w)
        assert len(p["input"][0]) == w
    random.seed(5)
    assert len(gen("e0fb7511", height=9)["input"]) == 9
    random.seed(5)
    p = gen("f0df5ff0", width=12, height=9, num_boxes=5, density=0.4)
    assert sum(r.count(1) for r in p["input"]) == 5
    random.seed(5)
    p = gen("e0fb7511", width=8, height=7, density=0.3, min_marked=0)
    assert (len(p["input"]), len(p["input"][0])) == (7, 8)


def test_explicit_scenes_are_never_filtered():
    # all-black and all-blue e0 scenes (legacy returned None grids for these)
    assert {v for r in gen("e0fb7511", colors=[0] * 169)["output"] for v in r} == {8}
    assert gen("e0fb7511", colors=[1] * 169)["output"] == [[1] * 13 for _ in range(13)]
    uniform = gen("0c786b71", width=5, height=2, colors=[7] * 10)
    assert uniform["output"] == [[7] * 10 for _ in range(4)]
    seedless = gen("f0df5ff0", width=4, height=4, colors=[2] * 16)
    assert seedless["output"] == seedless["input"]


@pytest.mark.parametrize("tid,kw", [
    ("0c786b71", dict(width=16)), ("0c786b71", dict(width=0)), ("0c786b71", dict(height=True)),
    ("0c786b71", dict(colors=[1.0] * 12)), ("0c786b71", dict(colors=[1] * 11)),
    ("e0fb7511", dict(colors=[0.0] * 169)), ("e0fb7511", dict(colors=[2] * 169)),
    ("e0fb7511", dict(colors=[0] * 169, density=0.2)),
    ("e0fb7511", dict(colors=[0] * 169, min_marked=1)), ("e0fb7511", dict(width=31)),
    ("e0fb7511", dict(density=0)), ("e0fb7511", dict(density=1.0)),
    ("e0fb7511", dict(width=1, height=1)), ("e0fb7511", dict(width=3, height=3, min_marked=10)),
    ("f0df5ff0", dict(colors=[1] + [0] * 224)),                       # edge seed
    ("f0df5ff0", dict(width=5, height=4, colors=[0] * 6 + [1, 0, 1] + [0] * 11)),  # overlap
    ("f0df5ff0", dict(width=3, height=3, colors=[2, 2, 2, 2, 1, 2, 2, 2, 0])),     # 2 blue
    ("f0df5ff0", dict(width=5, height=2)), ("f0df5ff0", dict(width=6, height=6, num_boxes=5)),
    ("f0df5ff0", dict(num_boxes=0)), ("f0df5ff0", dict(colors=[0] * 225, num_boxes=2)),
    ("f3cdc58f", dict(width=3)), ("f3cdc58f", dict(colors=[1, 2, 3, 0], width=4, height=1)),
    ("f3cdc58f", dict(colors=[1, 1, 2, 3, 4], width=5, height=1)),
    ("f3cdc58f", dict(colors=[1.0, 2, 3, 4], width=4, height=1)),
    ("f3cdc58f", dict(colors=[1, 2, 3, 5], width=4, height=1)),
])
def test_invalid_arguments_raise(tid, kw):
    with pytest.raises(ValueError):
        gen(tid, **kw)


# ---------------------------------------------------------------- boundaries
BOUNDARY = {
    "0c786b71": [dict(width=1, height=1, colors=[4]), dict(width=15, height=15),
                 dict(width=1, height=15), dict(width=15, height=1), dict(width=14, height=15)],
    "e0fb7511": [dict(width=2, height=1, colors=[0, 0]), dict(width=30, height=30),
                 dict(width=1, height=30, colors=[i % 2 for i in range(30)]),
                 dict(width=30, height=1, colors=[0, 0] + [1] * 28), dict(width=29, height=30)],
    "f0df5ff0": [dict(width=3, height=3, colors=[0, 2, 0, 2, 1, 2, 0, 2, 0]),
                 dict(width=30, height=30), dict(width=3, height=30), dict(width=30, height=3),
                 dict(width=29, height=30)],
    "f3cdc58f": [dict(width=4, height=1, colors=[4, 3, 2, 1]), dict(width=30, height=30),
                 dict(width=4, height=30), dict(width=30, height=4), dict(width=29, height=30)],
}


@pytest.mark.parametrize("tid", FAMILIES)
def test_boundary_shapes_both_sides(tid):
    pairs = []
    for i, kw in enumerate(BOUNDARY[tid]):
        random.seed(100 + i)
        p = gen(tid, **kw)
        for side in ("input", "output"):
            assert all(1 <= n <= 30 for n in (len(p[side]), len(p[side][0])))
        pairs.append(p)
    certify(tid, pairs)
    if tid == "0c786b71":
        assert (len(pairs[1]["output"]), len(pairs[1]["output"][0])) == (30, 30)


def test_dense_explicit_counts_finish_within_deadline():
    f0 = mod("f0df5ff0")
    for w, h in ((30, 30), (15, 15), (9, 9), (6, 7)):
        cap = f0.window_capacity(w, h)
        random.seed(cap)
        p = gen("f0df5ff0", width=w, height=h, num_boxes=cap)       # 3 s deadline
        assert sum(r.count(1) for r in p["input"]) == cap


# ------------------------------------------------------------ boundedness
def test_infeasible_explicit_sampling_fails_bounded():
    random.seed(0)
    with pytest.raises(RuntimeError):
        gen("e0fb7511", width=30, height=30, density=0.03)        # cannot reach 69 azure
    import common
    original = common.randint
    try:   # every placement lands on cell 0: colours 1..3 never survive
        common.randint = lambda a, b: a
        with pytest.raises(RuntimeError):
            mod("f3cdc58f").generate(width=30, height=30)
    finally:
        common.randint = original


def test_mirror_neighbourhood_witnesses_are_constructor_scenes():
    for p in witnesses.SYMMETRIC_DEMOS:
        assert gen("0c786b71", width=3, height=2,
                   colors=[v for r in p["input"] for v in r]) == p
    for p in (witnesses.NO_DIAGONAL + [witnesses.DIAGONAL_QUERY] + witnesses.PAIRS_ONLY
              + witnesses.NO_PAIR + witnesses.FOURS_ONLY + witnesses.SINGLETONS_ONLY):
        assert gen("e0fb7511", width=5, height=5, colors=[v for r in p["input"] for v in r]) == p
    for p in witnesses.CROSS_ONLY:
        assert gen("f0df5ff0", width=5, height=5, colors=[v for r in p["input"] for v in r]) == p


# --------------------------------------------------------- hash binding
@pytest.mark.parametrize("tid", FAMILIES)
def test_certificates_bind_current_bytes(tid):
    src = (BASE.parent / "tasks" / f"task_{tid}.py").read_bytes()
    fac = (BASE / "direct_factories" / f"task_{tid}.py").read_bytes()
    for cert in (json.loads((BASE / "direct_factories" / f"{tid}.json").read_text()),
                 json.loads((BASE / "reports/diversity-v1/native-certificates" /
                             f"{tid}.json").read_text())):
        assert cert["passed"] and cert["constructor_sha256"] == hashlib.sha256(src).hexdigest()
        assert cert["factory_sha256"] == hashlib.sha256(fac).hexdigest()
        assert (cert["fresh_pairs_checked"], cert["augmented_pair_checks"],
                cert["fixture_variants_checked"]) == (1000, 8000, 16)
    record = json.loads((BASE / "direct_factories" / f"{tid}.json").read_text())
    assert record["previous_constructor_sha256"] == LEGACY_SHA[tid]
    assert "provenance" in record
    audits = json.loads((REPORT / "context-audit.json").read_text())
    for key in (tid, tid + "@min_corner"):
        audit = audits[key]
        assert audit["passed"] and audit["queries_accepted"] == audit["queries_requested"] == 250
        assert not audit["queries_failed"] and audit["make_record_calls"] == 2000
        for name, rel in (("constructor", f"../tasks/task_{tid}.py"),
                          ("factory", f"direct_factories/task_{tid}.py"),
                          ("factory_certificate", f"direct_factories/{tid}.json"),
                          ("mirror_neighbourhood_evidence", "mirror_neighbourhood_evidence.py"),
                          ("colour_evidence", "colour_evidence.py"),
                          ("verified_rules", "verified_rules.py")):
            assert audit["source_sha256"][name] == hashlib.sha256(
                (BASE / rel).read_bytes()).hexdigest()
