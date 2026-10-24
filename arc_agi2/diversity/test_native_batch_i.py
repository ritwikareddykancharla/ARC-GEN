"""Native batch I: 18447a8d (key/lock bands) and b4a43f3b (motif stamp) domain expansion.

Rules, colour roles, canonical fixtures and the direct factories are unchanged.
- 18447a8d: random band count 2..7 (num_bands), sampled without rejection.
- b4a43f3b: free non-empty maps, motif scale 1..3, map height 1..10, and
  enumerated motif masks.
Complete explicit legacy argument paths keep their old labels.
"""
import hashlib
import json
import random
import time
from pathlib import Path

import pytest

from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import verify
from arc_agi2.runtime import BASE, call, grid, reference, verification_solver
from arc_agi2.direct_factories import task_18447a8d as factory_k, task_b4a43f3b as factory_b
from tasks import task_18447a8d as keys, task_b4a43f3b as stamp

REPORT = BASE / "reports/diversity-v1/native-batch-i"
PALETTE = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
FACTORY = {"18447a8d": factory_k, "b4a43f3b": factory_b}
MODULE = {"18447a8d": keys, "b4a43f3b": stamp}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def certify(tid, pairs):
    check = verification_solver(tid)
    for p in pairs:
        assert grid(check(p["input"])) == p["output"]
    for pal in (list(range(10)), PALETTE):
        for d4 in range(8):
            verify(FACTORY[tid].build_program(d4, pal), episode(pairs, d4, pal))


def draws(module, n=150, **kw):
    out = []
    for i in range(n):
        random.seed(hashlib.sha256(f"batch-i-test:{module.__name__}:{i}:{kw}".encode()).digest()[:8])
        out.append(call(module.generate, seconds=3, **kw))
    return out


@pytest.mark.parametrize("tid", sorted(MODULE))
def test_fixture_replay(tid):
    fx = reference(tid)["canonical"]
    replay = MODULE[tid].validate()
    for split in ("train", "test"):
        assert sorted(map(json.dumps, replay[split])) == sorted(map(json.dumps, fx[split]))


@pytest.mark.parametrize("tid", sorted(MODULE))
def test_no_unbounded_loops_in_constructor(tid):
    source = Path(MODULE[tid].__file__).read_text()
    assert "while True" not in source and "diagonally_connected_sprite(" not in source


# ------------------------------------------------------------------ 18447a8d
def test_18447a8d_random_domain():
    counts = set()
    for p in draws(keys, 240):
        g, o = p["input"], p["output"]
        n = (len(g) - 1) // 4
        assert 2 <= n <= 7 and len(g) == 4 * n + 1 and all(len(r) == 11 for r in g)
        counts.add(n)
        colours = [g[4 * b + 1][10] for b in range(n)]
        assert len(set(colours)) == n and not set(colours) & {0, 7, 8}
        for b in range(n):
            assert all(g[4 * b][c] == 7 for c in range(11))
            for r in range(4 * b + 1, 4 * b + 4):
                assert 1 <= g[r].count(8) <= 4 and o[r][:5].count(7) == 0 and o[r][5:] == [7] * 6
    assert counts == set(range(2, 8))


def test_18447a8d_canonical_two_band_shape_is_now_random_reachable():
    two = [p for p in draws(keys, 60) if len(p["input"]) == 9]
    assert two, "2-band scenes (canonical train[1]) must be in the random domain"
    for p in draws(keys, 20, num_bands=2):
        assert len(p["input"]) == 9


