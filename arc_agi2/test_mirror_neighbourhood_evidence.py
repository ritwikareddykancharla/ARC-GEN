"""Mirror-anchor / adjacency / dilation evidence gates (root-authorised, native batch E).

Each gate keeps the listed candidate rules that reproduce every demonstration and
requires them to agree on the query INPUT. Pairs here are labelled by an
independent restatement of each native rule; diversity/test_native_batch_e.py
checks that the constructors reproduce these exact witness scenes.
"""
import random

import pytest

from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.mirror_neighbourhood_evidence import (ANCHORS, TASK_IDS, candidate_predictions,
                                                    dilation_variants, surviving_rules,
                                                    surviving_thresholds, threshold_output)
from arc_agi2.program_targets import compile_target, make_record, verify
from arc_agi2.runtime import reference

PALETTES = (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5], [7, 1, 5, 0, 6, 9, 2, 4, 3, 8])


def gen(tid, width, height, colors):
    """Native pair for an explicit row-major scene (independent labeller)."""
    a = [list(colors[r * width:(r + 1) * width]) for r in range(height)]
    if tid == "0c786b71":       # unflipped input bottom-right, mirrored outward
        half = [r[::-1] + r for r in a]
        return {"input": a, "output": half[::-1] + half}
    out = [r[:] for r in a]
    for y in range(height):
        for x in range(width):
            near = lambda steps: [(y + dy, x + dx) for dy, dx in steps
                                  if 0 <= y + dy < height and 0 <= x + dx < width]
            if tid == "e0fb7511" and a[y][x] == 0:
                if any(a[r][c] == 0 for r, c in near(((1, 0), (-1, 0), (0, 1), (0, -1)))):
                    out[y][x] = 8
            if tid == "f0df5ff0" and a[y][x] == 1:
                for r, c in near([(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)]):
                    if a[r][c] == 0:
                        out[r][c] = 1
    return {"input": a, "output": out}


def accepted(tid, pairs, d4=0, palette=None):
    palette = list(range(10)) if palette is None else palette
    ep = episode(pairs, d4, palette)
    # episode() exposes only the query INPUT to the gate
    assert set(ep["test"][0]) == {"input"}
    try:
        require_colour_evidence(tid, ep["train"], ep["test"], palette, d4)
        return True
    except MissingColourEvidence:
        return False


def everywhere(tid, pairs):
    return {accepted(tid, pairs, d4, p) for d4 in range(8) for p in PALETTES}


@pytest.mark.parametrize("tid", TASK_IDS)
@pytest.mark.parametrize("version", ("canonical", "teaching_fixture"))
def test_fixtures_accepted_with_native_rule_alone(tid, version):
    fx = reference(tid)[version]
    if tid == "e0fb7511":
        assert surviving_thresholds(fx["train"]) == {"four": (2, 2)}
    else:
        native = ANCHORS.index("BR") if tid == "0c786b71" else 0
        assert surviving_rules(tid, fx["train"]) == {native}
    assert everywhere(tid, fx["train"] + fx["test"]) == {True}


# ---------------------------------------------------------------- 0c786b71
SYMMETRIC_DEMOS = [gen("0c786b71", width=3, height=2, colors=c) for c in
                   ([1, 2, 1, 3, 3, 3], [4, 5, 4, 4, 4, 4], [6, 6, 6, 7, 8, 7])]


def test_mirror_symmetric_demos_leave_two_anchors():
    # Left-right symmetric demos cannot separate BR from BL (nor TL from TR).
    assert surviving_rules("0c786b71", SYMMETRIC_DEMOS) == {ANCHORS.index("BL"),
                                                            ANCHORS.index("BR")}
    asymmetric = gen("0c786b71", width=3, height=2, colors=[1, 2, 3, 4, 5, 6])
    symmetric = gen("0c786b71", width=3, height=2, colors=[2, 9, 2, 1, 1, 1])
    assert everywhere("0c786b71", SYMMETRIC_DEMOS + [asymmetric]) == {False}
    assert everywhere("0c786b71", SYMMETRIC_DEMOS + [symmetric]) == {True}
    # one fully asymmetric demonstration resolves the anchor
    assert everywhere("0c786b71", SYMMETRIC_DEMOS[:2] + [gen(
        "0c786b71", width=3, height=2, colors=[5, 5, 6, 7, 5, 5]), asymmetric]) == {True}


