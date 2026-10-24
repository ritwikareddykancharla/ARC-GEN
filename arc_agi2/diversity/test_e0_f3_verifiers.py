"""Reviewed pair checkers for e0fb7511 (black 4-adjacency) and f3cdc58f (histogram).

Root-authorised narrow corrections. The archived solvers infer the target or
background as the modal colour; legal dense or tied scenes break that. The
reviewed checkers use the fixed native colours. Direct factories are unchanged.
"""
import json

import pytest

from arc_agi2.program_targets import compile_target
from arc_agi2.runtime import BASE, grid, reference, solver, verification_solver
from arc_agi2.verified_rules import (VERIFIER_EVIDENCE, VERIFIERS, fixed_colour_histogram,
                                     native_zero_adjacency)

FN = {"e0fb7511": native_zero_adjacency, "f3cdc58f": fixed_colour_histogram}
REPORT = BASE / "reports/diversity-v1/native-batch-e"


@pytest.mark.parametrize("tid", sorted(FN))
def test_registered_documented_and_factory_still_used(tid):
    assert verification_solver(tid) is FN[tid] and VERIFIERS[tid] is FN[tid]
    ev = VERIFIER_EVIDENCE[tid]
    assert ev["canonical_data_changed"] is False and ev["archived_reference_changed"] is False
    assert (BASE.parent / ev["counterexample"]).exists()
    # The exported program still comes from the unchanged direct factory.
    assert compile_target(tid, 3, list(range(10)))[1] == "reviewed_direct_coordinate_rewrite"


@pytest.mark.parametrize("tid", sorted(FN))
def test_fixture_labels_untouched(tid):
    packet = reference(tid)
    archived = solver(tid)
    n = 0
    for name in ("canonical", "teaching_fixture"):
        for p in packet[name]["train"] + packet[name]["test"]:
            assert FN[tid](p["input"]) == p["output"] == grid(archived(p["input"]))
            n += 1
    assert n == 8


def test_saved_counterexamples_reproduce():
    e0 = json.loads((REPORT / "e0fb7511-archived-verifier-counterexample.json").read_text())
    assert native_zero_adjacency(e0["input"]) == e0["constructor_output"] != e0["archived"]
    assert {v for r in e0["constructor_output"] for v in r} == {8}
    f3 = json.loads((REPORT / "f3cdc58f-archived-verifier-counterexample.json").read_text())
    assert fixed_colour_histogram(f3["input"]) == f3["expected"] != f3["archived"]
    assert f3["expected"][0] == [1, 2, 3, 4] and f3["archived"][0] == [2, 3, 4, 1]


def test_e0_adjacency_cases():
    f = native_zero_adjacency
    assert f([[0]]) == [[0]] and f([[1]]) == [[1]] and f([[0, 0]]) == [[8, 8]]
    board = [[(y + x) % 2 for x in range(30)] for y in range(30)]   # diagonal-only black
    assert f(board) == board
    assert f([[0] * 30 for _ in range(30)]) == [[8] * 30 for _ in range(30)]
    assert f([[1] * 7 for _ in range(5)]) == [[1] * 7 for _ in range(5)]
    row = [[0 if y == 2 else 1 for _ in range(6)] for y in range(5)]
    assert f(row)[2] == [8] * 6 and f(row)[0] == [1] * 6
    col = [[0 if x == 0 else 1 for x in range(6)] for _ in range(30)]
    assert all(r[0] == 8 for r in f(col))
    # blue line splitting black: still every black cell has a black neighbour
    split = [[1 if y == 1 else 0 for _ in range(3)] for y in range(3)]
    assert f(split) == [[8, 8, 8], [1, 1, 1], [8, 8, 8]]
    # singleton beside a pair, and diagonal contact only
    g = [[0, 1, 0], [1, 1, 0], [0, 1, 1]]
    assert f(g) == [[0, 1, 8], [1, 1, 8], [0, 1, 1]]
    with pytest.raises(ValueError):
        f([[0, 2]])
    with pytest.raises(ValueError):
        f([[0, 1], [0]])


def test_f3_histogram_cases():
    f = fixed_colour_histogram
    assert f([[4, 3, 2, 1]]) == [[1, 2, 3, 4]]
    tall = [[1, 2, 3, 4] for _ in range(30)]
    assert f(tall) == tall
    modal = [[1, 2, 3, 4] for _ in range(9)] + [[1, 0, 0, 0]]
    out = f(modal)
    assert out[0] == [1, 0, 0, 0] and out[-1] == [1, 2, 3, 4] and out[1] == [1, 2, 3, 4]
    wide = [[0] * 30 for _ in range(3)]
    wide[0][29], wide[1][0], wide[2][15], wide[2][14] = 1, 2, 3, 4
    assert f(wide) == [[0] * 30, [0] * 30, [1, 2, 3, 4] + [0] * 26]
    # narrow, missing colour, colour 5, count 2 > height 1, count 3 > height 2
    for bad in ([[1, 2, 3]], [[1, 2, 3, 0]], [[1, 2, 3, 4, 5]], [[1, 1, 2, 3, 4]],
                [[1, 2, 3, 4], [1, 1, 0, 0]]):
        with pytest.raises(ValueError):
            f(bad)
