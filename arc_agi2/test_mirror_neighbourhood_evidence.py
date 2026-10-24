"""Mirror-anchor / adjacency / dilation evidence gates (root-authorised, native batch E).

Each gate keeps the listed candidate rules that reproduce every demonstration and
requires them to agree on the query INPUT. Pairs here are labelled by an
independent restatement of each native rule; diversity/test_native_batch_e.py
checks that the constructors reproduce these exact witness scenes.
"""
import pytest

from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.mirror_neighbourhood_evidence import (ANCHORS, TASK_IDS, adjacency_variants,
                                                    dilation_variants, surviving_rules)
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
    assert surviving_rules("e0fb7511", NO_DIAGONAL) == {0, 1}
    # the competitor really differs on the query
    four, eight = adjacency_variants(DIAGONAL_QUERY["input"], list(range(10)))
    assert four == DIAGONAL_QUERY["output"] != eight
    assert everywhere("e0fb7511", NO_DIAGONAL + [DIAGONAL_QUERY]) == {False}
    assert everywhere("e0fb7511", NO_DIAGONAL + [blue(5, 5, {(0, 0), (1, 0), (3, 3)})]) == {True}
    with_diagonal = NO_DIAGONAL[:2] + [blue(5, 5, {(0, 0), (1, 1), (3, 3), (3, 4)})]
    assert surviving_rules("e0fb7511", with_diagonal) == {0}
    assert everywhere("e0fb7511", with_diagonal + [DIAGONAL_QUERY]) == {True}


def test_adjacency_uniform_queries_need_no_extra_evidence():
    # all-black and all-blue answers coincide under both neighbourhoods
    for colors in ([0] * 25, [1] * 25):
        q = gen("e0fb7511", width=5, height=5, colors=colors)
        assert everywhere("e0fb7511", NO_DIAGONAL + [q]) == {True}


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
