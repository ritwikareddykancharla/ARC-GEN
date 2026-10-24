"""34b99a2b shared verifier correction: midpoint divider instead of first full column.

The archived solver treats the first full non-zero column as the divider, so a
valid left-panel column filled with 8 is misread. The reviewed checker uses the
midpoint geometry shared by every fixture and constructor output.
"""

import hashlib
import importlib
import json
import random

import pytest

from arc_agi2.runtime import BASE, grid, reference, solver, verification_solver
from arc_agi2.verified_rules import VERIFIER_EVIDENCE, VERIFIERS, midpoint_xor_panels

TID = "34b99a2b"
REPORT = BASE / "reports/diversity-v1/native-batch-d"


def gen(**kw):
    return importlib.import_module("tasks.task_" + TID).generate(**kw)


def oracle(top, bottom, width, height):
    """Truth table straight from the masks: XOR -> 2, else 0."""
    return [[2 if bool(top[r * width + c]) != bool(bottom[r * width + c]) else 0
             for c in range(width)] for r in range(height)]


def test_registered_and_documented():
    assert verification_solver(TID) is midpoint_xor_panels
    assert VERIFIERS[TID] is midpoint_xor_panels
    ev = VERIFIER_EVIDENCE[TID]
    assert ev["canonical_data_changed"] is False and ev["archived_reference_changed"] is False
    assert (BASE.parent / ev["counterexample"]).exists()
    # Batch D adds only this ID and the later root-authorised 195ba7dc/281123b4.
    assert {"78332cb0", "de493100", "3a301edc", "d6542281", "aaecdb9a", "007bbfb7",
            "7e2bad24", TID, "195ba7dc", "281123b4"} == set(VERIFIERS)


def test_fixture_labels_untouched_and_midpoint_geometry():
    packet = reference(TID)
    archived = solver(TID)
    n = 0
    for name in ("canonical", "teaching_fixture"):
        for split in ("train", "test"):
            for p in packet[name][split]:
                g = p["input"]
                w = len(g[0])
                assert w % 2 == 1 and {r[w // 2] for r in g} == {4}
                assert len(p["output"][0]) == w // 2 and len(p["output"]) == len(g)
                assert grid(midpoint_xor_panels(g)) == p["output"] == grid(archived(g))
                n += 1
    assert n == 10
    # canonical replay of the constructor is still exact
    replay = importlib.import_module("tasks.task_" + TID).validate()
    for split in ("train", "test"):
        assert (sorted(json.dumps(p, sort_keys=True) for p in replay[split])
                == sorted(json.dumps(p, sort_keys=True) for p in packet["canonical"][split]))


def test_archived_counterexample():
    cx = json.loads((REPORT / (TID + "-archived-verifier-counterexample.json")).read_text())
    random.seed(cx["seed"])
    pair = gen(**cx["generate_kwargs"])
    assert pair["input"] == cx["input"] and pair["output"] == cx["constructor_output"]
    assert cx["full_internal_columns"] and min(cx["full_internal_columns"]) < cx["midpoint_column"]
    assert grid(midpoint_xor_panels(pair["input"])) == pair["output"]
    try:
        archived = grid(solver(TID)(pair["input"]))
    except Exception:
        archived = None
    assert archived != pair["output"]


@pytest.mark.parametrize("width,height", [(4, 5), (1, 1), (1, 30), (14, 1), (14, 30), (7, 13)])
def test_full_internal_columns_are_content(width, height):
    n = width * height
    cases = {
        "left_col0_full": ([1 if i % width == 0 else 0 for i in range(n)], [0] * n),
        "right_last_full": ([0] * n, [1 if i % width == width - 1 else 0 for i in range(n)]),
        "both_same_col": ([1 if i % width == 0 else 0 for i in range(n)],
                          [1 if i % width == 0 else 0 for i in range(n)]),
        "left_all_full": ([1] * n, [random.Random(n).randint(0, 1) for _ in range(n)]),
        "both_all_full": ([1] * n, [1] * n),
        "both_empty": ([0] * n, [0] * n),
    }
    for name, (top, bottom) in cases.items():
        pair = gen(top=top, bottom=bottom, width=width, height=height)
        assert pair["output"] == oracle(top, bottom, width, height), name
        assert grid(midpoint_xor_panels(pair["input"])) == pair["output"], name


def test_truth_table_and_rejections():
    # all four (top, bottom) combinations in one 1x4 panel pair
    pair = gen(top=[0, 1, 0, 1], bottom=[0, 0, 1, 1], width=4, height=1)
    assert midpoint_xor_panels(pair["input"]) == [[0, 2, 2, 0]]
    for bad in ([[8, 4, 0, 0]],                       # even width
                [[8, 4, 0], [8, 0, 0]],               # midpoint not full
                [[8, 0, 5], [0, 0, 5]],               # midpoint is background
                [[8, 4, 5], [8, 4]]):                 # ragged
        with pytest.raises(ValueError):
            midpoint_xor_panels(bad)


@pytest.mark.parametrize("kind", ["legacy_default", "expanded_explicit"])
def test_thousand_constructor_draws(kind):
    archived = solver(TID)
    archived_bad = 0
    for i in range(1000):
        random.seed(int(hashlib.sha256(f"test:{TID}:{kind}:{i}".encode()).hexdigest()[:12], 16))
        kw = ({"width": 4, "height": 5} if kind == "legacy_default"
              else {"width": random.randint(3, 14), "height": random.randint(3, 30)})
        pair = gen(**kw)
        assert grid(midpoint_xor_panels(pair["input"])) == pair["output"]
        try:
            archived_bad += grid(archived(pair["input"])) != pair["output"]
        except Exception:
            archived_bad += 1
    assert archived_bad > 0  # the archived first-column heuristic is demonstrably wrong


def test_recorded_evidence_counts():
    ev = json.loads((REPORT / (TID + "-verifier-evidence.json")).read_text())
    assert ev["fixtures"] == {"pairs": 10, "archived_exact": 10, "reviewed_exact": 10}
    for kind in ("legacy_default", "expanded_explicit"):
        assert ev[kind]["draws"] == 1000 and ev[kind]["reviewed_disagree"] == 0
        assert ev[kind]["archived_disagree"] > 0