def test_mirror_gate_runs_inside_make_record_but_not_verify():
    pairs = SYMMETRIC_DEMOS + [gen("0c786b71", width=3, height=2, colors=[1, 2, 3, 4, 5, 6])]
    ep = episode(pairs, 0, list(range(10)))
    verify(compile_target("0c786b71")[0], ep)   # program is exact; context is not
    ep.update(task_id="0c786b71", episode_id="t", d4_transform=0,
              color_permutation=list(range(10)))
    with pytest.raises(MissingColourEvidence):
        make_record(ep)


# ---------------------------------------------------------------- e0fb7511
def blue(width, height, black):
    return gen("e0fb7511", width=width, height=height,
               colors=[0 if (r, c) in black else 1 for r in range(height) for c in range(width)])


# orthogonal pairs and isolated singletons only: no diagonal-only contact
NO_DIAGONAL = [blue(5, 5, {(0, 0), (0, 1), (3, 3)}), blue(5, 5, {(1, 4), (2, 4), (4, 0)}),
               blue(5, 5, {(2, 1), (2, 2), (0, 4), (4, 4)})]
DIAGONAL_QUERY = blue(5, 5, {(1, 1), (2, 2), (4, 4)})


def test_adjacency_diagonal_witness():
    assert surviving_thresholds(NO_DIAGONAL) == {"four": (2, 2), "eight": (2, 2)}
    # the competitor really differs on the query
    four = threshold_output(DIAGONAL_QUERY["input"], list(range(10)), "four", 2)
    eight = threshold_output(DIAGONAL_QUERY["input"], list(range(10)), "eight", 2)
    assert four == DIAGONAL_QUERY["output"] != eight
    assert everywhere("e0fb7511", NO_DIAGONAL + [DIAGONAL_QUERY]) == {False}
    assert everywhere("e0fb7511", NO_DIAGONAL + [blue(5, 5, {(0, 0), (1, 0), (3, 3)})]) == {True}
    with_diagonal = NO_DIAGONAL[:2] + [blue(5, 5, {(0, 0), (1, 1), (3, 3), (3, 4)})]
    assert surviving_thresholds(with_diagonal) == {"four": (2, 2)}
    assert everywhere("e0fb7511", with_diagonal + [DIAGONAL_QUERY]) == {True}


# distinct 5x5 demos with no diagonal-only contact, so only the threshold varies
PAIRS_ONLY = [blue(5, 5, {(0, 0), (0, 1), (3, 3), (4, 3)}), blue(5, 5, {(2, 0), (2, 1)}),
              blue(5, 5, {(1, 4), (2, 4), (4, 0), (4, 1)})]
NO_PAIR = [blue(5, 5, {(0, 0), (0, 1), (0, 2), (3, 3)}), blue(5, 5, {(4, 4), (2, 0), (2, 1), (2, 2)}),
           blue(5, 5, {(0, 4), (1, 4), (2, 4), (3, 4), (4, 0)})]
FOURS_ONLY = [blue(5, 5, {(0, 0), (0, 1), (0, 2), (0, 3), (3, 3)}),
              blue(5, 5, {(2, 0), (2, 1), (3, 0), (3, 1), (0, 4)}),
              blue(5, 5, {(4, 1), (4, 2), (4, 3), (4, 4), (1, 4)})]
SINGLETONS_ONLY = [blue(5, 5, {(0, 0), (2, 2)}), blue(5, 5, {(4, 4), (0, 2)}),
                   blue(5, 5, {(2, 0), (4, 2), (0, 4)})]


