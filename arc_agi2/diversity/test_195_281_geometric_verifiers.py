"""195ba7dc / 281123b4 shared verifier corrections: geometric panels, not heuristics.

The archived solvers locate the divider/separator as the first full uniform
column (195ba7dc: colour unique to that column; 281123b4: non-modal colour all
in full columns). A valid sparse scene whose only foreground fills one column
of the first panel defeats both at the native 4x4 size, so the failures are
not confined to tiny panels. The reviewed checkers read panels at the fixed
geometry shared by every fixture and constructor output.
"""

import hashlib
import importlib
import json
import random

import numpy as np
import pytest

from arc_agi2.runtime import BASE, grid, reference, solver, verification_solver
from arc_agi2.verified_rules import (VERIFIER_EVIDENCE, VERIFIERS, midpoint_or_panels,
                                     separated_priority_panels)

REPORT = BASE / "reports/diversity-v1/native-batch-d"
FN = {"195ba7dc": midpoint_or_panels, "281123b4": separated_priority_panels}
MASKS = {"195ba7dc": ("top", "bottom"), "281123b4": ("top", "upper", "lower", "bottom")}
MAX = {"195ba7dc": (14, 30), "281123b4": (6, 30)}
LEGACY = {"195ba7dc": (6, 5), "281123b4": (4, 4)}


def gen(tid, **kw):
    return importlib.import_module("tasks.task_" + tid).generate(**kw)


def oracle(tid, masks, w, h):
    out = []
    for r in range(h):
        row = []
        for c in range(w):
            on = [m for m in MASKS[tid] if masks[m][r * w + c]]
            if tid == "195ba7dc":
                row.append(1 if on else 0)
            else:
                colour = {"top": 8, "upper": 5, "lower": 9, "bottom": 4}
                row.append(next((v for v in (9, 4, 8, 5) if v in {colour[m] for m in on}), 0))
        out.append(row)
    return out


def check(tid, w, h, masks):
    p = gen(tid, width=w, height=h, **masks)
    expected = oracle(tid, masks, w, h)
    assert p["output"] == expected
    assert grid(FN[tid](p["input"])) == expected
    return p


@pytest.mark.parametrize("tid", sorted(FN))
def test_registered_and_documented(tid):
    assert verification_solver(tid) is FN[tid] and VERIFIERS[tid] is FN[tid]
    ev = VERIFIER_EVIDENCE[tid]
    assert ev["canonical_data_changed"] is False and ev["archived_reference_changed"] is False
    assert (BASE.parent / ev["counterexample"]).exists()
    assert "not confined to tiny panels" in ev["reason"]


def test_only_authorised_ids_added():
    # Batch E later adds the root-authorised e0fb7511/f3cdc58f checkers.
    assert set(VERIFIERS) == {"78332cb0", "de493100", "3a301edc", "d6542281", "aaecdb9a",
                              "007bbfb7", "7e2bad24", "34b99a2b", "195ba7dc", "281123b4",
                              "e0fb7511", "f3cdc58f", "b4a43f3b", "e74e1818", "a04b2602"}


@pytest.mark.parametrize("tid", sorted(FN))
def test_fixture_labels_untouched(tid):
    packet = reference(tid)
    archived = solver(tid)
    n = 0
    for name in ("canonical", "teaching_fixture"):
        for split in ("train", "test"):
            for p in packet[name][split]:
                assert grid(FN[tid](p["input"])) == p["output"] == grid(archived(p["input"]))
                n += 1
    assert n == {"195ba7dc": 10, "281123b4": 14}[tid]
    replay = importlib.import_module("tasks.task_" + tid).validate()
    for split in ("train", "test"):
        assert (sorted(json.dumps(p, sort_keys=True) for p in replay[split])
                == sorted(json.dumps(p, sort_keys=True) for p in packet["canonical"][split]))


