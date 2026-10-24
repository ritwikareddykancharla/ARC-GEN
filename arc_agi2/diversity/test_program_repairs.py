"""Regression checks for reviewed program repairs on broader RE-ARC domains.

Each family's earlier direct program failed augmented RE-ARC episodes although
both verifiers accepted the labels. The hand-built scenes reproduce each
failure mode. They are D4/palette variants of valid constructor scenes.
"""

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from arc_agi2.direct_certificates import certified_factory_source
from arc_agi2.augmentation import transformed
from arc_agi2.diversity.certify_programs import EPISODE_BUDGET, PAIR_BUDGET, PROGRAM_REPAIRS
from arc_agi2.diversity.rearc import generators, utils, verifiers
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import audit_target, compile_target, verify
from arc_agi2.runtime import call, grid, reference, verification_solver

ROOT = Path(__file__).parent
CERTS = ROOT.parent / "reports/diversity-v1/program-certificates"
FAMILIES = tuple(sorted(PROGRAM_REPAIRS))
PALETTE = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]


def run(tid, g, d4=0, palette=None):
    text, _ = compile_target(tid, d4, palette)
    namespace = {}
    exec(compile(text, "<target>", "exec"), namespace)
    return grid(namespace["solve"]([], [row[:] for row in g]))


@pytest.mark.parametrize("tid", FAMILIES)
def test_certificate_matches_current_sources(tid):
    cert = json.loads((CERTS / (tid + ".json")).read_text())
    assert cert["passed"] and cert["admission_gate_passed"] and not cert["bounded_stop"]
    assert cert["accepted_pairs"] >= PAIR_BUDGET
    assert cert["augmented_episode_checks"] >= EPISODE_BUDGET
    assert cert["fixture_variants_checked"] == 16
    native = cert["native_certificate"]
    assert native["fresh_pairs_checked"] >= 1000 and native["augmented_pair_checks"] >= 8000
    for name, digest in cert["dependency_sha256"].items():
        assert digest == hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest(), name
    text, _ = compile_target(tid)
    assert cert["program_sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert certified_factory_source(tid, 5, PALETTE) is not None


@pytest.mark.parametrize("tid", FAMILIES)
def test_native_fixtures_unchanged_under_all_transforms(tid):
    fixture = reference(tid)["canonical"]
    replay = importlib.import_module("tasks.task_" + tid).validate()
    for split in ("train", "test"):
        assert (sorted(json.dumps(p, sort_keys=True) for p in replay[split])
                == sorted(json.dumps(p, sort_keys=True) for p in fixture[split]))
    pairs = fixture["train"] + fixture["test"]
    for palette in (list(range(10)), PALETTE):
        for d4 in range(8):
            text, _ = compile_target(tid, d4, palette)
            audit_target(tid, text)
            verify(text, episode(pairs, d4, palette))


@pytest.mark.parametrize("tid", FAMILIES)
def test_fresh_rearc_episodes_under_all_d4(tid):
    """Labels pass both verifiers unchanged; the program is exact in every transform."""
    pairs, seed = [], 0
    while len(pairs) < 8:
        assert seed < 120, "unexpectedly high archived-verifier rejection rate"
        random.seed(20_000 + seed)
        utils.rng.clear()
        seed += 1
        try:
            raw = {k: grid(v) for k, v in
                   call(getattr(generators, "generate_" + tid), 0., 1., seconds=2).items()}
        except Exception:
            continue
        assert grid(call(getattr(verifiers, "verify_" + tid),
                         tuple(map(tuple, raw["input"])))) == raw["output"]
        try:
            agrees = grid(call(verification_solver(tid), raw["input"])) == raw["output"]
        except Exception:
            agrees = False
        if agrees:
            pairs.append(raw)
    palette = list(range(10))
    random.Random(tid).shuffle(palette)
    for offset in (0, 4):
        for d4 in range(8):
            text, _ = compile_target(tid, d4, palette)
            audit_target(tid, text)
            verify(text, episode(pairs[offset:offset + 4], d4, palette))


def test_63613498_bracket_found_by_geometry_not_size():
    # Bracket at the bottom-left corner (a D4 image of the native top-left one).
    # A green bar as large as the bracket (7 cells) precedes it in reading order.
    g = [[0] * 8 for _ in range(8)]
    for c in range(1, 8):
        g[0][c] = 3
    for c in range(0, 4):
        g[5][c] = 5
    for r in range(5, 8):
        g[r][3] = 5
    g[6][0] = g[7][0] = g[7][1] = 6         # key shape inside the bracket
    g[2][6] = g[3][6] = g[3][7] = 4         # matching shape elsewhere
    out = run("63613498", g)
    assert out[2][6] == out[3][6] == out[3][7] == 5
    assert out[0][1] == 3 and out[7][0] == 6


def test_57aa92db_complete_scaled_copy_does_not_become_template():
    # Template 1-2 (key 1 on the left) and a complete 2x copy in 3 come first in
    # reading order. Their non-key/scale ratios tie; the unscaled template wins.
    g = [[0] * 12 for _ in range(10)]
    for r in (0, 1):
        for c in (0, 1):
            g[r][c] = 1
        for c in (2, 3):
            g[r][c] = 3
    g[4][8], g[4][9] = 1, 2                  # unscaled template
    for r in (7, 8):
        for c in (2, 3):
            g[r][c] = 1                      # 2x key with nothing shown yet
    g[7][4] = 6                              # one visible cell of a 2x copy
    out = run("57aa92db", g)
    assert [out[r][c] for r in (7, 8) for c in (4, 5)] == [6] * 4
    assert out[0][2] == out[1][3] == 3 and out[4][9] == 2


def test_aabf363d_marker_is_rarer_colour_not_smallest_component():
    # RE-ARC drawings grow through diagonal neighbours. The single-pixel
    # 4-component at (1, 1) precedes the marker in reading order and ties it in size.
    g = [[7] * 6 for _ in range(6)]
    g[1][1] = 2
    for r in range(2, 5):
        for c in range(2, 5):
            g[r][c] = 2
    g[5][0] = 4                              # marker, native corner
    out = run("aabf363d", g)
    assert out[5][0] == 7 and out[1][1] == out[3][3] == 4
    assert sum(row.count(4) for row in out) == 10 and sum(row.count(2) for row in out) == 0
    tie = [[0, 0, 0, 0], [0, 1, 2, 0], [0, 0, 0, 0]]
    with pytest.raises(ValueError):
        run("aabf363d", tie)


def test_aabf363d_drawing_may_outnumber_background():
    # The drawing never reaches the border, so the border colour is the background.
    g = [[7] * 7 for _ in range(7)]
    for r in range(1, 6):
        for c in range(1, 6):
            g[r][c] = 2
    g[0][6] = 4
    out = run("aabf363d", g)
    assert out[0][6] == 7 and out[3][3] == 4 and out[0][0] == 7


def test_1a07d186_moves_are_drawn_after_all_strays_are_cleared():
    # A blue stray sits where a green stray must dock and comes later in
    # reading order. Clearing it used to erase the docked green pixel.
    g = [[0] * 7 for _ in range(9)]
    g[2] = [3] * 7                           # green line, row 2
    g[6] = [1] * 7                           # blue line, row 6
    g[0][4] = 3                              # green stray above its line
    g[1][4] = 1                              # blue stray on the green docking cell
    g[8][1] = 9                              # unmatched stray disappears
    out = run("1a07d186", g)
    assert out[1][4] == 3 and out[5][4] == 1
    assert out[0][4] == 0 and out[8][1] == 0
    for d4 in range(8):                      # every transform gives the same scene
        got = run("1a07d186", transformed(g, d4, PALETTE), d4, PALETTE)
        assert got == transformed(out, d4, PALETTE)


def test_fcb5c309_box_with_most_dots_wins_over_equal_sized_box():
    g = [[0] * 12 for _ in range(6)]
    for left in (0, 6):
        for r in range(5):
            for c in range(left, left + 5):
                if r in (0, 4) or c in (left, left + 4):
                    g[r][c] = 2
    g[1][7] = g[2][8] = g[3][9] = 4          # three dots in the right box
    g[2][2] = 4                              # one dot in the left box
    g[5][11] = 4                             # stray dot outside every box
    out = run("fcb5c309", g)
    assert out == [[4 if v == 2 else v for v in row[6:11]] for row in g[:5]]
    g[2][1] = g[3][3] = 4                    # now three dots each: ambiguous
    with pytest.raises(ValueError):
        run("fcb5c309", g)


def test_272f95fa_black_lines_are_found():
    # RE-ARC samples line colours from {0, 5, 7, 8, 9}; here lines are black on 9.
    g = [[9] * 7 for _ in range(7)]
    for i in range(7):
        g[2][i] = g[4][i] = g[i][1] = g[i][5] = 0
    out = run("272f95fa", g)
    assert out[0][3] == 2 and out[3][0] == 4 and out[3][3] == 6
    assert out[3][6] == 3 and out[6][3] == 1 and out[0][0] == 9


def test_8403a5d5_black_seed_on_coloured_background():
    g = [[6] * 6 for _ in range(5)]
    g[4][1] = 0
    out = run("8403a5d5", g)
    assert [out[r][1] for r in range(5)] == [0] * 5 and [out[r][3] for r in range(5)] == [0] * 5
    assert out[0][2] == 5 and out[4][4] == 5 and out[2][2] == 6
