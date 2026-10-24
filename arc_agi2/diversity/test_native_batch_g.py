"""Native batch G: placement/canvas expansion (8ba14f53), blank counts (4cd1b7b2).

* 8ba14f53  hole tally of two boxes, left box first, into a 3x3 grid.
  Canvas H 3..30 x W 6..30 (legacy 4x9), free margins, gap, vertical offsets
  and hole rectangles up to the output capacity. Two boxes in disjoint column
  ranges are kept.
* 4cd1b7b2  4x4 Latin-square hole filling; 1..7 blanks (legacy 5..6), all
  carved from complete lines so that line propagation completes uniquely.

Rules, colour roles, factories and canonical labels are unchanged. Both
families gain demonstration-evidence gates. Even the legacy samplers leave
the query ambiguous under named competing rules in many three-demonstration
contexts (batch-g-evidence.json).
"""
import hashlib
import importlib
import json
import random

import pytest

from arc_agi2 import hole_tally_8ba14f53_evidence as tally
from arc_agi2 import latin_fill_4cd1b7b2_evidence as latin
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import compile_target, make_record, verify
from arc_agi2.runtime import BASE, call, grid, reference, verification_solver

FAMILIES = ("8ba14f53", "4cd1b7b2")
GATES = {"8ba14f53": tally, "4cd1b7b2": latin}
GATE_FILES = {"8ba14f53": "hole_tally_8ba14f53_evidence.py",
              "4cd1b7b2": "latin_fill_4cd1b7b2_evidence.py"}
PALETTES = (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5])
REPORT = BASE / "reports/diversity-v1/native-batch-g"
LEGACY_SHA = {"8ba14f53": "4f1cca95b331ef528f60627fc1cbe6be1307a4f02cee7fb678976c8660e9ca7b",
              "4cd1b7b2": "30bf33e553a02c15ef38065146c5f8688946a435e58b63760246d5cdad5a6c2c"}
FACTORY_SHA = {"8ba14f53": "82f82e9e9cf41326b16f2816bbe56e58a09e4545c2de8fd89d0edde8b8fac404",
               "4cd1b7b2": "cf5a91352896e1750403ab867f45fd1c9fa3f33fdb482ad760382d7e853dae91"}


def mod(tid):
    return importlib.import_module("tasks.task_" + tid)


def gen(tid, **kw):
    return call(mod(tid).generate, seconds=3, **kw)


def sha_file(rel):
    return hashlib.sha256((BASE / rel).read_bytes()).hexdigest()


def evidence():
    return json.loads((REPORT / "batch-g-evidence.json").read_text())


def gate_verdict(tid, demos, query_input, palette=None, d4=0):
    try:
        require_colour_evidence(tid, demos, [{"input": query_input}], palette, d4)
        return True
    except MissingColourEvidence:
        return False


# ---------------------------------------------------------------- fixtures
@pytest.mark.parametrize("tid", FAMILIES)
def test_canonical_fixtures_replay_exactly(tid):
    fixture = reference(tid)["canonical"]
    replay = mod(tid).validate()
    for split in ("train", "test"):
        assert (sorted(json.dumps(p, sort_keys=True) for p in replay[split])
                == sorted(json.dumps(p, sort_keys=True) for p in fixture[split]))


@pytest.mark.parametrize("tid", FAMILIES)
def test_canonical_episodes_pass_gate_with_unique_label(tid):
    fixture = reference(tid)["canonical"]
    for palette in PALETTES:
        for d4 in range(8):
            ep = episode(fixture["train"] + fixture["test"], d4, palette)
            ep.update(task_id=tid, episode_id="canonical", d4_transform=d4,
                      color_permutation=palette)
            make_record(ep)
            answers = GATES[tid].candidate_predictions(ep["train"], ep["test"][0]["input"], palette)
            assert [[list(r) for r in a] for a in answers] == [ep["solutions"][0]]


# ---------------------------------------------------------- 4cd1b7b2 domain
def is_latin(g):
    return all(sorted(r) == [1, 2, 3, 4] for r in g) and all(
        sorted(r[c] for r in g) == [1, 2, 3, 4] for c in range(4))


