"""f3cdc58f bar-order demonstration evidence (histogram_order_evidence).

The constructor, factory, pair checker and labels are unchanged; the valid
domain (random W, H 4..30; explicit W 4..30, H 1..30) is not narrowed. The gate
compares three natural readings (fixed legend, ascending count, descending
count; ties by the demonstrated legend) on each query INPUT only.
"""
import hashlib
import importlib
import json
import random

import pytest

from arc_agi2 import histogram_order_evidence as gate
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, grid, reference, verification_solver

TID = "f3cdc58f"
REPORT = BASE / "reports/diversity-v1/f3cdc58f-order-evidence-20261025"
CONSTRUCTOR_SHA = "abd953bb8cd3a8c121ee081492f4c8e8df591b26cd03d3b13d01b875c9934d97"
FACTORY_SHA = "81c2164bbfb8fd3e335c16ef06186c432b50bf3c3e4ad7afb5b939673f3204d9"
PALETTES = (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5], [7, 4, 1, 0, 9, 2, 6, 8, 5, 3])


def mod():
    return importlib.import_module("tasks.task_" + TID)


def pair(counts, height=4, width=4, seed=0):
    """Constructor pair with the given counts of colours 1..4 (label from generate)."""
    cells = [c for c, n in zip((1, 2, 3, 4), counts) for _ in range(n)]
    cells += [0] * (height * width - len(cells))
    random.Random(seed).shuffle(cells)
    p = mod().generate(colors=cells, width=width, height=height)
    assert grid(verification_solver(TID)(p["input"])) == grid(p["output"])
    return p


def record(pairs, d4, palette):
    ep = episode(pairs, d4, palette)
    ep.update(task_id=TID, episode_id=f"test-{d4}", d4_transform=d4, color_permutation=palette)
    return make_record(ep)


def accepted_everywhere(pairs):
    """make_record verdict over 8 D4 x 3 palettes; must not depend on the frame."""
    verdicts = set()
    for palette in PALETTES:
        for d4 in range(8):
            try:
                record(pairs, d4, palette)
                verdicts.add(True)
            except MissingColourEvidence:
                verdicts.add(False)
    assert len(verdicts) == 1, "verdict depends on D4/palette"
    return verdicts.pop()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_constructor_factory_and_checker_unchanged():
    assert sha(BASE.parent / "tasks" / f"task_{TID}.py") == CONSTRUCTOR_SHA
    assert sha(BASE / "direct_factories" / f"task_{TID}.py") == FACTORY_SHA
    cert = json.loads((BASE / "direct_factories" / f"{TID}.json").read_text())
    assert (cert["constructor_sha256"], cert["factory_sha256"]) == (CONSTRUCTOR_SHA, FACTORY_SHA)
    from arc_agi2.verified_rules import VERIFIERS, fixed_colour_histogram
    assert VERIFIERS[TID] is fixed_colour_histogram


def test_valid_domain_not_narrowed():
    m = mod()
    for h in (1, 2, 3, 4):
        p = m.generate(colors=[1, 2, 3, 4] + [0] * (4 * h - 4), width=4, height=h)
        assert len(p["input"]) == h
    random.seed(5)
    heights = set()
    for _ in range(300):
        heights.add(len(m.generate()["input"]))
    assert min(heights) == 4 and max(heights) <= 30
    with pytest.raises(ValueError):
        m.generate(colors=[1, 1, 1, 2, 3, 4, 0, 0], width=4, height=2)  # count 3 > H


@pytest.mark.parametrize("key", ["canonical", "teaching_fixture"])
def test_fixtures_accepted_8d4_palettes(key):
    task = reference(TID)[key]
    pairs = task["train"] + [task["test"][0]]
    assert gate.surviving_rules(task["train"]) == {"fixed_legend"}
    assert accepted_everywhere(pairs)


def test_pregate_witnesses_now_rejected():
    data = json.loads((REPORT / "pregate-witness.json").read_text())
    assert set(data["witnesses"]) == {"ascending_count", "descending_count"}
    for rule, w in data["witnesses"].items():
        demos = w["demonstrations"]
        query = {"input": w["query"]["input"], "output": w["query"]["native_answer"]}
        pairs = [{"input": d["input"], "output": d["output"]} for d in demos] + [query]
        assert len({input_orbit(p["input"]) for p in pairs}) == 4
        for p in pairs:
            assert grid(verification_solver(TID)(p["input"])) == grid(p["output"])
        assert gate.surviving_rules(demos) == {"fixed_legend", rule}
        answers = gate.candidate_predictions(demos, query["input"])
        assert len(answers) == 2 and query["output"] in answers
        assert w["query"]["competitor_answer"] in answers
        assert len(w["pregate_make_record_accepted"]) == 16
        for palette in (list(range(10)), w["seeded_palette"]):
            for d4 in range(8):
                with pytest.raises(MissingColourEvidence, match="bar order ambiguous"):
                    record(pairs, d4, palette)


def test_informative_demos_accept_any_query():
    # Each demo refutes both count orders: counts are not monotone in legend order.
    demos = [pair((2, 1, 3, 2), seed=1), pair((3, 1, 2, 1), seed=2), pair((1, 3, 1, 2), seed=3)]
    assert gate.surviving_rules(demos) == {"fixed_legend"}
    for q, counts in enumerate(((3, 2, 1, 3), (1, 2, 3, 3), (2, 2, 2, 2))):
        assert accepted_everywhere(demos + [pair(counts, seed=10 + q)])


