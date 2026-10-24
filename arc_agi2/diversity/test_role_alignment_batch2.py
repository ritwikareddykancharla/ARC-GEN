"""Regression checks for the second batch of reviewed RE-ARC colour roles."""

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

BATCH2 = ("0a938d79", "0ca9ddb6", "1caeab9d", "25ff71a9", "31aa019c", "3aa6fb7a",
          "4258a5f9", "4347f46a", "46f33fce", "50cb2852", "56dc2b01", "60b61512",
          "6d75e8bb", "6e82a1ae", "7468f01a")
ROOT = Path(__file__).parent
CERTS = ROOT.parent / "reports/diversity-v1/role-certificates"


@pytest.mark.parametrize("tid", BATCH2)
def test_native_fixtures_are_role_fixed_points(tid):
    """The declared roles agree with the native constructor's own colours."""
    ref = reference(tid)["canonical"]
    for pair in ref["train"] + ref["test"]:
        aligned, palette = align_pair(tid, {k: pair[k] for k in ("input", "output")})
        assert palette == list(range(10))
        assert aligned["input"] == pair["input"] and aligned["output"] == pair["output"]


@pytest.mark.parametrize("tid", BATCH2)
def test_fresh_aligned_episodes_under_all_d4(tid):
    """Constructor labels survive alignment and both verifiers and the direct program."""
    pairs, seed = [], 0
    while len(pairs) < 8:
        random.seed(10_000 + seed)
        utils.rng.clear()
        seed += 1
        raw = {k: grid(v) for k, v in
               call(getattr(generators, "generate_" + tid), 0., 1., seconds=2).items()}
        assert grid(call(getattr(verifiers, "verify_" + tid),
                         tuple(map(tuple, raw["input"])))) == raw["output"]
        try:
            aligned, _ = align_pair(tid, raw)
        except ValueError:
            continue
        assert grid(call(verification_solver(tid), aligned["input"])) == aligned["output"]
        pairs.append(aligned)
    assert seed < 40, "unexpectedly high alignment rejection rate"
    palette = list(range(10))
    random.Random(tid).shuffle(palette)
    for offset in (0, 4):
        for d4 in range(8):
            text, _ = compile_target(tid, d4, palette)
            audit_target(tid, text)
            verify(text, episode(pairs[offset:offset + 4], d4, palette))


def test_ring_colour_background_is_rejected():
    # 31aa019c draws a fixed red (2) ring; a red background would hide it.
    g = [[2] * 5 for _ in range(5)]
    g[2][2], g[0][0], g[0][1] = 6, 4, 4
    with pytest.raises(ValueError, match="output marker"):
        align_pair("31aa019c", {"input": g, "output": g})


def test_modal_tie_is_rejected():
    g = [[5, 5, 5], [9, 9, 9]]
    with pytest.raises(ValueError, match="unique modal"):
        align_pair("3aa6fb7a", {"input": g, "output": g})


def test_foreground_needs_exactly_one_free_colour():
    # 56dc2b01: background, red bar (2) and one shape colour; a cyan (8) shape
    # would collide with the fixed marker colour and is rejected.
    g = [[6, 6, 6, 6, 6, 6], [6, 2, 6, 8, 8, 6], [6, 2, 6, 6, 6, 6], [6, 2, 6, 6, 6, 6]]
    with pytest.raises(ValueError):
        align_pair("56dc2b01", {"input": g, "output": g})
    g = [[6, 6, 6, 6, 6, 6], [6, 2, 6, 4, 4, 6], [6, 2, 6, 6, 6, 6], [6, 2, 6, 6, 6, 6]]
    aligned, palette = align_pair("56dc2b01", {"input": g, "output": g})
    assert (palette[6], palette[4], palette[2], palette[8]) == (0, 3, 2, 8)
    assert sorted(palette) == list(range(10))


def test_fixed_seed_legend_is_untouched():
    # 0ca9ddb6 keeps its 1/2/6/8 seeds and 4/7 stamps; only background moves.
    g = [[3] * 6 for _ in range(6)]
    g[2][2], g[4][4] = 1, 2
    out = [row[:] for row in g]
    _, palette = align_pair("0ca9ddb6", {"input": g, "output": out})
    assert palette[3] == 0 and palette[0] == 3
    assert all(palette[c] == c for c in (1, 2, 4, 6, 7, 8))


@pytest.mark.parametrize("tid", BATCH2)
def test_certificate_matches_current_sources(tid):
    cert = json.loads((CERTS / (tid + ".json")).read_text())
    assert cert["passed"] and cert["admission_gate_passed"]
    assert cert["augmented_episode_checks"] >= 2048 and cert["accepted_pairs"] >= 1024
    assert cert["role_spec"] == json.loads(json.dumps(ROLE_SPECS[tid]))
    for name, digest in cert["dependency_sha256"].items():
        assert digest == hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest(), name
    text, _ = compile_target(tid)
    assert cert["program_sha256"] == hashlib.sha256(text.encode()).hexdigest()