@pytest.mark.parametrize("blanks", range(1, 8))
def test_latin_every_blank_count_is_line_solvable(blanks):
    checker = verification_solver("4cd1b7b2")
    random.seed(blanks)
    for _ in range(30):
        p = gen("4cd1b7b2", blanks=blanks)
        assert sum(v == 0 for r in p["input"] for v in r) == blanks
        assert is_latin(p["output"]) and grid(checker(p["input"])) == p["output"]
        assert all(a in (0, b) for ra, rb in zip(p["input"], p["output"]) for a, b in zip(ra, rb))


def test_latin_default_sampler_reaches_one_to_seven():
    random.seed(7)
    seen = {sum(v == 0 for r in gen("4cd1b7b2")["input"] for v in r) for _ in range(400)}
    assert seen == set(range(1, 8))


@pytest.mark.parametrize("kw", [dict(blanks=0), dict(blanks=8), dict(blanks=True),
                                dict(blanks=5.0), dict(colors=[1] * 15),
                                dict(colors=[0] * 16),        # propagation cannot finish
                                dict(colors=[1, 2, 3, 4] * 4, blanks=1)])
def test_latin_rejects_invalid_arguments(kw):
    with pytest.raises(ValueError):
        mod("4cd1b7b2").generate(**kw)


# ---------------------------------------------------------- 8ba14f53 domain
def boxes(g):
    measures, extent = tally.analyse(g, 0)
    return measures["cells"], extent


def test_tally_default_domain_is_broad_and_column_disjoint():
    checker = verification_solver("8ba14f53")
    random.seed(11)
    shapes, heights, widths = set(), set(), set()
    for _ in range(300):
        p = gen("8ba14f53")
        g = p["input"]
        shapes.add((len(g), len(g[0])))
        cells, extent = boxes(g)
        assert len(cells) == 2
        left, right = sorted(extent, key=lambda c: extent[c][2])
        assert extent[left][3] < extent[right][2]            # disjoint column ranges
        assert grid(checker(g)) == p["output"]
        heights.update(e[1] - e[0] + 1 for e in extent.values())
        widths.update(e[3] - e[2] + 1 for e in extent.values())
    assert len(shapes) > 150
    assert {h for h, _ in shapes} >= {3, 30} and {w for _, w in shapes} >= {6, 30}
    assert max(heights) > 4 and max(widths) > 5               # beyond legacy 3..4 x 3..5


@pytest.mark.parametrize("height,width", [(3, 6), (4, 9), (30, 30), (7, 13)])
def test_tally_explicit_canvas_is_respected(height, width):
    random.seed(height * 31 + width)
    for _ in range(20):
        p = gen("8ba14f53", height=height, width=width)
        assert (len(p["input"]), len(p["input"][0])) == (height, width)


@pytest.mark.parametrize("kw", [dict(height=2), dict(width=5), dict(height=31),
                                dict(width=True), dict(colors=[1, 2]),
                                dict(rows=[1], cols=[1], groups=[0], colors=[1, 2]),
                                dict(rows=[1, 1], cols=[1, 3], groups=[0, 1], colors=[1, 2]),
                                dict(rows=[1, 1], cols=[1, 5], groups=[0, 1], colors=[3, 3]),
                                dict(rows=[1, 1], cols=[1, 8], groups=[0, 1], colors=[1, 2]),
                                dict(rows=[1, 1, 1, 1, 2, 2, 2, 2] + [1], cols=[1, 2, 3, 4, 1, 2, 3, 4] + [7],
                                     groups=[0] * 8 + [1], colors=[1, 2], width=10)])
def test_tally_rejects_invalid_arguments(kw):
    with pytest.raises(ValueError):
        mod("8ba14f53").generate(**kw)


def test_tally_explicit_scenes_default_to_legacy_canvas():
    p = gen("8ba14f53", rows=[1, 1], cols=[1, 5], groups=[0, 1], colors=[8, 6])
    assert (len(p["input"]), len(p["input"][0])) == (4, 9)


# ------------------------------------------------------------------- gates
def witnesses(tid):
    return evidence()["families"][tid]["witnesses"]