def test_query_specific_verdict_with_monotone_demos():
    demos = [pair((1, 2, 2, 3), seed=1), pair((1, 1, 2, 3), seed=2), pair((2, 2, 3, 3), seed=3)]
    assert gate.surviving_rules(demos) == {"fixed_legend", "ascending_count"}
    assert accepted_everywhere(demos + [pair((2, 2, 2, 2), seed=4)])   # all tied
    assert accepted_everywhere(demos + [pair((1, 1, 3, 3), seed=5)])   # also non-decreasing
    assert not accepted_everywhere(demos + [pair((3, 1, 2, 2), seed=6)])


def test_all_tied_demos_need_all_tied_query():
    demos = [pair((2, 2, 2, 2), seed=s) for s in (1, 2, 3)]
    assert gate.surviving_rules(demos) == set(gate.RULES)
    assert accepted_everywhere(demos + [pair((3, 3, 3, 3), seed=4)])
    assert not accepted_everywhere(demos + [pair((1, 2, 2, 3), seed=5)])
    assert not accepted_everywhere(demos + [pair((3, 2, 2, 1), seed=6)])


@pytest.mark.parametrize("height", [1, 2, 3])
def test_explicit_small_heights_kept(height):
    # H = 1: every count is 1, all readings agree, nothing to reject.
    if height == 1:
        demos = [pair((1, 1, 1, 1), 1, 4 + s, seed=s) for s in range(3)]
        assert accepted_everywhere(demos + [pair((1, 1, 1, 1), 1, 7, seed=9)])
        return
    top = height
    informative = [pair((top, 1, top, 1), height, 5, seed=1), pair((1, top, 1, 1), height, 5, seed=2),
                   pair((top, 1, 1, top), height, 6, seed=3)]
    query = pair((top, 1, 1, 1), height, 5, seed=4)
    assert accepted_everywhere(informative + [query])
    monotone = [pair((1, 1, top, top), height, 5, seed=5), pair((1, top, top, top), height, 5, seed=6),
                pair((1, 1, 1, top), height, 6, seed=7)]
    assert not accepted_everywhere(monotone + [query])


def test_dense_and_full_colour_cases():
    full = pair((4, 4, 4, 4), 4, 4, seed=1)             # no background cell at all
    assert {v for row in full["input"] for v in row} == {1, 2, 3, 4}
    demos = [pair((4, 1, 3, 2), 4, 4, seed=2), pair((2, 4, 1, 3), 4, 4, seed=3), full]
    assert accepted_everywhere(demos + [pair((4, 4, 4, 3), 4, 4, seed=4)])
    tall = [pair((30, 7, 30, 1), 30, 30, seed=5), pair((12, 30, 3, 9), 30, 4, seed=6),
            pair((30, 30, 30, 30), 30, 4, seed=7)]
    assert accepted_everywhere(tall + [pair((1, 30, 2, 29), 30, 30, seed=8)])


class AnswerFreeQuery(dict):
    def __getitem__(self, key):
        if key != "input":
            raise AssertionError("query answer read: " + key)
        return dict.__getitem__(self, key)

    def get(self, key, default=None):
        if key != "input":
            raise AssertionError("query answer read: " + key)
        return dict.get(self, key, default)


def test_query_answers_unused():
    demos = [pair((1, 2, 2, 3), seed=1), pair((1, 1, 2, 3), seed=2), pair((2, 2, 3, 3), seed=3)]
    ok, bad = pair((2, 2, 2, 2), seed=4), pair((3, 1, 2, 2), seed=6)
    require_colour_evidence(TID, demos, [AnswerFreeQuery(input=ok["input"])])
    with pytest.raises(MissingColourEvidence):
        require_colour_evidence(TID, demos, [AnswerFreeQuery(input=bad["input"])])
    # Swapping in a wrong answer changes nothing: the verdict depends on inputs only.
    require_colour_evidence(TID, demos, [{"input": ok["input"], "output": bad["output"]}])


def test_sampled_4x4_contexts_frame_invariant_and_sound():
    m = mod()
    rng = random.Random(7)
    seen = {True: 0, False: 0}
    for _ in range(60):
        pairs = []
        for _ in range(4):
            random.seed(rng.getrandbits(48))
            pairs.append(m.generate(width=4, height=4))
        verdict = accepted_everywhere(pairs)
        seen[verdict] += 1
        if verdict:
            for palette in PALETTES[:2]:
                for d4 in (0, 3, 5):
                    ep = episode(pairs, d4, palette)
                    assert gate.candidate_predictions(ep["train"], ep["test"][0]["input"],
                                                      palette, d4) == [ep["solutions"][0]]
    assert seen[True] > seen[False] > 0   # 4x4 kept; ambiguity is rejected per query


def test_matches_independent_witness_competitor():
    import importlib.util
    spec = importlib.util.spec_from_file_location("witness", REPORT / "witness.py")
    witness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(witness)
    m = mod()
    random.seed(11)
    for _ in range(200):
        p = m.generate(width=random.randint(4, 8), height=random.randint(4, 6))
        options = gate.variants(p["input"], (1, 2, 3, 4))
        for rule in ("ascending_count", "descending_count"):
            assert [list(r) for r in options[rule]] == witness.render(p["input"], rule)
        assert [list(r) for r in options["fixed_legend"]] == p["output"]


def test_out_of_domain_inputs_raise_missing_evidence():
    demos = [pair((1, 2, 3, 4), seed=s) for s in (1, 2, 3)]
    for bad in ([[1, 2, 3]], [[1, 2, 3, 0]], [[1, 2, 3, 5]], [[1, 1, 2, 3], [4, 0, 0, 0]]):
        with pytest.raises(MissingColourEvidence):
            require_colour_evidence(TID, demos, [{"input": bad}])
