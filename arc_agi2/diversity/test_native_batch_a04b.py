"""Native batch a04b: a04b2602 rings around reds inside green rectangles.

Domain: canvas 10..30 x 10..30, 2..3 rectangles of side 4..(side - 6),
spacing >= 1 (legacy 2; canonical train[0] has a one-row gap), red rate 1/k
with k in 12..30 (legacy 1/20). Kept: the outlined == expected guard (reds
with >= 2 orthogonal green neighbours are exactly the reds inside
rectangles, and there is one), bounded retries without fallback, explicit
colors drawn exactly as given. Checker: verified_rules.rectangle_red_rings
(the archived component-box solver mislabels rectangles cut by reds, legacy
bytes included). Gate: rect_ring_a04b2602_evidence (spare-reds rings,
corner-reds-unframed and sequential stamping survive about a fifth of random
three-demonstration contexts). Factory and canonical labels are unchanged.
"""
import hashlib
import importlib.util
import json
import random
import subprocess
import types

import pytest

import common
from arc_agi2 import rect_ring_a04b2602_evidence as gate
from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import make_record
from arc_agi2.runtime import BASE, grid, reference, solver, verification_solver
from arc_agi2.verified_rules import VERIFIER_EVIDENCE, VERIFIERS, rectangle_red_rings
import tasks.task_a04b2602 as task

TID = "a04b2602"
PALETTES = (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5])
REPORT = BASE / "reports/diversity-v1/native-batch-a04b"
BASE_COMMIT = "9498a906edc8a0ce0ec9e556476f3411714e3d25"
LEGACY_SHA = "bdc127732747d186de38978a1ba859b0ac8783c8b065e7abd791982131f44b7c"
FACTORY_SHA = "d9e8477a5d2e1c4b59d774e1fda7ec59c80b9c162c10175b0b9f2ac9b4e5a21f"
ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))