@pytest.mark.parametrize("demos,interval,ambiguous,resolved", [
    # no isolated cell shown: T = 1 (mark every black cell) survives
    (PAIRS_ONLY, (1, 2), blue(5, 5, {(0, 0), (0, 1), (3, 3)}), blue(5, 5, {(1, 1), (1, 2)})),
    # no marked 2-cell component shown: T = 3 survives
    (NO_PAIR, (2, 3), blue(5, 5, {(0, 0), (0, 1), (3, 3)}), blue(5, 5, {(0, 0), (0, 1), (0, 2)})),
    # only 4-cell components marked: T in 2..4 survive; a 3-cell query is ambiguous
    (FOURS_ONLY, (2, 4), blue(5, 5, {(0, 0), (0, 1), (0, 2)}),
     blue(5, 5, {(0, 0), (0, 1), (0, 2), (0, 3), (4, 4)})),
    # nothing marked: every T >= 2, including "mark none", survives
    (SINGLETONS_ONLY, (2, None), blue(5, 5, {(1, 1), (1, 2)}), blue(5, 5, {(1, 1), (3, 3)})),
])
def test_threshold_witnesses(demos, interval, ambiguous, resolved):
    assert surviving_thresholds(demos)["four"] == interval
    assert len(candidate_predictions("e0fb7511", demos, ambiguous["input"])) > 1
    assert everywhere("e0fb7511", demos + [ambiguous]) == {False}
    assert everywhere("e0fb7511", demos + [resolved]) == {True}


def test_informative_context_accepts_any_query():
    informative = [blue(5, 5, {(0, 0), (0, 1), (3, 3)}), blue(5, 5, {(0, 0), (1, 1), (4, 4)}),
                   blue(5, 5, {(2, 1), (2, 2), (2, 3), (0, 4)})]
    assert surviving_thresholds(informative) == {"four": (2, 2)}
    rng = random.Random(3)
    for _ in range(20):
        q = blue(6, 4, {(r, c) for r in range(4) for c in range(6) if rng.random() < 0.4})
        assert candidate_predictions("e0fb7511", informative, q["input"]) == [q["output"]]
        assert accepted("e0fb7511", informative + [q], rng.randrange(8), rng.choice(PALETTES))


def test_adjacency_uniform_queries_need_no_extra_evidence():
    # all-blue answers never depend on the rule; all-black ones only if T is
    # bounded by the size of the demos' marked components (here T = 2)
    for colors in ([0] * 25, [1] * 25):
        q = gen("e0fb7511", width=5, height=5, colors=colors)
        assert everywhere("e0fb7511", NO_DIAGONAL + [q]) == {True}


def test_threshold_demos_fitting_no_rule_are_rejected():
    pair = blue(4, 1, {(0, 0), (0, 1)})
    partial = {"input": pair["input"], "output": [[8, 0, 1, 1]]}
    recoloured = {"input": pair["input"], "output": [[8, 8, 1, 0]]}
    inverted = {"input": [[0, 1, 0, 0]], "output": [[8, 1, 0, 0]]}   # singleton marked, pair not
    for bad in (partial, recoloured, inverted):
        assert surviving_thresholds([bad]) == {}
        assert candidate_predictions("e0fb7511", [bad], pair["input"]) == []
        assert not accepted("e0fb7511", [bad, pair])


def _brute(grid, connectivity, threshold):
    """Independent labeller: flood fill, mark components of >= threshold cells."""
    h, w = len(grid), len(grid[0])
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if connectivity == "eight":
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    out, seen = [r[:] for r in grid], set()
    for y in range(h):
        for x in range(w):
            if grid[y][x] or (y, x) in seen:
                continue
            comp, frontier = {(y, x)}, [(y, x)]
            while frontier:
                cy, cx = frontier.pop()
                for dy, dx in steps:
                    n = (cy + dy, cx + dx)
                    if 0 <= n[0] < h and 0 <= n[1] < w and not grid[n[0]][n[1]] and n not in comp:
                        comp.add(n)
                        frontier.append(n)
            seen |= comp
            if len(comp) >= threshold:
                for cy, cx in comp:
                    out[cy][cx] = 8
    return out


