"""Reviewed b4a43f3b pair checker: geometric colour-5 separator, motif stamp."""
import json
import random

import pytest

from arc_agi2.runtime import BASE, grid, reference, solver, verification_solver
from arc_agi2.verified_rules import VERIFIER_EVIDENCE, VERIFIERS, separated_motif_stamp
from tasks import task_b4a43f3b as m

REPORT = BASE / "reports/diversity-v1/native-batch-i"


def test_registered_with_evidence():
    assert VERIFIERS["b4a43f3b"] is separated_motif_stamp
    assert verification_solver("b4a43f3b") is separated_motif_stamp
    ev = VERIFIER_EVIDENCE["b4a43f3b"]
    assert ev["canonical_data_changed"] is False and ev["archived_reference_changed"] is False
    assert (BASE.parent / ev["counterexample"]).exists()


def test_fixtures_exact():
    ref = reference("b4a43f3b")
    for version in ("canonical", "teaching_fixture"):
        for split in ("train", "test"):
            for p in ref[version][split]:
                assert separated_motif_stamp(p["input"]) == p["output"]


def test_counterexample_full_single_colour_scale1_row_is_content():
    ce = json.loads((REPORT / "b4a43f3b-archived-verifier-counterexample.json").read_text())
    pair = m.generate(**ce["generate_kwargs"])
    assert pair["input"] == ce["input"] and pair["output"] == ce["constructor_output"]
    assert separated_motif_stamp(ce["input"]) == ce["constructor_output"]
    with pytest.raises(ValueError):                       # archived: 0x9 answer
        grid(solver("b4a43f3b")(ce["input"]))


@pytest.mark.parametrize("kw", [
    dict(colors="555010101", pattern="000000002000022220002000000000000000"),   # legacy 5s
    dict(colors="000000000", pattern="000000220000220000002000000200000000"),   # all-0 motif
    dict(colors="136010221", pattern="0" * 36),                                 # empty map
    dict(colors="101020320", pattern="999000" * 6),                             # any digit -> 2
    dict(colors="020333010", pattern="222", scale=1),
    dict(colors="101010101", pattern=("2" + "0" * 8) * 10, scale=3),
])
def test_adversarial_explicit_scenes(kw):
    pair = m.generate(**kw)
    assert separated_motif_stamp(pair["input"]) == pair["output"]


def test_new_default_draws_agree():
    for i in range(200):
        random.seed(5000 + i)
        pair = m.generate()
        assert separated_motif_stamp(pair["input"]) == pair["output"]


@pytest.mark.parametrize("bad", [
    [[0] * 6] * 13,                                        # no separator at row W
    [[0] * 5] * 12,                                        # width not 3s
    [[1] * 6] * 6 + [[5] * 6],                             # no map
    [[1, 2, 0, 0, 0, 0]] * 6 + [[5] * 6] + [[2] * 6],      # top is not a 2x upscale
    [[0] * 3] * 3 + [[5] * 3] + [[2] * 3] * 11,            # map taller than 10
])
def test_out_of_layout_inputs_raise(bad):
    with pytest.raises(ValueError):
        separated_motif_stamp(bad)


def test_evidence_report_bound_to_current_sources():
    import hashlib
    ev = json.loads((REPORT / "verifier-evidence-b4a43f3b.json").read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert ev["passed"]
    assert ev["source_sha256"]["verified_rules"] == sha(BASE / "verified_rules.py")
    assert ev["source_sha256"]["constructor"] == sha(BASE.parent / "tasks/task_b4a43f3b.py")
    assert ev["old_1000"]["reviewed_agree"] == ev["new_1000"]["reviewed_agree"] == 1000
