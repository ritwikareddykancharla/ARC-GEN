"""Native batch c7d4/d47a: c7d4e6ad legend/canvas and d47aa2ff panel/count expansion.

* c7d4e6ad  row-wise legend recolouring. Canvas 3..30 x 3..30, legend height
  2..H at any offset, 2..8 colours, grey box from any column >= 2. Kept:
  column-0 contiguous legend of distinct non-grey runs, one 4-connected grey
  shape whose rows are exactly the legend rows, black modal. No gate: every
  named competitor is refuted by one demonstration or equal on the domain.
* d47aa2ff  moved dots between two equal panels. Panels 3..30 x 3..14,
  1..6 colours, 2..max(2, HW//9) dots, 1..min(colours, dots-1) movers. Kept:
  colours avoid 0/1/2/5, one mover per colour, spacing, no collisions, a kept
  dot, legacy displacement window. Gate: movement-trail readings.

Rules, factories and canonical labels are unchanged.
"""
import hashlib
import importlib
import importlib.util
import json
import random
import subprocess
import types

import pytest

from arc_agi2 import dot_motion_d47aa2ff_evidence as motion
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, grid, reference, verification_solver

FAMILIES = ("c7d4e6ad", "d47aa2ff")
PALETTES = (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5])
REPORT = BASE / "reports/diversity-v1/native-batch-c7d4-d47a"
BASE_COMMIT = "99def42"
LEGACY_SHA = {"c7d4e6ad": "6c88d33d0ea07a8a0287037d101dcca94647f3be73cf0a746ab224908705dc04",
              "d47aa2ff": "fd5d1120f720c045ea6668bc1690ef50c035540e87d23f5e6b0a9bb81fd135ea"}
FACTORY_SHA = {"c7d4e6ad": "e7d7c61c30b96650b766573b16545a3a639303a257a553c3c16a6fdc56e72c7f",
               "d47aa2ff": "5206d6b295169148e5f9308909721afcbfc8daa84b6099af8d51c8387b8e34b0"}


def mod(tid):
    return importlib.import_module("tasks.task_" + tid)


