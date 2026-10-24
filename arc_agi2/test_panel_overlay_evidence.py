"""Panel overlay evidence gates (root-authorised): 281123b4 priority, Boolean occupancy
for 195ba7dc (OR), 31d5ba1a (XOR) and 34b99a2b (XOR)."""

import importlib
import random

import pytest

from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.panel_overlay_evidence import (ORDERS, observed_truth_table, predict_from_table,
                                             surviving_orders)
from arc_agi2.panel_overlay_evidence import priority_predictions as predictions
from arc_agi2.program_targets import compile_target, make_record, verify
from arc_agi2.runtime import reference

TID = "281123b4"
NATIVE_ORDER = ORDERS.index((2, 3, 0, 1))  # panel colours (8,5,9,4): 9 > 4 > 8 > 5
PALETTES = (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5], [7, 1, 5, 0, 6, 9, 2, 4, 3, 8])
PANEL = {8: "top", 5: "upper", 9: "lower", 4: "bottom"}


def gen(**kw):
    return importlib.import_module("tasks.task_" + TID).generate(**kw)


def scene(cells, width=4, height=1):
    """cells: list of colour sets per output cell (row-major)."""
    masks = {name: [int(c in s) for s in cells] for c, name in PANEL.items()}
    return gen(width=width, height=height, **masks)


def gate(pairs, d4=0, palette=None):
    palette = list(range(10)) if palette is None else palette
    ep = episode(pairs, d4, palette)
    require_colour_evidence(TID, ep["train"], ep["test"], palette, d4)


def accepted(pairs, **kw):
    try:
        gate(pairs, **kw)
        return True
    except MissingColourEvidence:
        return False


DISJOINT = [scene([{8}, {5}, {9}, {4}]), scene([{4}, set(), {8}, {5}]), scene([{9}, {9}, {5}, set()])]
# one 4x4 demo enumerating all 16 panel subsets determines the full order
ALL_SUBSETS = scene([{c for k, c in enumerate((8, 5, 9, 4)) if i >> k & 1} for i in range(16)],
                    width=4, height=4)
OVERLAP_QUERY = scene([{8, 5}, set(), {9}, {4}])


def test_canonical_fixtures_accepted_with_unique_order():
    fx = reference(TID)["canonical"]
    pairs = fx["train"] + fx["test"]
    assert surviving_orders(fx["train"]) == {NATIVE_ORDER}
    for palette in PALETTES:
        for d4 in range(8):
            gate(pairs, d4, palette)


def test_constructor_labels_match_native_order():
    for seed in range(300):
        random.seed(seed)
        w, h = random.randint(1, 6), random.randint(1, 30)
        p = gen(width=w, height=h)
        assert [list(r) for r in predictions(p["input"])[NATIVE_ORDER]] == p["output"]


def test_ambiguous_nonoverlap_demos_rejected():
    assert len(surviving_orders(DISJOINT)) == 24
    with pytest.raises(MissingColourEvidence, match="unresolved"):
        gate(DISJOINT + [OVERLAP_QUERY])
    ep = episode(DISJOINT + [OVERLAP_QUERY], 0, list(range(10)))
    ep.update(task_id=TID, episode_id="t", d4_transform=0, color_permutation=list(range(10)))
    with pytest.raises(MissingColourEvidence):
        make_record(ep)  # production export path enforces the gate


def test_informative_overlaps_accepted():
    demos = [ALL_SUBSETS, DISJOINT[0], DISJOINT[1]]
    assert surviving_orders(demos) == {NATIVE_ORDER}
    for seed in range(20):
        random.seed(seed)
        gate(demos + [gen(width=random.randint(1, 6), height=random.randint(1, 30))])
    ep = episode(demos + [OVERLAP_QUERY], 3, PALETTES[1])
    ep.update(task_id=TID, episode_id="t", d4_transform=3, color_permutation=PALETTES[1])
    make_record(ep)