def test_threshold_interval_matches_exhaustive_enumeration():
    rng = random.Random(11)
    rules = [(c, t) for c in ("four", "eight") for t in range(1, 18)]   # 17 > any 4x4 component
    ambiguous = 0
    for case in range(300):
        h, w = rng.randint(1, 4), rng.randint(1, 4)
        label_rule = rng.choice(rules)
        inputs = [[[0 if rng.random() < rng.choice((0.3, 0.6, 0.9)) else 1 for _ in range(w)]
                   for _ in range(h)] for _ in range(4)]
        demos = [{"input": g, "output": _brute(g, *label_rule)} for g in inputs[:3]]
        fitting = [r for r in rules if all(_brute(d["input"], *r) == d["output"] for d in demos)]
        expected = []
        for r in fitting:
            answer = _brute(inputs[3], *r)
            if answer not in expected:
                expected.append(answer)
        got = candidate_predictions("e0fb7511", demos, inputs[3])
        # extremal answers are real answers, and agreement is decided exactly
        assert all(g in expected for g in got), case
        assert (len(got) == 1) == (len(expected) == 1), case
        if len(got) == 1:
            assert got == expected
        assert {c for c, _ in fitting} == set(surviving_thresholds(demos))
        for c, (low, high) in surviving_thresholds(demos).items():
            ts = [t for cc, t in fitting if cc == c]
            assert min(ts) == low and (max(ts) == high if high else max(ts) == 17), case
        ambiguous += len(expected) > 1
    assert ambiguous > 20                     # the crosscheck exercises both outcomes


# ---------------------------------------------------------------- f0df5ff0
def seeded(diagonal_zero):
    """5x5 with a centre seed whose diagonal cells hold confetti 3 (unless listed)."""
    colors = [0] * 25
    colors[12] = 1
    for r, c in ((1, 1), (1, 3), (3, 1), (3, 3)):
        if (r, c) not in diagonal_zero:
            colors[r * 5 + c] = 3
    return colors


CROSS_ONLY = [gen("f0df5ff0", width=5, height=5, colors=c) for c in
              (seeded(()), seeded(()) [:24] + [7], [9] + seeded(())[1:])]


def test_dilation_square_vs_cross_witness():
    assert surviving_rules("f0df5ff0", CROSS_ONLY) == {0, 1}
    q = gen("f0df5ff0", width=5, height=5, colors=seeded({(1, 1)}))
    square, cross = dilation_variants(q["input"], list(range(10)))
    assert square == q["output"] != cross
    assert everywhere("f0df5ff0", CROSS_ONLY + [q]) == {False}
    blocked = gen("f0df5ff0", width=5, height=5, colors=seeded(()))
    assert everywhere("f0df5ff0", CROSS_ONLY[:2] + [CROSS_ONLY[2], blocked]) == {True}
    resolved = CROSS_ONLY[:2] + [gen("f0df5ff0", width=5, height=5, colors=seeded({(3, 3)}))]
    assert surviving_rules("f0df5ff0", resolved) == {0}
    assert everywhere("f0df5ff0", resolved + [q]) == {True}


def test_demonstrations_fitting_no_candidate_are_rejected():
    fx = reference("f0df5ff0")["canonical"]
    broken = [dict(p) for p in fx["train"]]
    broken[0] = {"input": broken[0]["input"], "output": broken[0]["input"]}
    assert not accepted("f0df5ff0", broken + fx["test"])


def test_histogram_family_is_not_gated():
    # every f3cdc58f pair shows all four bars; no gate was added for it
    assert require_colour_evidence("f3cdc58f", [], [{"input": [[1, 2, 3, 4]]}]) is None
