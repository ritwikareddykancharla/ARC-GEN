"""Native batch D: panel-dimension expansion for four Boolean/priority panel families.

* 195ba7dc  OR of two panels (7 on 0) split by a 2 column, output 1.
* 281123b4  four panels 8 | 5 | 9 | 4 split by three 3 columns, priority 9>4>8>5.
* 31d5ba1a  XOR of a 9 panel stacked over a 4 panel, output 6.
* 34b99a2b  XOR of an 8 panel and a 5 panel split by a 4 column, output 2.

Panel count, layout, colour roles and Boolean/priority logic are unchanged;
only the incidental fixed panel size becomes a sampled range. The random
minima are a sampling choice (informative demonstrations), not a semantic
restriction: explicit sizes from 1x1 up to the 30-cell limit are accepted and
sparse layouts are never filtered. Explicit arguments are never replaced, and
explicit dimensions replay the legacy RNG stream exactly.
"""

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import audit_target, compile_target, verify
from arc_agi2.runtime import BASE, call, grid, reference, verification_solver

FAMILIES = ("195ba7dc", "281123b4", "31d5ba1a", "34b99a2b")
PALETTE = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
REPORT = BASE / "reports/diversity-v1/native-batch-d"
# legacy (width, height), explicit maximum, random range
SPEC = {
    "195ba7dc": {"legacy": (6, 5), "max": (14, 30), "random": ((3, 14), (3, 30)),
                 "masks": ("top", "bottom")},
    "281123b4": {"legacy": (4, 4), "max": (6, 30), "random": ((4, 6), (4, 30)),
                 "masks": ("top", "upper", "lower", "bottom")},
    "31d5ba1a": {"legacy": (5, 3), "max": (30, 15), "random": ((3, 30), (3, 15)),
                 "masks": ("top", "bottom")},
    "34b99a2b": {"legacy": (4, 5), "max": (14, 30), "random": ((3, 14), (3, 30)),
                 "masks": ("top", "bottom")},
}
LEGACY_SHA = {"195ba7dc": "30fee2d98afa62cdb7069c55f5e49cf95480cc39ef24e5aaa22ce58aa6b6ac88",
              "281123b4": "91c64590592220df177e06d352c66c1d30c6c97ae340df5e12d85d6ffad8e594",
              "31d5ba1a": "d33bd3dd36d31c328dd22e23963cfd0395b30f2bc0e753accc02fc5c9a9f09e2",
              "34b99a2b": "e08df2c2c01b4b1d91be950f255e3f18dffb2d6454822c6ff81a3bd8528d8cac"}


def gen(tid, **kw):
    return importlib.import_module("tasks.task_" + tid).generate(**kw)


def build(tid, masks, w, h):
    """Independent construction of (input, output) from the panel masks."""
    cell = lambda m, r, c: bool(m[r * w + c])
    if tid == "281123b4":
        names, colours = ("top", "upper", "lower", "bottom"), (8, 5, 9, 4)
        g = [[0] * (4 * w + 3) for _ in range(h)]
        out = [[0] * w for _ in range(h)]
        for r in range(h):
            for k in (1, 2, 3):
                g[r][k * (w + 1) - 1] = 3
            for c in range(w):
                on = set()
                for k, (n, col) in enumerate(zip(names, colours)):
                    if cell(masks[n], r, c):
                        g[r][k * (w + 1) + c] = col
                        on.add(col)
                out[r][c] = next((col for col in (9, 4, 8, 5) if col in on), 0)
        return g, out
    a, b = masks["top"], masks["bottom"]
    if tid == "31d5ba1a":
        g = [[(9 if cell(a, r, c) else 0) for c in range(w)] for r in range(h)]
        g += [[(4 if cell(b, r, c) else 0) for c in range(w)] for r in range(h)]
        out = [[6 if cell(a, r, c) != cell(b, r, c) else 0 for c in range(w)] for r in range(h)]
        return g, out
    left, sep, right, on, op = ((7, 2, 7, 1, lambda x, y: x or y) if tid == "195ba7dc"
                                else (8, 4, 5, 2, lambda x, y: x != y))
    g = [[(left if cell(a, r, c) else 0) for c in range(w)] + [sep]
         + [(right if cell(b, r, c) else 0) for c in range(w)] for r in range(h)]
    out = [[on if op(cell(a, r, c), cell(b, r, c)) else 0 for c in range(w)] for r in range(h)]
    return g, out


def check_pairs(tid, pairs, palettes=(PALETTE,)):
    checker = verification_solver(tid)
    pairs = [{k: grid(p[k]) for k in ("input", "output")} for p in pairs]
    for pair in pairs:
        assert grid(call(checker, pair["input"])) == pair["output"]
    for palette in palettes:
        for d4 in range(8):
            source, _ = compile_target(tid, d4, list(palette))
            audit_target(tid, source)
            verify(source, episode(pairs, d4, palette))