@pytest.mark.parametrize("tid", sorted(FN))
def test_root_sparse_full_column_counterexample(tid):
    col0 = [int(i % 4 == 0) for i in range(16)]
    masks = {m: (col0 if m == "top" else [0] * 16) for m in MASKS[tid]}
    p = check(tid, 4, 4, masks)
    archived = np.asarray(solver(tid)(p["input"]))
    assert archived.shape == {"195ba7dc": (4, 0), "281123b4": (4, 18)}[tid]
    cx = json.loads((REPORT / (tid + "-archived-verifier-counterexample.json")).read_text())
    assert cx["input"] == p["input"] and cx["constructor_output"] == p["output"]
    assert cx["reviewed_result"] == p["output"]
    assert cx["archived_solver_shape"] == list(archived.shape)


def panel_masks(w, h):
    n = w * h
    yield "empty", [0] * n
    yield "full", [1] * n
    for c in {0, w - 1, w // 2}:
        yield f"col{c}", [int(i % w == c) for i in range(n)]
    for r in {0, h - 1, h // 2}:
        yield f"row{r}", [int(i // w == r) for i in range(n)]
    yield "single", [int(i == n - 1) for i in range(n)]
    yield "checker", [int((i // w + i % w) % 2) for i in range(n)]


# minimal 1x1, even/odd panel shapes, and the max-30 compound grids
DIMS = [(1, 1), (1, 2), (2, 1), (2, 2), (3, 3), (4, 4), (3, 4), (4, 3), (5, 6), (6, 5),
        "max", "max-1"]


@pytest.mark.parametrize("tid", sorted(FN))
@pytest.mark.parametrize("dims", DIMS, ids=str)
def test_adversarial_panels(tid, dims):
    if dims == "max":
        w, h = MAX[tid]
    elif dims == "max-1":
        w, h = MAX[tid][0] - 1, MAX[tid][1] - 1
    else:
        w, h = dims
    names = MASKS[tid]
    for slot in names:
        for label, mask in panel_masks(w, h):
            check(tid, w, h, {m: (mask if m == slot else [0] * (w * h)) for m in names})
    for fill in (0, 1):
        check(tid, w, h, {m: [fill] * (w * h) for m in names})
    # a different full column in every panel, and full rows in every panel
    check(tid, w, h, {m: [int(i % w == k % w) for i in range(w * h)] for k, m in enumerate(names)})
    check(tid, w, h, {m: [int(i // w == k % h) for i in range(w * h)] for k, m in enumerate(names)})
    if dims == "max":
        p = gen(tid, width=w, height=h)
        assert max(len(p["input"]), len(p["input"][0])) == 30


@pytest.mark.parametrize("tid", sorted(FN))
def test_rejects_malformed_geometry(tid):
    fn = FN[tid]
    good = gen(tid, width=2, height=2)["input"]
    bad = [[r[:-1] for r in good],                       # width breaks the geometry
           [r[:] for r in good[:1]] + [good[1][:-1]],    # ragged
           []]
    broken = [r[:] for r in good]
    broken[0][2] = 0                                     # first divider cell erased
    bad.append(broken)
    for g in bad:
        with pytest.raises(ValueError):
            fn(g)
    if tid == "281123b4":
        stray = [r[:] for r in good]
        stray[0][0] = 7                                  # colour outside panel roles
        with pytest.raises(ValueError):
            fn(stray)


@pytest.mark.parametrize("tid", sorted(FN))
@pytest.mark.parametrize("kind", ["legacy_dims", "expanded_explicit"])
def test_thousand_constructor_draws(tid, kind):
    for i in range(1000):
        random.seed(int(hashlib.sha256(f"test:{tid}:{kind}:{i}".encode()).hexdigest()[:12], 16))
        w, h = (LEGACY[tid] if kind == "legacy_dims"
                else (random.randint(1, MAX[tid][0]), random.randint(1, MAX[tid][1])))
        p = gen(tid, width=w, height=h)
        assert grid(FN[tid](p["input"])) == p["output"]


def test_recorded_evidence():
    ev = json.loads((REPORT / "geometric-verifier-evidence-195ba7dc-281123b4.json").read_text())
    for tid in FN:
        r = ev[tid]
        assert r["fixtures"]["reviewed_exact"] == r["fixtures"]["pairs"]
        for kind in ("legacy_dims", "expanded_explicit", "adversarial"):
            assert r[kind]["reviewed_disagree"] == 0
        assert r["adversarial"]["archived_disagree_at_4x4_or_larger"] > 0
