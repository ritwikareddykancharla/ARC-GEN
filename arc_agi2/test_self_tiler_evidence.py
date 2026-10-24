"""Self-tiler demonstration gate (27f8ce4f, 48f8583b, 5b6cbef5).

The gate keeps every candidate of a finite family (selector x placement x
content x fill) that reproduces every demonstration, and requires one answer on
each query input. These tests cover fixture acceptance, named competitor
witnesses that are constructor scenes, query-answer independence, monochrome
48f8583b support, a brute-force cross-check, and the make_record wiring.
"""
import importlib
import json
import random

import pytest

from arc_agi2.augmentation import transformed
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import make_record, verify
from arc_agi2.runtime import BASE, call, grid, reference
from arc_agi2.self_tiler_evidence import (CONTENTS, SELECTORS, TASK_IDS, candidate_predictions,
                                          exported_candidate, placements, predict,
                                          require_self_tiler_evidence, surviving_candidates)

PALETTES = (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5], [5, 1, 2, 3, 4, 0, 6, 7, 8, 9])
WITNESSES = BASE / "reports/diversity-v1/native-batch-f/pregate-witnesses.json"


def gen(tid, **kw):
    p = call(importlib.import_module("tasks.task_" + tid).generate, seconds=3, **kw)
    return {k: grid(v) for k, v in p.items()}


def scene(tid, colors, h, w):
    return gen(tid, colors=colors, height=h, width=w)


def ambiguous(tid, demos, query):
    with pytest.raises(MissingColourEvidence):
        require_self_tiler_evidence(tid, demos, [{"input": query["input"]}])


@pytest.mark.parametrize("tid", TASK_IDS)
def test_fixtures_accepted_under_d4_and_palettes(tid):
    for name in ("canonical", "teaching_fixture"):
        f = reference(tid)[name]
        pairs = f["train"] + f["test"]
        for palette in PALETTES:
            for d4 in range(8):
                ps = [{k: transformed(p[k], d4, palette) for k in ("input", "output")}
                      for p in pairs]
                answers = candidate_predictions(tid, ps[:-1], ps[-1]["input"], palette)
                assert answers == [ps[-1]["output"]]
                assert exported_candidate(tid, palette)[:3] in surviving_candidates(ps[:-1])


def test_exported_rule_reproduces_constructor():
    for tid in TASK_IDS:
        for seed in range(200):
            random.seed(f"exported:{tid}:{seed}")
            p = gen(tid)
            assert predict(p["input"], *exported_candidate(tid)) == p["output"]


def test_fixed_colour_witness_modal():
    """Demos whose modal colour is always 1; query modal colour 2."""
    demos = [scene("27f8ce4f", c, 3, 3) for c in (
        [1, 1, 1, 2, 3, 4, 1, 2, 3], [2, 1, 3, 1, 1, 4, 5, 1, 3], [1, 3, 4, 1, 4, 1, 3, 1, 5])]
    query = scene("27f8ce4f", [2, 2, 1, 3, 2, 4, 2, 3, 1], 3, 3)
    ambiguous("27f8ce4f", demos, query)
    fixed = ("colour:1", "id", "id", 0)
    assert all(predict(d["input"], *fixed) == d["output"] for d in demos)
    assert predict(query["input"], *fixed) != query["output"]
    # A demo with another modal colour refutes the fixed-colour competitor.
    demos[2] = scene("27f8ce4f", [3, 3, 4, 3, 4, 3, 5, 3, 1], 3, 3)
    assert ("colour:1", "id", "id") not in surviving_candidates(demos)


def test_frequency_swap_witness_one_ink_masks():
    """Sparse demos fit 'minority'; a dense query separates it from 'inked'."""
    demos = [scene("5b6cbef5", c, 3, 3) for c in (
        [1, 0, 0, 0, 1, 0, 0, 0, 0], [0, 2, 0, 0, 0, 0, 2, 0, 2], [0, 0, 0, 3, 3, 0, 0, 0, 0])]
    query = scene("5b6cbef5", [4, 4, 0, 4, 4, 4, 0, 4, 4], 3, 3)
    ambiguous("5b6cbef5", demos, query)
    assert predict(query["input"], "minority", "id", "id", 0) != query["output"]
    demos[2] = scene("5b6cbef5", [5, 5, 5, 0, 5, 5, 0, 5, 0], 3, 3)    # dense demo
    assert candidate_predictions("5b6cbef5", demos, query["input"]) == [query["output"]]


def test_monochrome_48f8583b_supported_and_fill_evidence():
    mono = scene("48f8583b", [7] * 9, 3, 3)
    multi = [scene("48f8583b", c, 3, 3) for c in (
        [1, 2, 2, 2, 2, 3, 3, 3, 3], [4, 4, 6, 4, 4, 4, 5, 5, 5], [8, 9, 9, 8, 8, 8, 8, 8, 8])]
    # Monochrome queries are accepted when the demos settle the rule.
    require_self_tiler_evidence("48f8583b", multi, [{"input": mono["input"]}])
    # Monochrome demos alone never show the fill colour: a multi-colour query is ambiguous.
    monos = [scene("48f8583b", [c] * 9, 3, 3) for c in (1, 2, 3)]
    ambiguous("48f8583b", monos, multi[0])
    # One monochrome demo among informative ones is fine.
    require_self_tiler_evidence("48f8583b", [mono] + multi[:2], [{"input": multi[2]["input"]}])


