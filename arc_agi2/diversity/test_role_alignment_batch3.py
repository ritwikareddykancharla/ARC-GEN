"""Regression checks for the third batch of reviewed RE-ARC colour roles.

All ten use background alignment only; their saved direct programs are unchanged.
"""

import hashlib
import json
import random
from pathlib import Path

import pytest

from arc_agi2.diversity.colour_roles import ROLE_SPECS, align_pair
from arc_agi2.diversity.rearc import generators, utils, verifiers
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import audit_target, compile_target, verify
from arc_agi2.runtime import call, grid, reference, verification_solver

BATCH3 = ("834ec97d", "a5313dff", "a5f85a15", "a79310a0", "aba27056",
          "ae4f1146", "cdecee7f", "d06dbe63", "d5d6de2d", "fcc82909")
ROOT = Path(__file__).parent
CERTS = ROOT.parent / "reports/diversity-v1/role-certificates"


def test_batch_specs_are_background_only():
    for tid in BATCH3:
        assert set(ROLE_SPECS[tid]) <= {"fixed", "input_colours"}, tid


@pytest.mark.parametrize("tid", BATCH3)
def test_native_fixtures_are_role_fixed_points(tid):
    ref = reference(tid)["canonical"]
    for pair in ref["train"] + ref["test"]:
        aligned, palette = align_pair(tid, {k: pair[k] for k in ("input", "output")})
        assert palette == list(range(10))
        assert aligned["input"] == pair["input"] and aligned["output"] == pair["output"]


@pytest.mark.parametrize("tid", BATCH3)
def test_fresh_aligned_episodes_under_all_d4(tid):
    pairs, seed = [], 0
    while len(pairs) < 8:
        random.seed(20_000 + seed)
        utils.rng.clear()
        seed += 1
        raw = {k: grid(v) for k, v in
               call(getattr(generators, "generate_" + tid), 0., 1., seconds=2).items()}
        if grid(call(getattr(verifiers, "verify_" + tid),
                     tuple(map(tuple, raw["input"])))) != raw["output"]:
            continue
        try:
            aligned, palette = align_pair(tid, raw)
        except ValueError:
            continue
        assert all(palette[c] == c for c in ROLE_SPECS[tid].get("fixed", ()))
        assert grid(call(verification_solver(tid), aligned["input"])) == aligned["output"]
        pairs.append(aligned)
    assert seed < 40, "unexpectedly high rejection rate"
    palette = list(range(10))
    random.Random(tid).shuffle(palette)
    for offset in (0, 4):
        for d4 in range(8):
            text, _ = compile_target(tid, d4, palette)
            audit_target(tid, text)
            verify(text, episode(pairs[offset:offset + 4], d4, palette))


def test_fixed_output_colour_cannot_be_background():
    # a5313dff fills enclosed regions with blue (1); a blue background is rejected.
    g = [[1] * 5 for _ in range(5)]
    g[1][1] = g[1][2] = 7
    with pytest.raises(ValueError, match="output marker"):
        align_pair("a5313dff", {"input": g, "output": g})


def test_single_pixel_family_rejects_extra_colours():
    # 834ec97d moves exactly one pixel; a second foreground colour is out of domain.
    g = [[6] * 5 for _ in range(5)]
    g[1][1], g[3][3] = 2, 9
    with pytest.raises(ValueError, match="number of input colours"):
        align_pair("834ec97d", {"input": g, "output": g})


def test_background_swap_keeps_marker_and_dot_colours():
    # d06dbe63: a black dot on a cyan background. Cyan becomes 0, black takes cyan,
    # and the grey staircase colour 5 is untouched.
    g = [[8] * 6 for _ in range(6)]
    g[3][2] = 0
    out = [row[:] for row in g]
    out[2][2] = out[1][2] = out[1][3] = out[1][4] = 5
    aligned, palette = align_pair("d06dbe63", {"input": g, "output": out})
    assert (palette[8], palette[0], palette[5]) == (0, 8, 5)
    assert aligned["input"][3][2] == 8 and aligned["output"][1][3] == 5


@pytest.mark.parametrize("tid", BATCH3)
def test_certificate_matches_current_sources(tid):
    cert = json.loads((CERTS / (tid + ".json")).read_text())
    assert cert["passed"] and cert["admission_gate_passed"]
    assert cert["augmented_episode_checks"] >= 2048 and cert["accepted_pairs"] >= 1024
    assert cert["fixture_variants_checked"] == 16
    assert cert["role_spec"] == json.loads(json.dumps(ROLE_SPECS[tid]))
    for name, digest in cert["dependency_sha256"].items():
        assert digest == hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest(), name
    text, _ = compile_target(tid)
    assert cert["program_sha256"] == hashlib.sha256(text.encode()).hexdigest()