@pytest.mark.parametrize("tid", FAMILIES)
def test_witnesses_are_ambiguous_and_rejected(tid):
    gate = GATES[tid]
    found = witnesses(tid)
    assert found
    for key, w in found.items():
        if w["competitor_answer"] is None:          # Sudoku: not a gated rule
            continue
        answers = [None if a is None else [list(r) for r in a]
                   for a in gate.candidate_predictions(w["demonstrations"], w["query_input"])]
        assert w["native_answer"] in answers and w["competitor_answer"] in answers, key
        assert not gate_verdict(tid, w["demonstrations"], w["query_input"]), key


@pytest.mark.parametrize("tid", FAMILIES)
def test_witness_queries_are_resolved_by_resampled_context(tid):
    """Same query, new demonstrations: some bounded context certifies the label."""
    checker = verification_solver(tid)
    for key, w in sorted(witnesses(tid).items())[:6]:
        q = w["query_input"]
        kw = {"height": len(q), "width": len(q[0])} if tid == "8ba14f53" else {}
        random.seed(key)
        for _ in range(64):
            demos = [gen(tid, **kw) for _ in range(3)]
            assert all(grid(checker(d["input"])) == d["output"] for d in demos)
            if gate_verdict(tid, demos, q):
                answers = GATES[tid].candidate_predictions(demos, q)
                assert [[list(r) for r in a] for a in answers] == [w["native_answer"]], key
                break
        else:
            pytest.fail(f"{tid} {key}: no context resolved the witness query")


@pytest.mark.parametrize("tid", FAMILIES)
def test_gate_is_d4_invariant_and_ignores_query_answer(tid):
    random.seed(23)
    for n in range(40):
        q = gen(tid)
        kw = {"height": len(q["input"]), "width": len(q["input"][0])} if tid == "8ba14f53" else {}
        pairs = [gen(tid, **kw) for _ in range(3)] + [q]
        verdicts, counts = set(), set()
        for palette in PALETTES:
            for d4 in range(8):
                ep = episode(pairs, d4, palette)
                # A wrong answer next to the query input must not matter.
                bogus = [{"input": ep["test"][0]["input"], "output": [[palette[0]]]}]
                try:
                    require_colour_evidence(tid, ep["train"], bogus, palette, d4)
                    verdicts.add((tuple(palette), True))
                except MissingColourEvidence:
                    verdicts.add((tuple(palette), False))
                counts.add((tuple(palette), len(GATES[tid].surviving_rules(ep["train"], palette))))
        # Colour-index orders (8ba14f53) are palette-dependent by design: whether
        # the demonstrations refute them depends on the visible colours. So both
        # survivors and verdicts are compared across the eight D4 per palette.
        assert len(verdicts) == len(counts) == len(PALETTES), n


def test_tally_gate_rejects_ambiguous_hole_owner():
    g = [[0, 0, 0, 0, 0, 0, 0],
         [0, 1, 1, 2, 2, 2, 0],
         [0, 1, 0, 0, 0, 2, 0],
         [0, 1, 1, 2, 2, 2, 0],
         [0, 0, 0, 0, 0, 0, 0]]
    with pytest.raises(MissingColourEvidence):
        tally.analyse(g, 0)


def test_tally_native_rule_is_in_every_d4_frame():
    """The factory's visible rule is one enumerated rule for every D4 and palette."""
    fixture = reference("8ba14f53")["canonical"]
    pairs = fixture["train"] + fixture["test"]
    for palette in PALETTES:
        for d4 in range(8):
            ep = episode(pairs, d4, palette)
            alive = tally.surviving_rules(ep["train"] + [{"input": ep["test"][0]["input"],
                                                          "output": ep["solutions"][0]}], palette)
            assert alive


def test_latin_gate_requires_demonstrated_colours():
    fixture = reference("4cd1b7b2")["canonical"]
    demos = fixture["train"]
    q = fixture["test"][0]["input"]
    assert gate_verdict("4cd1b7b2", demos, q)
    with pytest.raises(MissingColourEvidence):
        latin.require_latin_fill_evidence(demos, [{"input": [[5 if v == 4 else v for v in r] for r in q]}])
    single = [{"input": [[0, 1], [1, 1]], "output": [[1, 1], [1, 1]]}]
    with pytest.raises(MissingColourEvidence):
        latin.require_latin_fill_evidence(single, [{"input": q}])