def test_query_independent_case_allowed_despite_unresolved_order():
    demos = [scene([{9, 4}, {9}, {4}, set()]), scene([{4, 8}, {8}, set(), {5}]),
             scene([{5}, {8}, {9}, {4}])]
    alive = surviving_orders(demos)
    assert 1 < len(alive) < 24  # 9>4 and 4>8 shown; 8 vs 5 and 9 vs 8 unresolved
    assert accepted(demos + [scene([{9, 4}, {4, 8}, {9, 4, 8}, {5}])])
    # 8&5 overlap without a dominating colour depends on the unresolved pair
    assert not accepted(demos + [scene([{8, 5}, set(), set(), set()])])
    # candidate rules are total orders, so 9>4 and 4>8 already imply 9>8
    assert accepted(demos + [scene([{9, 8}, set(), set(), set()])])
    # colour 5's rank is still free (it may sit above 9), so a full-overlap cell is open
    assert not accepted(demos + [scene([{9, 4, 8, 5}, set(), set(), set()])])
    assert not accepted(demos + [scene([{9, 5}, set(), set(), set()])])


@pytest.mark.parametrize("palette", PALETTES)
def test_d4_palette_robust(palette):
    cases = {
        "ambiguous": (DISJOINT + [OVERLAP_QUERY], False),
        "informative": ([ALL_SUBSETS, DISJOINT[0], DISJOINT[2], OVERLAP_QUERY], True),
    }
    for name, (pairs, expected) in cases.items():
        for d4 in range(8):
            assert accepted(pairs, d4=d4, palette=palette) is expected, (name, d4)
            ep = episode(pairs, d4, palette)
            assert len(surviving_orders(ep["train"], palette)) == len(surviving_orders(pairs[:3]))


