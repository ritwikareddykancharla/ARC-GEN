"""Regression checks for the fourth batch of reviewed RE-ARC colour roles.

All six use background alignment only; their saved direct programs are unchanged.
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

BATCH4 = ("7b6016b9", "8eb1be9a", "97999447", "ba97ae07", "d4a91cb9", "f35d900a")
ROOT = Path(__file__).parent
CERTS = ROOT.parent / "reports/diversity-v1/role-certificates"


def test_batch_specs_are_background_only():
    for tid in BATCH4:
        assert set(ROLE_SPECS[tid]) <= {"fixed", "input_colours"}, tid


@pytest.mark.parametrize("tid", BATCH4)
def test_native_fixtures_are_role_fixed_points(tid):
    ref = reference(tid)["canonical"]
    for pair in ref["train"] + ref["test"]:
        aligned, palette = align_pair(tid, {k: pair[k] for k in ("input", "output")})
        assert palette == list(range(10))
        assert aligned["input"] == pair["input"] and aligned["output"] == pair["output"]


@pytest.mark.parametrize("tid", BATCH4)
def test_fresh_aligned_episodes_under_all_d4(tid):
    pairs, seed = [], 0
    while len(pairs) < 8:
        random.seed(40_000 + seed)
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


def test_fixed_output_colours_cannot_be_background():
    # 7b6016b9 paints enclosed background red and open background green.
    for colour in (2, 3):
        g = [[colour] * 6 for _ in range(6)]
        g[2][1] = g[2][2] = g[2][3] = 7
        with pytest.raises(ValueError, match="output marker"):
            align_pair("7b6016b9", {"input": g, "output": g})


def test_path_family_rejects_missing_endpoint():
    # d4a91cb9 needs background, the cyan start and the red end: three colours.
    g = [[6] * 6 for _ in range(6)]
    g[1][1] = 8
    with pytest.raises(ValueError, match="number of input colours"):
        align_pair("d4a91cb9", {"input": g, "output": g})


def test_background_swap_keeps_endpoint_and_path_colours():
    # d4a91cb9 on a black-free palette: background 6 becomes 0; 2, 4 and 8 stay put.
    g = [[6] * 6 for _ in range(6)]
    g[1][1], g[4][3] = 8, 2
    out = [row[:] for row in g]
    for r in (2, 3, 4):
        out[r][1] = 4
    out[4][2] = 4
    aligned, palette = align_pair("d4a91cb9", {"input": g, "output": out})
    assert (palette[6], palette[0], palette[2], palette[4], palette[8]) == (0, 6, 2, 4, 8)
    assert aligned["output"][4][1] == 4 and aligned["input"][0][0] == 0
    assert grid(call(verification_solver("d4a91cb9"), aligned["input"])) == aligned["output"]


@pytest.mark.parametrize("tid", BATCH4)
def test_certificate_matches_current_sources(tid):
    cert = json.loads((CERTS / (tid + ".json")).read_text())
    assert cert["passed"] and cert["admission_gate_passed"]
    assert cert["augmented_episode_checks"] >= 2048 and cert["accepted_pairs"] >= 1024
    assert cert["requested_proposals"] >= 1152
    assert cert["fixture_variants_checked"] == 16
    assert cert["role_spec"] == json.loads(json.dumps(ROLE_SPECS[tid]))
    for name, digest in cert["dependency_sha256"].items():
        assert digest == hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest(), name
    text, _ = compile_target(tid)
    assert cert["program_sha256"] == hashlib.sha256(text.encode()).hexdigest()