def test_latin_sudoku_rule_never_predicts_a_different_grid():
    """Box-valid squares are Latin, so the box rule agrees or has no completion."""
    w = witnesses("4cd1b7b2")["sudoku_no_completion"]
    from importlib import util
    spec = util.spec_from_file_location("bge", REPORT / "batch_g_evidence.py")
    bge = util.module_from_spec(spec)
    spec.loader.exec_module(bge)
    assert all(bge.box_valid(d["output"]) for d in w["demonstrations"])
    assert bge.box_completions(w["query_input"]) == []
    assert not bge.box_valid(w["native_answer"])
    for kind, n in evidence()["families"]["4cd1b7b2"]["ambiguity"]["current"][
            "sudoku_rule_when_all_demo_outputs_box_valid"].items():
        assert kind in ("same", "none") and n > 0


# ------------------------------------------------------- certificates/audit
@pytest.mark.parametrize("tid", FAMILIES)
def test_certificate_is_current(tid):
    record = json.loads((BASE / "direct_factories" / f"{tid}.json").read_text())
    mirror = json.loads((BASE / "reports/diversity-v1/native-certificates" / f"{tid}.json").read_text())
    for cert in (record, mirror):
        assert cert["passed"] and (cert["fresh_pairs_checked"], cert["augmented_pair_checks"],
                                   cert["fixture_variants_checked"]) == (1000, 8000, 16)
        assert cert["constructor_sha256"] == sha_file(f"../tasks/task_{tid}.py")
        assert cert["factory_sha256"] == sha_file(f"direct_factories/task_{tid}.py") == FACTORY_SHA[tid]
        assert cert["auditor_sha256"] == sha_file("diversity/recertify.py")
        assert cert["sampler_rejections"] == []
    assert record["previous_constructor_sha256"] == LEGACY_SHA[tid]
    assert "provenance" in record
    source, _ = compile_target(tid, 3, PALETTES[1])
    random.seed(5)
    pairs = [{k: grid(v) for k, v in gen(tid).items()} for _ in range(4)]
    verify(source, episode(pairs, 3, PALETTES[1]))


@pytest.mark.parametrize("tid", FAMILIES)
def test_context_audit_is_current_and_passed(tid):
    audits = json.loads((REPORT / "context-audit.json").read_text())
    keys = [k for k in audits if k.split("@")[0] == tid]
    assert len(keys) == 3
    for key in keys:
        a = audits[key]
        assert a["passed"] and a["queries_accepted"] == a["queries_requested"] == 250, key
        assert not a["queries_failed"] and a["d4_inconsistent_contexts"] == 0
        assert a["contexts_evaluated"] >= 250 * 8
        for name, rel in (("constructor", f"../tasks/task_{tid}.py"),
                          ("factory", f"direct_factories/task_{tid}.py"),
                          ("factory_certificate", f"direct_factories/{tid}.json"),
                          ("gate", GATE_FILES[tid]),
                          ("colour_evidence", "colour_evidence.py"),
                          ("verified_rules", "verified_rules.py"),
                          ("program_targets", "program_targets.py")):
            assert a["source_sha256"][name] == sha_file(rel), (key, name)


def test_evidence_report_is_current():
    data = evidence()
    for name, rel in (("constructor_8ba14f53", "../tasks/task_8ba14f53.py"),
                      ("constructor_4cd1b7b2", "../tasks/task_4cd1b7b2.py"),
                      ("hole_tally_8ba14f53_evidence", "hole_tally_8ba14f53_evidence.py"),
                      ("latin_fill_4cd1b7b2_evidence", "latin_fill_4cd1b7b2_evidence.py"),
                      ("colour_evidence", "colour_evidence.py")):
        assert data["source_sha256"][name] == sha_file(rel), name
    # The demonstration gap predates the expansion (legacy samplers).
    for tid in FAMILIES:
        assert data["families"][tid]["ambiguity"]["legacy"]["ambiguous_contexts"] > 0