def sha_bytes(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def legacy(tid):
    src = subprocess.run(["git", "show", f"{BASE_COMMIT}:tasks/task_{tid}.py"],
                         capture_output=True, check=True, cwd=BASE.parent).stdout
    assert hashlib.sha256(src).hexdigest() == LEGACY_SHA[tid]
    module = types.ModuleType(f"legacy_{tid}")
    exec(compile(src, f"legacy/task_{tid}.py", "exec"), module.__dict__)
    return module


def competitors():
    spec = importlib.util.spec_from_file_location("batch_c7d4_d47a_competitors",
                                                  REPORT / "competitors.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evidence():
    return json.loads((REPORT / "batch-evidence.json").read_text())


def verdict(tid, demos, query_input, palette=None, d4=0):
    try:
        require_colour_evidence(tid, demos, [{"input": query_input}], palette, d4)
        return True
    except MissingColourEvidence:
        return False


def draws(tid, n, seed, **kw):
    random.seed(seed)
    return [mod(tid).generate(**kw) for _ in range(n)]


# ---------------------------------------------------------------- fixtures
@pytest.mark.parametrize("tid", FAMILIES)
def test_canonical_fixtures_replay_exactly(tid):
    fixture = reference(tid)["canonical"]
    replay = mod(tid).validate()
    for split in ("train", "test"):
        assert (sorted(json.dumps(p, sort_keys=True) for p in replay[split])
                == sorted(json.dumps(p, sort_keys=True) for p in fixture[split]))


@pytest.mark.parametrize("tid", FAMILIES)
def test_canonical_episodes_pass_make_record_in_all_variants(tid):
    fixture = reference(tid)["canonical"]
    for palette in PALETTES:
        for d4 in range(8):
            ep = episode(fixture["train"] + fixture["test"], d4, palette)
            ep.update(task_id=tid, episode_id="t", d4_transform=d4, color_permutation=palette)
            assert make_record(ep)["verification"]["all_exact"]
            if tid == "d47aa2ff":
                assert len(motion.candidate_predictions(
                    ep["train"], ep["test"][0]["input"], palette, d4)) == 1


@pytest.mark.parametrize("tid", FAMILIES)
def test_explicit_legacy_scenes_keep_their_legacy_labels(tid):
    old = legacy(tid)
    random.seed(77)
    for _ in range(150):
        p = old.generate()
        if tid == "c7d4e6ad":
            new = mod(tid).generate(colors=[v for row in p["input"] for v in row])
        else:
            g, out = p["input"], p["output"]
            rows, cols, colors, rd, cd = [], [], [], [], []
            for r in range(10):
                for c in range(10):
                    if g[r][c]:
                        rows.append(r), cols.append(c), colors.append(g[r][c])
                        if out[r][c] == 2:
                            (r1, c1), = [(y, x) for y in range(10) for x in range(10)
                                         if out[y][x] == 1 and g[y][x + 11] == g[r][c]]
                            rd.append(r1 - r), cd.append(c1 - c)
                        else:
                            rd.append(0), cd.append(0)
            new = mod(tid).generate(rows=rows, cols=cols, colors=colors, rdiffs=rd, cdiffs=cd)
        assert new == p


# ---------------------------------------------------------------- c7d4e6ad
def test_c7d4e6ad_domain_breadth_and_invariants():
    checker = verification_solver("c7d4e6ad")
    shapes, heights, colours, top0, left = set(), set(), set(), 0, set()
    for p in draws("c7d4e6ad", 600, 5):
        g = p["input"]
        assert grid(checker(g)) == p["output"]
        h, w = len(g), len(g[0])
        shapes.add((h, w))
        legend = [r for r in range(h) if g[r][0]]
        grey = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 5]
        assert sorted({r for r, _ in grey}) == legend
        assert min(c for _, c in grey) >= 2
        heights.add(len(legend))
        colours.add(len({g[r][0] for r in legend}))
        top0 += legend[0] == 0
        left.add(min(c for _, c in grey))
        for r in range(h):
            for c in range(w):
                assert p["output"][r][c] == (g[r][0] if g[r][c] else 0)
    assert len(shapes) > 300 and min(min(s) for s in shapes) == 3 and max(max(s) for s in shapes) == 30
    assert min(heights) == 2 and max(heights) > 20
    assert colours >= {2, 5, 6} and max(colours) <= 8
    assert top0 > 0 and len(left) > 15


@pytest.mark.parametrize("h,w", [(3, 3), (3, 30), (30, 3), (30, 30), (10, 10)])
def test_c7d4e6ad_explicit_shapes_including_3x3(h, w):
    for p in draws("c7d4e6ad", 20, h * 100 + w, height=h, width=w):
        assert (len(p["input"]), len(p["input"][0])) == (h, w)


def test_c7d4e6ad_explicit_contracts():
    gen = mod("c7d4e6ad").generate
    for kw in ({"height": 2, "width": 10}, {"height": 10, "width": 31},
               {"height": True, "width": 10}, {"height": 10.0, "width": 10}):
        with pytest.raises(ValueError):
            gen(**kw)
    valid = [0] * 100
    for r, colour in ((1, 3), (2, 4)):
        valid[r * 10] = colour
        valid[r * 10 + 3] = 5
    assert gen(colors=valid)["output"][1][3] == 3
    with pytest.raises(ValueError):
        gen(colors=valid, height=10)            # partial dimensions
    with pytest.raises(ValueError):
        gen(colors=valid[:99])                  # wrong length
    bad = list(valid)
    bad[3 * 10 + 3] = 5                         # grey row outside the legend
    with pytest.raises(ValueError):
        gen(colors=bad)
    bad = list(valid)
    bad[1 * 10 + 3], bad[1 * 10 + 1] = 0, 5     # grey in column 1
    with pytest.raises(ValueError):
        gen(colors=bad)
    bad = list(valid)
    bad[2 * 10] = 3                             # single legend colour
    with pytest.raises(ValueError):
        gen(colors=bad)


def test_c7d4e6ad_has_no_gate_and_no_competitor_ambiguity():
    comp = competitors()
    random.seed(8)
    pairs = draws("c7d4e6ad", 400, 8)
    for i in range(0, 400, 4):
        demos, query = pairs[i:i + 3], pairs[i + 3]
        assert verdict("c7d4e6ad", demos, query["input"])
        answers = comp.candidate_predictions("c7d4e6ad", demos, query["input"])
        assert [[list(r) for r in a] for a in answers] == [query["output"]]


# ---------------------------------------------------------------- d47aa2ff
def test_d47aa2ff_domain_breadth_and_invariants():
    checker = verification_solver("d47aa2ff")
    shapes, colours, movers, dots = set(), set(), set(), set()
    for p in draws("d47aa2ff", 600, 6):
        g, out = p["input"], p["output"]
        assert grid(checker(g)) == out
        h, width = len(g), len(g[0])
        assert width <= 30 and width % 2 == 1
        w = (width - 1) // 2
        assert all(row[w] == 5 for row in g)
        left = [row[:w] for row in g]
        right = [row[w + 1:] for row in g]
        cells = [(r, c) for r in range(h) for c in range(w) if left[r][c]]
        assert all(left[r][c] in (3, 4, 6, 7, 8, 9) for r, c in cells)
        assert all(max(abs(a - b), abs(x - y)) >= 2 for i, (a, x) in enumerate(cells)
                   for b, y in cells[:i])
        gone = [(r, c) for r in range(h) for c in range(w) if out[r][c] == 2]
        came = [(r, c) for r in range(h) for c in range(w) if out[r][c] == 1]
        assert len(gone) == len(came) >= 1 and len(cells) - len(gone) >= 1
        moved = [left[r][c] for r, c in gone]
        assert len(moved) == len(set(moved))
        for r, c in gone:
            (r1, c1), = [(y, x) for y, x in came if right[y][x] == left[r][c]]
            assert (r1 - r, c1 - c) in motion_offsets()
        shapes.add((h, w))
        colours.add(len({left[r][c] for r, c in cells}))
        movers.add(len(gone))
        dots.add(len(cells))
    assert len(shapes) > 200 and min(min(s) for s in shapes) == 3
    assert max(s[0] for s in shapes) == 30 and max(s[1] for s in shapes) == 14
    assert colours >= {1, 2, 3, 4, 5, 6}
    assert max(movers) >= 4 and min(dots) == 2 and max(dots) > 20


def motion_offsets():
    return set(mod("d47aa2ff").OFFSETS)


def test_d47aa2ff_explicit_contracts():
    gen = mod("d47aa2ff").generate
    base = dict(rows=[1, 5], cols=[1, 5], colors=[3, 4], rdiffs=[1, 0], cdiffs=[0, 0])
    assert gen(**base)["output"][2][1] == 1
    assert len(gen(**base, height=7, width=6)["input"][0]) == 13
    for change in ({"colors": [2, 4]}, {"colors": [5, 4]}, {"rdiffs": [0, 0]},
                   {"rdiffs": [1, 1]}, {"rdiffs": [2, 0], "cdiffs": [2, 0]},
                   {"rows": [1, 2], "cols": [1, 2]}, {"rows": [1, 5, 7]}, {"rdiffs": [1, True]}):
        with pytest.raises(ValueError):
            gen(**dict(base, **change))
    with pytest.raises(ValueError):
        gen(rows=[1], cols=[1])
    with pytest.raises(ValueError):
        gen(**base, height=10)
    for kw in ({"height": 2, "width": 5}, {"height": 5, "width": 15}):
        with pytest.raises(ValueError):
            gen(**kw)
    two_same = dict(rows=[0, 0, 4], cols=[0, 3, 4], colors=[3, 3, 4],
                    rdiffs=[1, 1, 0], cdiffs=[0, 0, 0])
    with pytest.raises(ValueError):
        gen(**two_same)


@pytest.mark.parametrize("h,w", [(3, 3), (30, 14), (3, 14), (30, 3)])
def test_d47aa2ff_extreme_panels(h, w):
    for p in draws("d47aa2ff", 20, h * 100 + w, height=h, width=w):
        assert (len(p["input"]), len(p["input"][0])) == (h, 2 * w + 1)


def test_gate_rejects_every_stored_trail_witness_in_every_frame():
    witnesses = evidence()["families"]["d47aa2ff"]["witnesses"]
    assert set(witnesses) == set(motion.TRAILS)
    for w in witnesses.values():
        pairs = w["demonstrations"] + [{"input": w["query_input"], "output": w["native_answer"]}]
        for palette in PALETTES:
            for d4 in range(8):
                ep = episode(pairs, d4, palette)
                assert not verdict("d47aa2ff", ep["train"], ep["test"][0]["input"], palette, d4)


def test_trail_witness_query_is_resolved_by_a_two_cell_move_demo():
    w = evidence()["families"]["d47aa2ff"]["witnesses"]["trail-line-red"]
    fixture = reference("d47aa2ff")["canonical"]["train"]   # includes a (-2, 0) move
    demos = w["demonstrations"][:2] + [fixture[2]]
    assert verdict("d47aa2ff", demos, w["query_input"])


def test_gate_verdict_is_d4_invariant_and_answer_blind():
    random.seed(12)
    for _ in range(60):
        pairs = [mod("d47aa2ff").generate() for _ in range(4)]
        palette = list(range(10))
        random.shuffle(palette)
        seen = set()
        for d4 in range(8):
            ep = episode(pairs, d4, palette)
            plain = verdict("d47aa2ff", ep["train"], ep["test"][0]["input"], palette, d4)
            bogus = [{"input": ep["test"][0]["input"], "output": [[0]]}]
            try:
                require_colour_evidence("d47aa2ff", ep["train"], bogus, palette, d4)
                with_answer = True
            except MissingColourEvidence:
                with_answer = False
            assert plain == with_answer
            seen.add(plain)
        assert len(seen) == 1


def test_gate_matches_report_competitors_and_classes():
    comp = competitors()
    assert comp.RULES["d47aa2ff"] == motion.RULES
    classes = evidence()["families"]["d47aa2ff"]["competitors"]["current"]
    separable = {k for k, v in classes.items() if v["class"] == "separable"}
    assert separable == set(motion.TRAILS)
    c7 = evidence()["families"]["c7d4e6ad"]["competitors"]
    for label in ("legacy", "current"):
        assert {v["class"] for v in c7[label].values()} == {
            "native", "refuted_by_any_demo", "identical_on_domain"}


def test_off_domain_probes_are_outside_the_constructor_domain():
    probes = evidence()["probes"]
    for name in ("c7d4e6ad:grey_row_outside_legend", "c7d4e6ad:legend_row_without_grey"):
        with pytest.raises(ValueError):
            mod("c7d4e6ad").check_scene(probes[name]["query_input"])
    assert probes["c7d4e6ad:single_colour_legend_demo"]["ambiguous_with_three_copies"]
    assert probes["d47aa2ff:no_stationary_dot_demo"]["ambiguous_with_three_copies"]
    assert "matched_pairs_only" in probes["d47aa2ff:two_movers_same_colour"]["rules_differing_from_native"]


# ------------------------------------------------- capacity and audit
def test_finite_capacity_is_recorded_not_narrowed():
    cap = evidence()["capacity"]
    assert cap["c7d4e6ad_3x3_exact"]["valid_inputs"] == 112
    assert cap["c7d4e6ad_3x3_exact"]["input_orbits"] == 1
    assert mod("c7d4e6ad").MIN_DIM == 3


def test_context_audit_keeps_every_query_and_reports_failures():
    path = REPORT / "context-audit.json"
    if not path.exists():
        pytest.skip("context audit not yet written")
    audit = json.loads(path.read_text())
    assert len(audit) == 10
    for key, r in audit.items():
        assert r["queries_accepted"] + len(r["queries_failed"]) == r["queries_requested"] == 250
        assert r["semantic_checks_passed"], key
        assert r["d4_inconsistent_contexts"] == 0 and r["gate_competitor_disagreements"] == 0
        assert all(f["reason"] == "same_shape_orbit_capacity" for f in r["queries_failed"])
    assert audit["c7d4e6ad@min_canvas"]["queries_failed_by_reason"] == {"same_shape_orbit_capacity": 250}
    assert not audit["c7d4e6ad@min_canvas"]["passed"]


# ---------------------------------------------------------------- pins
@pytest.mark.parametrize("tid", FAMILIES)
def test_certificates_bind_current_bytes(tid):
    cert = json.loads((BASE / "direct_factories" / f"{tid}.json").read_text())
    mirror = json.loads((BASE / "reports/diversity-v1/native-certificates" / f"{tid}.json").read_text())
    assert cert["passed"] and cert["fresh_pairs_checked"] == 1000
    assert cert["augmented_pair_checks"] == 8000 and cert["fixture_variants_checked"] == 16
    assert cert["sampler_rejections"] == []
    assert cert["constructor_sha256"] == sha_bytes(BASE.parent / "tasks" / f"task_{tid}.py")
    assert cert["factory_sha256"] == FACTORY_SHA[tid] == sha_bytes(
        BASE / "direct_factories" / f"task_{tid}.py")
    assert cert["previous_constructor_sha256"] == LEGACY_SHA[tid]
    assert {k: cert[k] for k in mirror} == mirror


def test_evidence_and_audit_pin_current_sources():
    files = {"constructor_c7d4e6ad": BASE.parent / "tasks/task_c7d4e6ad.py",
             "constructor_d47aa2ff": BASE.parent / "tasks/task_d47aa2ff.py",
             "dot_motion_d47aa2ff_evidence": BASE / "dot_motion_d47aa2ff_evidence.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "competitors": REPORT / "competitors.py",
             "harness": REPORT / "batch_evidence.py"}
    pins = evidence()["source_sha256"]
    for key, path in files.items():
        assert pins[key] == sha_bytes(path), key
    path = REPORT / "context-audit.json"
    if path.exists():
        for key, r in json.loads(path.read_text()).items():
            tid = r["task_id"]
            assert r["source_sha256"]["constructor"] == sha_bytes(BASE.parent / "tasks" / f"task_{tid}.py")
            assert r["source_sha256"]["colour_evidence"] == sha_bytes(BASE / "colour_evidence.py")
            assert r["source_sha256"]["harness"] == sha_bytes(REPORT / "context_audit.py")