def test_18447a8d_explicit_arguments():
    p = keys.generate(colors=[9, 4, 1], num_bands=3)
    assert len(p["input"]) == 13 and [p["input"][4 * b + 1][10] for b in range(3)] == [9, 4, 1]
    with pytest.raises(ValueError):
        keys.generate(num_bands=8)
    for bad in ({"num_bands": True}, {"num_bands": 3.0}, {"num_bands": 1}, {"colors": [1, 1]},
                {"colors": [7, 1]}, {"colors": [1, 2], "num_bands": 3},
                {"lefts": [1, 2, 3, 4, 1, 2]}, {"rights": [1, 2, 3, 4, 1, 2]},
                {"lefts": [1] * 6, "rights": [4] * 6}):
        with pytest.raises(ValueError):
            keys.generate(**bad)


def test_18447a8d_legacy_complete_explicit_labels_kept():
    # repeated key colours, colour 0, a single band and zero bands were all drawable before.
    p = keys.generate(lefts=[1, 2, 3, 4, 3, 2], rights=[1, 2, 3, 4, 3, 2], colors=[3, 3])
    assert p["output"][1][:5] == [8, 3, 3, 3, 3]
    assert keys.generate(lefts=[1, 1, 1], rights=[4, 4, 4], colors=[0])["output"][2][:5] == [8, 0, 0, 0, 0]
    assert keys.generate(lefts=[], rights=[], colors=[]) == {"input": [[7] * 11], "output": [[7] * 11]}
    with pytest.raises(ValueError):                       # old code returned None grids
        keys.generate(lefts=[1, 1, 1, 1, 1, 1], rights=[4, 4, 4, 4, 4, 4], colors=[1, 2])
    with pytest.raises(ValueError):                       # old code crashed
        keys.generate(lefts=[12, 1, 1], rights=[4, 4, 4], colors=[1])
    with pytest.raises(ValueError):                       # 33 rows: outside ARC bounds
        keys.generate(lefts=[1] * 24, rights=[4] * 24, colors=[1] * 8)


@pytest.mark.parametrize("n", [2, 7])
def test_18447a8d_boundary_band_counts_checker_and_factory(n):
    for i in range(3):
        random.seed(900 + 10 * n + i)
        certify("18447a8d", [keys.generate(num_bands=n) for _ in range(4)])


# ------------------------------------------------------------------ b4a43f3b
def test_b4_random_domain():
    seen_scales, seen_heights = set(), set()
    for p in draws(stamp, 240):
        g, o = p["input"], p["output"]
        w = len(g[0])
        s, h = w // 3, len(g) - w - 1
        assert w in (3, 6, 9) and 1 <= h <= 10 and g[w] == [5] * w
        assert (len(o), len(o[0])) == (3 * h, 3 * w)
        motif = [[g[s * r][s * c] for c in range(3)] for r in range(3)]
        cells = [(r, c) for r in range(3) for c in range(3) if motif[r][c]]
        assert sorted(cells) in [sorted(m) for m in stamp.MOTIF_MASKS]
        assert {motif[r][c] for r, c in cells} <= {1, 2, 3, 6}
        assert any(v for r in g[w + 1:] for v in r) and {v for r in g[w + 1:] for v in r} <= {0, 2}
        seen_scales.add(s)
        seen_heights.add(h)
    assert seen_scales == {1, 2, 3} and seen_heights == set(range(1, 11))


def test_b4_motif_masks_are_spanning_and_8_connected():
    assert {len(m) for m in stamp.MOTIF_MASKS} == set(range(3, 10))
    for m in stamp.MOTIF_MASKS:
        assert {r for r, _ in m} == {0, 1, 2} == {c for _, c in m}


def test_b4_explicit_arguments():
    p = stamp.generate(colors="111202030", pattern="020222020000", scale=1)
    assert len(p["input"]) == 8 and p["input"][0] == [1, 1, 1]       # full scale-1 row kept
    assert len(stamp.generate(colors="101020320")["input"]) == 13     # legacy canvas
    q = stamp.generate(pattern="2" * 12, scale=2)                      # pattern kept, motif drawn
    assert len(q["input"]) == 6 + 1 + 2
    for bad in ({"scale": 4}, {"scale": True}, {"map_height": 11}, {"map_height": 2.0},
                {"pattern": "2" * 13, "scale": 2}, {"pattern": "2" * 12, "map_height": 3},
                {"colors": "12345678", "pattern": "2" * 6, "scale": 2}):
        with pytest.raises(ValueError):
            stamp.generate(**bad)