@pytest.mark.parametrize("tid", FAMILIES)
def test_original_fixtures_unchanged(tid):
    fixture = reference(tid)["canonical"]
    replay = importlib.import_module("tasks.task_" + tid).validate()
    for split in ("train", "test"):
        assert (sorted(json.dumps(p, sort_keys=True) for p in replay[split])
                == sorted(json.dumps(p, sort_keys=True) for p in fixture[split]))
    check_pairs(tid, fixture["train"] + fixture["test"], palettes=(list(range(10)), PALETTE))


@pytest.mark.parametrize("tid", FAMILIES)
def test_explicit_dims_replay_legacy_stream(tid):
    """Explicit width/height draw masks in the legacy order from the same RNG."""
    spec = SPEC[tid]
    for seed in range(40):
        rng = random.Random(seed)
        w, h = rng.randint(1, spec["max"][0]), rng.randint(1, spec["max"][1])
        random.seed(seed)
        masks = {n: [random.randint(0, 1) for _ in range(w * h)] for n in spec["masks"]}
        random.seed(seed)
        p = gen(tid, width=w, height=h)
        assert (p["input"], p["output"]) == build(tid, masks, w, h)
        assert p == gen(tid, width=w, height=h, **masks)


@pytest.mark.parametrize("tid", FAMILIES)
def test_random_domain_ranges_and_structure(tid):
    (wlo, whi), (hlo, hhi) = SPEC[tid]["random"]
    ws, hs = set(), set()
    for seed in range(1000):
        random.seed(seed)
        p = gen(tid)
        h, w = len(p["output"]), len(p["output"][0])
        assert wlo <= w <= whi and hlo <= h <= hhi
        ws.add(w); hs.add(h)
        assert all(1 <= n <= 30 for g in (p["input"], p["output"]) for n in (len(g), len(g[0])))
        masks = parse(tid, p["input"], w, h)
        assert (p["input"], p["output"]) == build(tid, masks, w, h)
    assert ws == set(range(wlo, whi + 1)) and {hlo, hhi} <= hs


def parse(tid, g, w, h):
    if tid == "281123b4":
        return {n: [int(g[r][k * (w + 1) + c] != 0) for r in range(h) for c in range(w)]
                for k, n in enumerate(SPEC[tid]["masks"])}
    if tid == "31d5ba1a":
        return {"top": [int(g[r][c] != 0) for r in range(h) for c in range(w)],
                "bottom": [int(g[h + r][c] != 0) for r in range(h) for c in range(w)]}
    return {"top": [int(g[r][c] != 0) for r in range(h) for c in range(w)],
            "bottom": [int(g[r][w + 1 + c] != 0) for r in range(h) for c in range(w)]}


@pytest.mark.parametrize("tid", FAMILIES)
def test_partial_explicit_dimensions(tid):
    (wlo, whi), (hlo, hhi) = SPEC[tid]["random"]
    for seed in range(30):
        random.seed(seed)
        p = gen(tid, width=1)
        assert len(p["output"][0]) == 1 and hlo <= len(p["output"]) <= hhi
        random.seed(seed)
        p = gen(tid, height=1)
        assert len(p["output"]) == 1 and wlo <= len(p["output"][0]) <= whi


@pytest.mark.parametrize("tid", FAMILIES)
def test_explicit_masks_keep_legacy_dims_and_values(tid):
    lw, lh = SPEC[tid]["legacy"]
    names = SPEC[tid]["masks"]
    rng = random.Random(7)
    masks = {n: [rng.randint(0, 1) for _ in range(lw * lh)] for n in names}
    p = gen(tid, **masks)
    assert (len(p["output"][0]), len(p["output"])) == (lw, lh)
    assert (p["input"], p["output"]) == build(tid, masks, lw, lh)
    # Booleans are the same values
    assert gen(tid, **{n: [bool(v) for v in m] for n, m in masks.items()}) == p
    # partial masks: the explicit mask is kept verbatim, the others are sampled
    for seed in range(10):
        random.seed(seed)
        q = gen(tid, top=masks["top"])
        assert parse(tid, q["input"], lw, lh)["top"] == masks["top"]
        assert (q["input"], q["output"]) == build(tid, parse(tid, q["input"], lw, lh), lw, lh)
    # explicit dims with explicit masks
    m = {n: [1, 0, 1, 1, 0, 0] for n in names}
    assert (gen(tid, width=3, height=2, **m)["input"], gen(tid, width=3, height=2, **m)["output"]) \
        == build(tid, m, 3, 2)


@pytest.mark.parametrize("tid", FAMILIES)
def test_invalid_arguments_raise(tid):
    mw, mh = SPEC[tid]["max"]
    lw, lh = SPEC[tid]["legacy"]
    bad = [dict(width=0), dict(height=0), dict(width=mw + 1), dict(height=mh + 1),
           dict(width=True), dict(height=2.0), dict(width="3"),
           dict(top=[1] * (lw * lh - 1)),                      # wrong length at legacy dims
           dict(top=[2] + [0] * (lw * lh - 1)),                # non-Boolean value
           dict(top=[1] * (lw * lh), width=lw + 1)]            # mask/dim mismatch
    for kw in bad:
        with pytest.raises(ValueError):
            gen(tid, **kw)