def sha_bytes(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def legacy():
    src = subprocess.run(["git", "show", f"{BASE_COMMIT}:tasks/task_{TID}.py"],
                         capture_output=True, check=True, cwd=BASE.parent).stdout
    assert hashlib.sha256(src).hexdigest() == LEGACY_SHA
    module = types.ModuleType(f"legacy_{TID}")
    exec(compile(src, f"legacy/task_{TID}.py", "exec"), module.__dict__)
    return module


def competitors():
    spec = importlib.util.spec_from_file_location("batch_a04b_competitors", REPORT / "competitors.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evidence():
    return json.loads((REPORT / "batch-evidence.json").read_text())


def verdict(demos, query_input, palette=None, d4=0):
    try:
        require_colour_evidence(TID, demos, [{"input": query_input}], palette, d4)
        return True
    except MissingColourEvidence:
        return False


def draws(n, seed, **kw):
    random.seed(seed)
    return [task.generate(**kw) for _ in range(n)]


def readings(g):
    """(reds with >= 2 orthogonal greens, reds inside merged rectangles)."""
    comp = competitors()
    return comp.sel_native(g), comp.sel_inside(g)


# ---------------------------------------------------------------- fixtures
def test_canonical_fixtures_replay_exactly():
    fixture = reference(TID)["canonical"]
    replay = task.validate()
    for split in ("train", "test"):
        assert (sorted(json.dumps(p, sort_keys=True) for p in replay[split])
                == sorted(json.dumps(p, sort_keys=True) for p in fixture[split]))


def test_canonical_episodes_pass_make_record_and_gate_in_all_variants():
    fixture = reference(TID)["canonical"]
    for palette in PALETTES:
        for d4 in range(8):
            ep = episode(fixture["train"] + fixture["test"], d4, palette)
            ep.update(task_id=TID, episode_id="t", d4_transform=d4, color_permutation=palette)
            assert make_record(ep)["verification"]["all_exact"]
            assert len(gate.candidate_predictions(ep["train"], ep["test"][0]["input"],
                                                  palette, d4)) == 1


def test_canonical_train0_gap1_is_now_reachable():
    rows = {r["pair"]: r for r in evidence()["canonical"]["pairs"]}
    assert rows["train0"]["pairwise_gaps"][0] == 1
    assert not rows["train0"]["reachable_legacy_spacing_2"]
    assert all(r["reachable_current_spacing_1"] for r in rows.values())
    assert task.SPACING == 1


def test_explicit_legacy_scenes_keep_their_legacy_labels():
    old = legacy()
    random.seed(77)
    for _ in range(150):
        pair = old.generate()
        g = pair["input"]
        again = task.generate(width=len(g[0]), height=len(g), colors=sum(g, []))
        assert again == pair


# ---------------------------------------------------------------- domain
def test_default_domain_breadth_and_invariants():
    comp = competitors()
    seen_gap1, periods, shapes, counts = 0, set(), set(), set()
    check = verification_solver(TID)
    calls = []
    orig = common.randint

    def spy(a, b):
        v = orig(a, b)
        if (a, b) == task.RED_PERIODS:
            calls.append(v)
        return v

    common.randint = spy
    try:
        pairs = draws(300, 5)
    finally:
        common.randint = orig
    for pair in pairs:
        g = pair["input"]
        h, w = len(g), len(g[0])
        assert 10 <= h <= 30 and 10 <= w <= 30
        shapes.add((h, w))
        assert {v for row in g for v in row} <= {0, 2, 3}
        native, inside = readings(g)
        assert native == inside and native
        boxes = comp.rectangles(g)
        counts.add(len(boxes))
        gaps = [max(max(a[0] - b[2], b[0] - a[2]) - 1, max(a[1] - b[3], b[1] - a[3]) - 1)
                for k, a in enumerate(boxes) for b in boxes[:k]]
        assert min(gaps) >= 1
        seen_gap1 += min(gaps) == 1
        assert grid(check(g)) == pair["output"]
    periods.update(calls)
    assert seen_gap1 > 60
    assert len(periods) >= 15 and min(periods) >= 12 and max(periods) <= 30
    assert counts <= {2, 3} and len(shapes) > 100


@pytest.mark.parametrize("h,w", [(10, 10), (10, 30), (30, 10), (30, 30), (17, 23)])
def test_explicit_dimensions_sample_at_that_shape(h, w):
    check = verification_solver(TID)
    for pair in draws(10, h * 100 + w, height=h, width=w):
        assert len(pair["input"]) == h and len(pair["input"][0]) == w
        assert grid(check(pair["input"])) == pair["output"]


@pytest.mark.parametrize("kw", [dict(width=12), dict(height=12), dict(width=9, height=12),
                                dict(width=12, height=31), dict(width=True, height=12),
                                dict(width=12.0, height=12), dict(colors=[0] * 100),
                                dict(width=10, height=10, colors=[0] * 99),
                                dict(width=31, height=10, colors=[0] * 310)])
def test_invalid_arguments_raise_value_error(kw):
    with pytest.raises(ValueError):
        task.generate(**kw)


def test_retries_are_bounded_without_fallback(monkeypatch):
    monkeypatch.setattr(common, "overlaps", lambda *a, **k: True)
    with pytest.raises(RuntimeError):
        task.generate()
    monkeypatch.setattr(task, "ATTEMPTS", 0)
    with pytest.raises(RuntimeError):
        task.generate(width=20, height=20)


def test_guard_rejects_gap_red_touching_two_rectangles():
    probes = evidence()["probes"]
    p = probes["gap1_red_touching_two_rectangles"]
    assert not p["native_neighbour_rule_equals_inside_rectangle"]
    assert p["reviewed_checker"].startswith("raised")
    assert probes["gap1_red_outside_facing_span"]["reviewed_equals_label"]
    assert probes["touching_rectangles"]["reviewed_checker"].startswith("raised")


# ---------------------------------------------------------------- checker
def test_reviewed_checker_is_registered_with_evidence():
    assert VERIFIERS[TID] is rectangle_red_rings is verification_solver(TID)
    ev = VERIFIER_EVIDENCE[TID]
    assert ev["module"] == "arc_agi2.verified_rules.rectangle_red_rings"
    assert not ev["canonical_data_changed"] and not ev["archived_reference_changed"]
    assert (BASE.parent / ev["counterexample"]).exists()


def test_reviewed_checker_exact_on_fixtures():
    ref = reference(TID)
    for name in ("canonical", "teaching_fixture"):
        for p in ref[name]["train"] + ref[name]["test"]:
            assert rectangle_red_rings(p["input"]) == p["output"]


def test_archived_counterexamples_replay():
    ce = json.loads((REPORT / f"{TID}-archived-verifier-counterexample.json").read_text())
    assert ce["legacy_constructor_sha256"] == LEGACY_SHA
    archived = solver(TID)
    for label in ("legacy", "current"):
        assert ce[label]["archived_disagreements"] >= 1
        assert ce[label]["reviewed_verifier_disagreements"] == 0
        x = ce[label]["first_counterexample"]
        assert grid(archived(x["input"])) != x["constructor_label"]
        assert rectangle_red_rings(x["input"]) == x["constructor_label"]
        assert x["reds_inside_rectangle_outside_component_boxes"]
    old = legacy()
    random.seed(ce["legacy"]["first_counterexample"]["seed"])
    assert old.generate()["input"] == ce["legacy"]["first_counterexample"]["input"]


def test_reviewed_checker_raises_off_domain():
    g = [[0] * 10 for _ in range(10)]
    g[0][0] = 5
    with pytest.raises(ValueError):
        rectangle_red_rings(g)
    with pytest.raises(ValueError):  # no red inside a rectangle
        rectangle_red_rings([[3] * 10 for _ in range(4)] + [[0] * 10 for _ in range(6)])


# ---------------------------------------------------------------- gate
def test_gate_rules_equal_harness_rules_and_answers():
    comp = competitors()
    assert set(gate.RULES) == set(comp.RULES) and len(gate.RULES) == 22
    for pair in draws(150, 31):
        v = gate.variants(pair["input"])
        for name, f in comp.RULES.items():
            assert v[name] == comp._key(f(pair["input"])), name


def test_dispatch_routes_to_gate():
    w = evidence()["witnesses"][0]
    with pytest.raises(MissingColourEvidence, match=TID):
        require_colour_evidence(TID, w["demonstrations"], [{"input": w["query_input"]}])


def test_every_stored_witness_is_rejected_in_all_frames():
    witnesses = evidence()["witnesses"]
    separable = set(evidence()["single_pair_classes"]["separable_in_some_context"])
    assert {n for w in witnesses for n in w["separating"]} == separable
    assert {"paint:spare_reds", "select:touch_ge3", "paint:sequential_stamp:rc",
            "select:component_bbox"} <= separable
    for w in witnesses:
        for palette in PALETTES:
            for d4 in range(8):
                ep = episode(w["demonstrations"] + [{"input": w["query_input"],
                                                     "output": w["query_input"]}], d4, palette)
                assert not verdict(ep["train"], ep["test"][0]["input"], palette, d4)


def test_gate_is_d4_invariant_and_answer_blind():
    rng = random.Random(3)
    outcomes = set()
    for i in range(40):
        four = draws(4, 1000 + i)
        palette = list(range(10))
        rng.shuffle(palette)
        seen = set()
        for d4 in range(8):
            ep = episode(four, d4, palette)
            plain = verdict(ep["train"], ep["test"][0]["input"], palette, d4)
            bogus = [{"input": ep["test"][0]["input"], "output": ep["train"][0]["output"]}]
            try:
                require_colour_evidence(TID, ep["train"], bogus, palette, d4)
                with_answer = True
            except MissingColourEvidence:
                with_answer = False
            assert plain == with_answer
            seen.add(plain)
        assert len(seen) == 1
        outcomes |= seen
    assert outcomes == {True, False}


def test_canonical_train_refutes_the_separable_readings():
    can = evidence()["canonical"]
    assert can["train_survivors"] == ["native", "select:inside_rectangle", "select:component_bbox"]
    assert not can["train_context_ambiguous_on_test"]


# ------------------------------------------------- evidence, capacity, audit
def test_domain_evidence_before_after():
    d = evidence()["domain"]
    assert d["legacy"]["scenes_with_gap_1"] == 0 and d["current"]["scenes_with_gap_1"] > 500
    assert d["legacy"]["red_period_histogram"] == {"20": 2000}
    assert len(d["current"]["red_period_histogram"]) == 19
    for label in ("legacy", "current"):
        assert d[label]["accepted"] == 2000 and not d[label]["runtime_errors"]
        assert d[label]["checker_agreement"]["reviewed"] == 2000
        assert d[label]["checker_agreement"]["factory_program"] == 2000
    assert d["legacy"]["checker_agreement"]["archived"] < 2000


def test_capacity_is_recorded_not_narrowed():
    cap = evidence()["capacity"]["distinct_input_orbits"]
    assert cap["10x10"] >= 4 and task.MIN_DIM == 10 and task.MAX_DIM == 30


def test_context_audit_keeps_every_query_and_reports_failures():
    path = REPORT / "context-audit.json"
    if not path.exists():
        pytest.skip("context audit not yet written")
    audit = json.loads(path.read_text())
    assert set(audit) == {TID, TID + "@gap1"}
    for key, r in audit.items():
        assert r["queries_accepted"] + len(r["queries_failed"]) == r["queries_requested"] == 250
        assert r["semantic_checks_passed"], key
        assert r["d4_inconsistent_contexts"] == 0 and r["gate_competitor_disagreements"] == 0
        assert all(f["reason"] for f in r["queries_failed"])
    assert audit[TID + "@gap1"]["query_min_gap_histogram"] == {"1": 250}


# ---------------------------------------------------------------- pins
def test_certificate_binds_current_bytes():
    cert = json.loads((BASE / "direct_factories" / f"{TID}.json").read_text())
    mirror = json.loads((BASE / "reports/diversity-v1/native-certificates" / f"{TID}.json").read_text())
    assert cert["passed"] and cert["fresh_pairs_checked"] == 1000
    assert cert["augmented_pair_checks"] == 8000 and cert["fixture_variants_checked"] == 16
    assert cert["sampler_rejections"] == [] and cert["unique_base_inputs"] == 1000
    assert cert["constructor_sha256"] == sha_bytes(BASE.parent / "tasks" / f"task_{TID}.py")
    assert cert["factory_sha256"] == FACTORY_SHA == sha_bytes(
        BASE / "direct_factories" / f"task_{TID}.py")
    assert cert["previous_constructor_sha256"] == LEGACY_SHA
    assert {k: cert[k] for k in mirror if k != "seconds"} == {
        k: v for k, v in mirror.items() if k != "seconds"}


def test_evidence_and_audit_pin_current_sources():
    files = {"constructor": BASE.parent / f"tasks/task_{TID}.py",
             "factory": BASE / "direct_factories" / f"task_{TID}.py",
             "factory_certificate": BASE / "direct_factories" / f"{TID}.json",
             "verified_rules": BASE / "verified_rules.py",
             "gate": BASE / "rect_ring_a04b2602_evidence.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "competitors": REPORT / "competitors.py",
             "harness": REPORT / "batch_evidence.py"}
    pins = evidence()["source_sha256"]
    for key, path in files.items():
        assert pins[key] == sha_bytes(path), key
    path = REPORT / "context-audit.json"
    if path.exists():
        for key, r in json.loads(path.read_text()).items():
            for name in ("constructor", "factory", "factory_certificate", "gate",
                         "colour_evidence", "verified_rules", "competitors"):
                assert r["source_sha256"][name] == pins[name], (key, name)
            assert r["source_sha256"]["harness"] == sha_bytes(REPORT / "context_audit.py")