def test_b4_legacy_complete_explicit_labels_kept():
    five = stamp.generate(colors="555010101", pattern="2" + "0" * 35)
    assert five["output"][0][:3] == [5, 5, 5]
    assert stamp.generate(colors="000000000", pattern="2" * 36)["output"] == [[0] * 18] * 18
    assert stamp.generate(colors="136010221", pattern="0" * 36)["output"] == [[0] * 18] * 18
    digits = stamp.generate(colors="101020320", pattern="9" + "0" * 35)
    assert digits["input"][7][0] == 2
    with pytest.raises(ValueError):                       # old code crashed
        stamp.generate(colors="1010", pattern="2" * 36)


@pytest.mark.parametrize("scale,height", [(1, 1), (1, 10), (3, 1), (3, 10), (2, 6)])
def test_b4_boundary_shapes_checker_and_factory(scale, height):
    for i in range(2):
        random.seed(700 + 31 * scale + height + i)
        certify("b4a43f3b", [stamp.generate(scale=scale, map_height=height) for _ in range(4)])


@pytest.mark.parametrize("tid", sorted(MODULE))
def test_default_draws_are_fast(tid):
    started = time.monotonic()
    for i in range(300):
        random.seed(i)
        MODULE[tid].generate()
    assert time.monotonic() - started < 5


# ------------------------------------------------------------------ evidence binding
@pytest.mark.parametrize("tid", sorted(MODULE))
def test_certificates_bound_to_current_sources(tid):
    constructor = sha(MODULE[tid].__file__)
    for path in (BASE / "direct_factories" / f"{tid}.json",
                 BASE / "reports/diversity-v1/native-certificates" / f"{tid}.json"):
        cert = json.loads(path.read_text())
        assert cert["passed"] and cert["constructor_sha256"] == constructor
        assert cert["fresh_pairs_checked"] == 1000 and cert["augmented_pair_checks"] == 8000
        assert cert["fixture_variants_checked"] == 16 and cert["sampler_rejections"] == []
        assert cert["factory_sha256"] == sha(BASE / "direct_factories" / f"task_{tid}.py")
    record = json.loads((BASE / "direct_factories" / f"{tid}.json").read_text())
    assert record["previous_constructor_sha256"] != constructor
    assert record["provenance"] and record["draft_notes"] and record["previous_domain_limitations"]


def test_context_audit_bound_to_current_sources():
    audit = json.loads((REPORT / "context-audit.json").read_text())
    assert set(audit) == {"18447a8d", "18447a8d@min_corner", "b4a43f3b", "b4a43f3b@min_corner"}
    for key, run in audit.items():
        assert run["passed"] and run["queries_accepted"] == run["queries_requested"] == 250
        assert run["make_record_calls"] == 2000 and not run["queries_failed"]
        files = {"constructor": BASE.parent / "tasks" / f"task_{run['task_id']}.py",
                 "native_i_evidence": BASE / "native_i_evidence.py",
                 "colour_evidence": BASE / "colour_evidence.py",
                 "verified_rules": BASE / "verified_rules.py",
                 "factory_certificate": BASE / "direct_factories" / f"{run['task_id']}.json",
                 "harness": REPORT / "context_audit.py"}
        for name, path in files.items():
            assert run["source_sha256"][name] == sha(path), (key, name)


def test_legacy_equivalence_report_bound_to_current_constructors():
    for r in json.loads((REPORT / "legacy-equivalence.json").read_text()):
        assert r["passed"] and not r["mismatches"]
        assert r["new_constructor_sha256"] == sha(MODULE[r["task_id"]].__file__)