class InputOnly(dict):
    def __getitem__(self, key):
        if key != "input":
            raise AssertionError("gate read a query answer: " + key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        return self[key] if key in self else default


def test_never_reads_query_answers():
    for demos, query, ok in ((DISJOINT, OVERLAP_QUERY, False),
                             ([ALL_SUBSETS] + DISJOINT[:2], OVERLAP_QUERY, True)):
        q = InputOnly(input=query["input"], output=[[1]])
        try:
            require_colour_evidence(TID, demos, [q])
            assert ok
        except MissingColourEvidence:
            assert not ok


def test_structural_failures_are_evidence_failures():
    bad = [[8, 3, 5], [0, 3, 0]]  # one separator only
    with pytest.raises(MissingColourEvidence):
        require_colour_evidence(TID, [ALL_SUBSETS], [{"input": bad}])
    wrong = {"input": DISJOINT[0]["input"], "output": [[5, 8, 9, 4]]}  # contradicts every order
    with pytest.raises(MissingColourEvidence, match="fit no"):
        require_colour_evidence(TID, [wrong], [{"input": OVERLAP_QUERY["input"]}])




# ------------------------------------------------- Boolean occupancy families

BOOL = {"195ba7dc": lambda a, b: a or b, "31d5ba1a": lambda a, b: a != b,
        "34b99a2b": lambda a, b: a != b}


def bgen(tid, combos, width=None, height=1):
    """Pair whose output cells have the given ordered (top, bottom) occupancies."""
    width = len(combos) // height if width is None else width
    mod = importlib.import_module("tasks.task_" + tid)
    return mod.generate(top=[a for a, _ in combos], bottom=[b for _, b in combos],
                        width=width, height=height)


def bgate(tid, pairs, d4=0, palette=None):
    palette = list(range(10)) if palette is None else palette
    ep = episode(pairs, d4, palette)
    try:
        require_colour_evidence(tid, ep["train"], ep["test"], palette, d4)
        return True
    except MissingColourEvidence:
        return False


ALL4 = [(0, 0), (1, 0), (0, 1), (1, 1)]


@pytest.mark.parametrize("tid", sorted(BOOL))
def test_boolean_canonical_and_constructor_labels(tid):
    fx = reference(tid)["canonical"]
    pairs = fx["train"] + fx["test"]
    for palette in PALETTES:
        for d4 in range(8):
            assert bgate(tid, pairs, d4, palette)
    table = observed_truth_table(tid, fx["train"])
    assert set(table) == set(ALL4)
    assert {c: bool(v) for c, v in table.items()} == {c: bool(BOOL[tid](*c)) for c in ALL4}
    mod = importlib.import_module("tasks.task_" + tid)
    for seed in range(200):
        random.seed(seed)
        p = mod.generate(width=random.randint(1, 14), height=random.randint(1, 15))
        assert predict_from_table(tid, table, p["input"]) == p["output"]


@pytest.mark.parametrize("tid", sorted(BOOL))
def test_nonoverlap_or_vs_xor_rejected(tid):
    # no (1,1) cell in any demo: OR and XOR both fit, so a (1,1) query is unresolved
    demos = [bgen(tid, [(0, 0), (1, 0), (0, 1), (0, 0)]) for _ in range(3)]
    assert not bgate(tid, demos + [bgen(tid, [(1, 1), (0, 0), (1, 0), (0, 1)])])
    assert bgate(tid, demos + [bgen(tid, [(0, 1), (0, 0), (1, 0), (0, 1)])])
    with_overlap = demos[:2] + [bgen(tid, ALL4)]
    assert bgate(tid, with_overlap + [bgen(tid, [(1, 1), (1, 1), (0, 0), (0, 1)])])


@pytest.mark.parametrize("tid", sorted(BOOL))
def test_missing_00_rejected(tid):
    demos = [bgen(tid, [(1, 0), (0, 1), (1, 1), (1, 0)]) for _ in range(3)]
    assert not bgate(tid, demos + [bgen(tid, [(0, 0), (1, 0), (0, 1), (1, 1)])])
    assert bgate(tid, demos + [bgen(tid, [(1, 1), (1, 0), (0, 1), (1, 1)])])


@pytest.mark.parametrize("tid", sorted(BOOL))
def test_boolean_inconsistent_and_structural(tid):
    good = bgen(tid, ALL4)
    flipped = {"input": good["input"], "output": [[9] + good["output"][0][1:]]}  # (0,0) -> 9 and 0
    other = bgen(tid, ALL4)
    with pytest.raises(MissingColourEvidence, match="fit no"):
        require_colour_evidence(tid, [other, flipped], [{"input": good["input"]}])
    with pytest.raises(MissingColourEvidence):
        require_colour_evidence(tid, [good], [{"input": [[0, 0, 0]]}])


@pytest.mark.parametrize("tid", sorted(BOOL))
@pytest.mark.parametrize("palette", PALETTES)
def test_boolean_d4_palette_robust(tid, palette):
    # height 2, width 4: 31d5ba1a inputs are 4x4 squares, so the axis must come from d4
    demos_amb = [bgen(tid, [(0, 0), (1, 0), (0, 1), (0, 0)] * 2, width=4, height=2)
                 for _ in range(3)]
    demos_ok = demos_amb[:2] + [bgen(tid, ALL4 * 2, width=4, height=2)]
    query = bgen(tid, [(1, 1), (0, 1), (1, 0), (0, 0)] * 2, width=4, height=2)
    for d4 in range(8):
        assert not bgate(tid, demos_amb + [query], d4, palette)
        assert bgate(tid, demos_ok + [query], d4, palette)
        ep = episode(demos_ok + [query], d4, palette)
        table = observed_truth_table(tid, ep["train"], palette, d4)
        assert predict_from_table(tid, table, ep["test"][0]["input"], palette, d4) == ep["solutions"][0]


@pytest.mark.parametrize("tid", sorted(BOOL))
def test_boolean_never_reads_query_answers(tid):
    demos = [bgen(tid, ALL4)] * 3
    q = InputOnly(input=bgen(tid, [(1, 1)] * 4)["input"], output=[[1]])
    require_colour_evidence(tid, demos, [q])


def ambiguous_and_informative(tid):
    if tid == TID:
        return DISJOINT + [OVERLAP_QUERY], [ALL_SUBSETS, DISJOINT[0], DISJOINT[1], OVERLAP_QUERY]
    demos = [bgen(tid, [(0, 0), (1, 0), (0, 1), (0, 0)]) for _ in range(3)]
    query = bgen(tid, [(1, 1), (0, 0), (1, 0), (0, 1)])
    return demos + [query], demos[:2] + [bgen(tid, ALL4), query]


@pytest.mark.parametrize("tid", [TID] + sorted(BOOL))
def test_make_record_invokes_gate_while_verify_alone_passes(tid):
    amb, ok = ambiguous_and_informative(tid)
    for pairs, should_pass in ((amb, False), (ok, True)):
        for d4, palette in ((0, list(range(10))), (5, PALETTES[2])):
            ep = episode(pairs, d4, palette)
            ep.update(task_id=tid, episode_id="t", d4_transform=d4, color_permutation=palette)
            source, _ = compile_target(tid, d4, palette)
            verify(source, ep)  # the exported program is right either way
            if should_pass:
                make_record(ep)
            else:
                with pytest.raises(MissingColourEvidence):
                    make_record(ep)