def test_corner_anchor_and_placement_witnesses():
    # Every demo has its modal colour in the top-left corner; the query does not.
    demos = [scene("27f8ce4f", c, 3, 3) for c in (
        [1, 2, 1, 3, 1, 4, 1, 2, 3], [5, 6, 7, 5, 5, 8, 6, 5, 7], [9, 9, 2, 3, 9, 4, 9, 2, 3])]
    query = scene("27f8ce4f", [2, 1, 1, 3, 1, 4, 1, 2, 1], 3, 3)
    ambiguous("27f8ce4f", demos, query)
    assert ("corner:tl", "id", "id") in surviving_candidates(demos)


def test_query_answers_never_read():
    random.seed(11)
    for tid in TASK_IDS:
        pairs = [gen(tid, height=3, width=4) for _ in range(4)]
        q = {"input": pairs[3]["input"]}
        a = candidate_predictions(tid, pairs[:3], q["input"])
        poisoned = dict(q, output=[[9]])
        assert candidate_predictions(tid, pairs[:3], poisoned["input"]) == a


def test_no_fit_and_shape_mismatch_rejected():
    demo = gen("27f8ce4f", height=3, width=3)
    bad = dict(demo, output=[r[:] for r in demo["output"]])
    bad["output"][0][0] = (bad["output"][0][0] + 1) % 10
    with pytest.raises(MissingColourEvidence, match="fit no"):
        require_self_tiler_evidence("27f8ce4f", [bad], [{"input": demo["input"]}])
    with pytest.raises(MissingColourEvidence, match="fit no"):
        require_self_tiler_evidence("27f8ce4f", [dict(demo, output=demo["input"])],
                                    [{"input": demo["input"]}])


def test_brute_force_cross_check():
    """Agreement computed by enumerating every candidate equals the gate's verdict."""
    rng = random.Random(5)
    for trial in range(120):
        tid = TASK_IDS[trial % 3]
        h, w = rng.choice([(2, 2), (2, 3), (3, 3), (3, 2)])
        random.seed(rng.random())
        pairs = [gen(tid, height=h, width=w) for _ in range(4)]
        demos, q = pairs[:3], pairs[3]["input"]
        answers = set()
        for s in SELECTORS:
            for p in placements(h, w):
                for c in CONTENTS:
                    for f in range(10):
                        cand = (s, p, c, f)
                        if all(predict(d["input"], *cand) == d["output"] for d in demos):
                            out = predict(q, *cand)
                            answers.add(None if out is None else json.dumps(out))
        gate = {None if a is None else json.dumps(a)
                for a in candidate_predictions(tid, demos, q)}
        assert gate == answers and json.dumps(pairs[3]["output"]) in gate


@pytest.mark.parametrize("tid", TASK_IDS)
def test_pregate_witnesses_now_rejected(tid):
    """Every recorded make_record-accepted pre-gate witness is now rejected by
    make_record on all 8 D4 transforms; the program itself still verifies."""
    report = json.loads(WITNESSES.read_text())
    seen = 0
    for shape in report["families"][tid].values():
        for name, wit in shape["witnesses"].items():
            pairs = wit["demonstrations"] + [{"input": wit["query_input"], "output": wit["label"]}]
            for d4 in range(8):
                ep = episode(pairs, d4, wit["palette"])
                ep.update(task_id=tid, episode_id=f"w-{tid}-{name}-{d4}", d4_transform=d4,
                          color_permutation=wit["palette"])
                with pytest.raises(MissingColourEvidence):
                    make_record(ep)
                from arc_agi2.program_targets import compile_target
                verify(compile_target(tid, d4, wit["palette"])[0], ep)
            seen += 1
    assert seen >= 2


def test_dispatch_is_narrow():
    random.seed(2)
    demos = [gen("5b6cbef5", height=3, width=3) for _ in range(3)]
    q = gen("5b6cbef5", height=3, width=3)
    for tid in TASK_IDS:
        try:
            require_colour_evidence(tid, demos, [{"input": q["input"]}])
        except MissingColourEvidence:
            pass
    with pytest.raises(ValueError):
        candidate_predictions("007bbfb7", demos, q["input"])


def test_sole_undefined_answer_is_a_failure():
    """Five constructor demos leave only the modal rule; on a tied-modal query (outside
    the constructor domain) its sole answer is None, which must not be accepted."""
    demos = [scene("27f8ce4f", sum(g, []), 3, 3) for g in (
        [[5, 1, 3], [1, 1, 3], [7, 3, 1]], [[9, 7, 1], [5, 9, 1], [1, 5, 8]],
        [[5, 1, 1], [1, 1, 1], [1, 8, 8]], [[9, 2, 8], [2, 6, 5], [2, 9, 5]],
        [[6, 8, 8], [6, 8, 7], [8, 7, 6]])]
    assert sorted(surviving_candidates(demos)) == [("modal", "id", "id")]
    tied = [[1, 1, 2], [2, 3, 4], [5, 6, 7]]
    assert candidate_predictions("27f8ce4f", demos, tied) == [None]
    with pytest.raises(MissingColourEvidence, match="undefined"):
        require_self_tiler_evidence("27f8ce4f", demos, [{"input": tied}])
    ok = scene("27f8ce4f", [1, 1, 2, 1, 3, 4, 5, 6, 7], 3, 3)
    require_self_tiler_evidence("27f8ce4f", demos, [{"input": ok["input"]}])


def test_sole_none_contract(monkeypatch):
    from arc_agi2 import self_tiler_evidence as gate
    demo = gen("48f8583b", height=3, width=3)
    monkeypatch.setattr(gate, "candidate_predictions", lambda *a, **k: [None])
    with pytest.raises(MissingColourEvidence, match="undefined"):
        gate.require_self_tiler_evidence("48f8583b", [demo], [{"input": demo["input"]}])
    monkeypatch.setattr(gate, "candidate_predictions", lambda *a, **k: [demo["output"]])
    gate.require_self_tiler_evidence("48f8583b", [demo], [{"input": demo["input"]}])