@pytest.mark.parametrize("tid", FAMILIES)
@pytest.mark.parametrize("which", ["max", "min"])
def test_boundary_rectangles(tid, which):
    w, h = SPEC[tid]["max"] if which == "max" else (1, 1)
    pairs = []
    for seed in range(4):
        random.seed(seed)
        pairs.append(gen(tid, width=w, height=h))
    for p in pairs:
        H, W = len(p["input"]), len(p["input"][0])
        assert max(H, W) <= 30 and (len(p["output"]), len(p["output"][0])) == (h, w)
        if which == "max":
            assert 30 in (H, W)
        assert (p["input"], p["output"]) == build(tid, parse(tid, p["input"], w, h), w, h)
    # registered pair verifier and production factory program at both corners
    check_pairs(tid, pairs)


def test_registered_verifiers_cover_sparse_full_columns_at_every_size():
    """The archived first-full-column heuristics fail on valid sparse scenes at
    any size (not only below the random minima); the registered geometric
    checkers label them exactly. Random minima are a sampling choice only."""
    for tid in FAMILIES:
        names = SPEC[tid]["masks"]
        mw, mh = SPEC[tid]["max"]
        for w, h in ((1, 1), (4, 4), (mw, mh)):
            masks = {n: ([int(i % w == 0) for i in range(w * h)] if n == "top" else [0] * (w * h))
                     for n in names}
            p = gen(tid, width=w, height=h, **masks)
            assert (p["input"], p["output"]) == build(tid, masks, w, h)
            assert grid(verification_solver(tid)(p["input"])) == p["output"]


def test_priority_conflict_witness():
    # every subset of the four panels in one 4x4 scene; priority 9 > 4 > 8 > 5
    names = SPEC["281123b4"]["masks"]
    masks = {n: [int(i >> k & 1) for i in range(16)] for k, n in enumerate(names)}
    p = gen("281123b4", width=4, height=4, **masks)
    flat = [v for row in p["output"] for v in row]
    for i, v in enumerate(flat):
        on = [c for k, c in enumerate((8, 5, 9, 4)) if i >> k & 1]
        assert v == next((c for c in (9, 4, 8, 5) if c in on), 0)
    assert flat[15] == 9 and flat[3] == 8 and flat[2 | 8] == 4 and flat[1 | 2] == 8


@pytest.mark.parametrize("tid", ["195ba7dc", "31d5ba1a", "34b99a2b"])
def test_truth_table_witness(tid):
    p = gen(tid, top=[0, 1, 0, 1], bottom=[0, 0, 1, 1], width=4, height=1)
    on = {"195ba7dc": 1, "31d5ba1a": 6, "34b99a2b": 2}[tid]
    expected = [0, on, on, on] if tid == "195ba7dc" else [0, on, on, 0]
    assert p["output"] == [expected]   # (1,1) separates OR from XOR, (0,0) is background


@pytest.mark.parametrize("tid", FAMILIES)
def test_certificates_bind_current_bytes(tid):
    cert = json.loads((BASE / "direct_factories" / (tid + ".json")).read_text())
    src = (BASE.parent / "tasks" / ("task_" + tid + ".py")).read_bytes()
    fac = (BASE / "direct_factories" / ("task_" + tid + ".py")).read_bytes()
    assert cert["passed"] and cert["constructor_sha256"] == hashlib.sha256(src).hexdigest()
    assert cert["factory_sha256"] == hashlib.sha256(fac).hexdigest()
    assert (cert["fresh_pairs_checked"], cert["augmented_pair_checks"],
            cert["fixture_variants_checked"]) == (1000, 8000, 16)
    assert cert["previous_constructor_sha256"] == LEGACY_SHA[tid]
    audits = json.loads((REPORT / "context-audit.json").read_text())
    for key in (tid, tid + "@min_corner"):
        audit = audits[key]
        assert audit["passed"] and audit["queries_accepted"] == audit["queries_requested"] == 250
        assert not audit["queries_failed"] and audit["make_record_calls"] == 2000
        assert audit["source_sha256"]["constructor"] == cert["constructor_sha256"]
        assert audit["source_sha256"]["factory"] == cert["factory_sha256"]
        for name, rel in (("panel_overlay_evidence", "panel_overlay_evidence.py"),
                          ("colour_evidence", "colour_evidence.py"),
                          ("verified_rules", "verified_rules.py"),
                          ("factory_certificate", f"direct_factories/{tid}.json")):
            assert audit["source_sha256"][name] == hashlib.sha256(
                (BASE / rel).read_bytes()).hexdigest()
