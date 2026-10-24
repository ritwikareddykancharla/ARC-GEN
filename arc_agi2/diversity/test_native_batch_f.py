"""Native batch F: independent H x W (2..5) for the three self-tiling families.

* 27f8ce4f  copy the input into each block whose cell has the unique modal colour.
* 48f8583b  copy the input into each block whose cell has the unique rarest colour.
* 5b6cbef5  copy the input into each block whose cell is inked (one-ink mask).

The output is (H*H) x (W*W), so each axis is limited to 2..5 independently
(5x5 -> 25x25 is the largest legal input; 6 would give 36). Rules, colour roles,
fixtures and direct factories are unchanged. Explicit colours with omitted
dimensions keep the legacy canvas (3x3, 3x3, 4x4), and every explicit input the
legacy generator labelled is labelled identically (tested against the
hash-checked legacy bytes).
"""
import hashlib
import importlib
import json
import random
import subprocess
import time
import types
from collections import Counter

import pytest

from arc_agi2.diversity.recertify import episode
from arc_agi2.program_targets import verify
from arc_agi2.runtime import BASE, call, grid, reference, verification_solver

FAMILIES = ("27f8ce4f", "48f8583b", "5b6cbef5")
PALETTE = [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]
REPORT = BASE / "reports/diversity-v1/native-batch-f"
BASE_REV = "e72190b"
LEGACY_SHA = {"27f8ce4f": "70c1d22e63c495fb6406e92fc0f616939995b39333bc8cf2fee2d2a62b1e3e78",
              "48f8583b": "e03a032ed0ebe4f6481595d20554648bb8fc2fe34d2556c4b8ad6fbf895cf0e6",
              "5b6cbef5": "7037789f7a5655b1bd06bcfbad383bdfc7b8c9d91f7a6b4c04c4f73df692aa24"}
LEGACY_DIMS = {"27f8ce4f": (3, 3), "48f8583b": (3, 3), "5b6cbef5": (4, 4)}


def mod(tid):
    return importlib.import_module("tasks.task_" + tid)


def gen(tid, **kw):
    return call(mod(tid).generate, seconds=3, **kw)


def legacy(tid):
    src = subprocess.run(["git", "show", f"{BASE_REV}:tasks/task_{tid}.py"], check=True,
                         capture_output=True, cwd=BASE.parent).stdout
    assert hashlib.sha256(src).hexdigest() == LEGACY_SHA[tid]
    module = types.ModuleType(f"legacy_{tid}")
    exec(compile(src, f"legacy/task_{tid}.py", "exec"), module.__dict__)
    return module


def factory(tid, d4, palette):
    return importlib.import_module("arc_agi2.direct_factories.task_" + tid).build_program(d4, palette)


def certify(tid, pairs):
    """Independent (archived) checker labels plus the direct factory on all eight D4."""
    checker = verification_solver(tid)
    for p in pairs:
        assert grid(checker(p["input"])) == p["output"]
    for d4 in range(8):
        verify(factory(tid, d4, PALETTE), episode(pairs, d4, PALETTE))


def independent(tid, g):
    """Self-tiling written from the rule statement, raising outside the native domain."""
    h, w = len(g), len(g[0])
    counts = Counter(v for r in g for v in r)
    if tid == "5b6cbef5":
        if len(set(counts) - {0}) != 1:
            raise ValueError("expected one ink")
        selected = lambda v: v != 0
    else:
        order = counts.most_common()
        if tid == "48f8583b":
            order = order[::-1]
        if len(order) > 1 and order[0][1] == order[1][1]:
            raise ValueError("tied selector")
        selected = lambda v, s=order[0][0]: v == s
    return [[g[y % h][x % w] if selected(g[y // h][x // w]) else 0 for x in range(w * w)]
            for y in range(h * h)]


# ------------------------------------------------------------- replay
@pytest.mark.parametrize("tid", FAMILIES)
def test_fixture_replay_and_factory(tid):
    ref = reference(tid)
    replay = mod(tid).validate()
    for split in ("train", "test"):
        assert (sorted(json.dumps(p, sort_keys=True) for p in replay[split])
                == sorted(json.dumps(p, sort_keys=True) for p in ref["canonical"][split]))
    for name in ("canonical", "teaching_fixture"):
        pairs = ref[name]["train"] + ref[name]["test"]
        assert all(independent(tid, p["input"]) == p["output"] for p in pairs)
        certify(tid, pairs)


def _explicit_cases(tid, rng, n=400):
    h, w = LEGACY_DIMS[tid]
    cases = []
    for _ in range(n):
        if tid == "5b6cbef5":
            inks = rng.sample(range(1, 10), rng.randint(1, 3))
            cases.append([rng.choice(inks) if rng.random() < 0.5 else 0 for _ in range(h * w)])
        else:
            pool = rng.sample(range(0, 10), rng.randint(1, 5))
            cases.append([rng.choice(pool) for _ in range(h * w)])
    cases += [[0] * (h * w), [5] * (h * w)]
    return cases


@pytest.mark.parametrize("tid", FAMILIES)
def test_explicit_legacy_outputs_preserved(tid):
    """Every explicit input the legacy bytes labelled gets the identical pair, including
    zeros (27/48), tied minima (48, legacy smallest-colour tie break), monochrome (48),
    several inks and empty masks (5b). Legacy None/crash cases now raise ValueError."""
    old, rng = legacy(tid), random.Random(7)
    labelled = raised = 0
    for colors in _explicit_cases(tid, rng):
        try:
            want = old.generate(colors=list(colors))
        except IndexError:          # 27f8ce4f one-colour input
            want = None
        if want is None or want["input"] is None:
            with pytest.raises(ValueError):
                gen(tid, colors=list(colors))
            raised += 1
        else:
            assert gen(tid, colors=list(colors)) == want
            labelled += 1
    assert labelled > 250
    if tid != "27f8ce4f":
        assert raised == 0
    else:
        assert raised > 0


def test_legacy_explicit_classes_kept():
    tie = gen("48f8583b", colors=[1, 1, 2, 2, 3, 3, 3, 3, 3])     # 1 and 2 tie at 2
    assert tie["output"][0][:3] == [1, 1, 2] and tie["output"][0][6:] == [0, 0, 0]
    mono = gen("48f8583b", colors=[6] * 9)
    assert all(v == 6 for r in mono["output"] for v in r)
    zero = gen("27f8ce4f", colors=[0, 0, 0, 0, 1, 2, 3, 0, 0])
    assert zero["output"][0][:3] == [0, 0, 0] and zero["output"][3][3:6] == [0, 0, 0]
    multi = gen("5b6cbef5", colors=[1, 2] + [0] * 14)            # legacy colour-on-mask
    assert multi["output"][0][:4] == [1, 1, 0, 0] and multi["output"][0][4:8] == [2, 2, 0, 0]
    empty = gen("5b6cbef5", colors=[0] * 16)
    assert all(v == 0 for r in empty["output"] for v in r)


@pytest.mark.parametrize("tid", ("27f8ce4f", "48f8583b"))
def test_legacy_rng_stream_replays_at_explicit_3x3(tid):
    old = legacy(tid)
    for seed in range(60):
        random.seed(seed)
        want = old.generate()
        random.seed(seed)
        assert gen(tid, height=3, width=3) == want


# ------------------------------------------------------------- domain
@pytest.mark.parametrize("tid", FAMILIES)
def test_all_sixteen_shapes_checker_and_factory(tid):
    for h in range(2, 6):
        for w in range(2, 6):
            random.seed(f"shape:{tid}:{h}:{w}")
            pairs = [{k: grid(v) for k, v in gen(tid, height=h, width=w).items()} for _ in range(4)]
            for p in pairs:
                assert (len(p["input"]), len(p["input"][0])) == (h, w)
                assert (len(p["output"]), len(p["output"][0])) == (h * h, w * w)
                assert independent(tid, p["input"]) == p["output"]
            certify(tid, pairs)


@pytest.mark.parametrize("tid", FAMILIES)
def test_default_sampling_structure(tid):
    shapes, kinds = Counter(), Counter()
    for seed in range(800):
        random.seed(f"default:{tid}:{seed}")
        g = gen(tid)["input"]
        h, w = len(g), len(g[0])
        shapes[(h, w)] += 1
        counts = Counter(v for r in g for v in r)
        assert 0 not in counts or tid == "5b6cbef5"
        if tid == "27f8ce4f":
            top = sorted(counts.values())
            assert 3 <= len(counts) <= min(5, h * w - 1) and top[-1] != top[-2]
            kinds[len(counts)] += 1
        elif tid == "48f8583b":
            low = sorted(counts.values())
            assert 1 <= len(counts) <= 4 and low.count(low[0]) == 1
            kinds[len(counts)] += 1
        else:
            assert len(set(counts) - {0}) == 1
            kinds[next(iter(set(counts) - {0}))] += 1
    assert len(shapes) == 16 and any(h != w for h, w in shapes)
    if tid == "27f8ce4f":
        assert set(kinds) == {3, 4, 5}
    elif tid == "48f8583b":
        assert set(kinds) == {1, 2, 3, 4}          # monochrome keeps default support
    else:
        assert set(kinds) == set(range(1, 10))      # ink 1..9


def test_small_shape_feasibility():
    for seed in range(200):
        random.seed(seed)
        g = gen("27f8ce4f", height=2, width=2)["input"]
        assert sorted(Counter(v for r in g for v in r).values()) == [1, 1, 2]
        g = gen("48f8583b", height=2, width=2)["input"]
        assert sorted(Counter(v for r in g for v in r).values()) in ([4], [1, 3])
    # 48f8583b keeps its legacy nominal subset: a 4-colour subset is legal even at 2x2.
    random.seed(1)
    gen("48f8583b", height=2, width=2, num_colors=4)


def test_largest_and_rectangular_canvases():
    for tid in FAMILIES:
        p = gen(tid, height=5, width=5)
        assert (len(p["output"]), len(p["output"][0])) == (25, 25)
        p = gen(tid, height=2, width=5)
        assert (len(p["output"]), len(p["output"][0])) == (4, 25)
        for bad in ({"height": 6}, {"width": 6}, {"height": 1}, {"width": 0}):
            with pytest.raises(ValueError):
                gen(tid, **bad)


# ------------------------------------------------------------- arguments
@pytest.mark.parametrize("tid", FAMILIES)
def test_partial_and_explicit_dimensions(tid):
    random.seed(3)
    p = gen(tid, height=2)
    assert len(p["input"]) == 2 and 2 <= len(p["input"][0]) <= 5
    p = gen(tid, width=5)
    assert len(p["input"][0]) == 5
    lh, lw = LEGACY_DIMS[tid]
    colors = [c for r in reference(tid)["canonical"]["train"][0]["input"] for c in r]
    assert gen(tid, colors=colors)["input"] == reference(tid)["canonical"]["train"][0]["input"]
    explicit = {"27f8ce4f": [1, 1, 2, 3, 1, 4], "48f8583b": [1, 2, 2, 2, 3, 3],
                "5b6cbef5": [0, 4, 4, 0, 0, 4]}[tid]
    p = gen(tid, colors=explicit, height=2, width=3)
    assert (len(p["input"]), len(p["input"][0])) == (2, 3) and independent(tid, p["input"]) == p["output"]
    # Partial dims with explicit colours: the omitted axis is the legacy size.
    if lw == 3:
        assert (len(gen(tid, colors=explicit, height=2)["input"][0])) == 3
        assert len(gen(tid, colors=explicit, width=2)["input"]) == 3
    else:
        with pytest.raises(ValueError):
            gen(tid, colors=explicit, height=2)
        p = gen(tid, colors=explicit + [0, 4], height=2)
        assert (len(p["input"]), len(p["input"][0])) == (2, 4)


@pytest.mark.parametrize("tid", FAMILIES)
def test_invalid_arguments_raise(tid):
    lh, lw = LEGACY_DIMS[tid]
    ok = [1] * (lh * lw - 2) + [2, 3] if tid == "27f8ce4f" else [1] * (lh * lw - 1) + [2]
    for bad in ({"height": 3.0}, {"width": True}, {"height": "3"},
                {"colors": ok[:-1]}, {"colors": ok[:-1] + [10]}, {"colors": ok[:-1] + [-1]},
                {"colors": ok[:-1] + [2.0]}, {"colors": ok[:-1] + [True]}):
        with pytest.raises(ValueError):
            gen(tid, **bad)
    sampling = "color" if tid == "5b6cbef5" else "num_colors"
    with pytest.raises(ValueError):
        gen(tid, colors=ok, **{sampling: 2})
    for value in (0, 10, 2.0, True) if tid == "5b6cbef5" else (1, 6, 3.0, False):
        with pytest.raises(ValueError):
            gen(tid, **{sampling: value})


def test_infeasible_colour_counts_raise_before_sampling():
    """27f8ce4f needs area >= K + 1: K = 4 or 5 at 2x2 is infeasible. The error is raised
    immediately (no RNG draws, no retries) and differs from budget exhaustion."""
    for k in (4, 5):
        random.seed(0)
        state = random.getstate()
        with pytest.raises(ValueError, match="infeasible"):
            gen("27f8ce4f", height=2, width=2, num_colors=k)
        assert random.getstate() == state
    gen("27f8ce4f", height=2, width=3, num_colors=5)
    # Omitted dimensions are drawn only among canvases that can hold the request.
    for seed in range(300):
        random.seed(seed)
        g = gen("27f8ce4f", num_colors=5)["input"]
        assert len(g) * len(g[0]) >= 6 and len(Counter(v for r in g for v in r)) == 5
        random.seed(seed)
        g = gen("27f8ce4f", height=2, num_colors=4)["input"]
        assert len(g) == 2 and len(g[0]) >= 3


def test_budget_exhaustion_is_runtime_error(monkeypatch):
    import common
    monkeypatch.setattr(common, "choices", lambda seq, k=1: [seq[0]] * k)
    with pytest.raises(RuntimeError, match="budget"):
        mod("27f8ce4f").generate(height=3, width=3)
    monkeypatch.setattr(common, "choices", lambda seq, k=1: [seq[i % 2] for i in range(k)])
    with pytest.raises(RuntimeError, match="budget"):
        mod("48f8583b").generate(height=2, width=2, num_colors=2)
    monkeypatch.setattr(common, "randint", lambda a, b: a)
    with pytest.raises(RuntimeError, match="budget"):
        mod("5b6cbef5").generate(height=2, width=2, color=3)


def test_default_draws_are_fast():
    started = time.monotonic()
    for tid in FAMILIES:
        for seed in range(300):
            random.seed(seed)
            gen(tid, height=2, width=3) if tid == "27f8ce4f" else gen(tid, height=2, width=2)
            gen(tid, height=5, width=5)
    assert time.monotonic() - started < 10


# ------------------------------------------------------------- provenance
@pytest.mark.parametrize("tid", FAMILIES)
def test_certificate_binds_current_sources(tid):
    cert = json.loads((BASE / "direct_factories" / f"{tid}.json").read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert cert["passed"] and cert["fresh_pairs_checked"] == 1000
    assert cert["augmented_pair_checks"] == 8000 and cert["fixture_variants_checked"] == 16
    assert cert["constructor_sha256"] == sha(BASE.parent / "tasks" / f"task_{tid}.py")
    assert cert["factory_sha256"] == sha(BASE / "direct_factories" / f"task_{tid}.py")
    assert cert["previous_constructor_sha256"] == LEGACY_SHA[tid]
    assert cert["provenance"] and cert["draft_notes"]["limitations"]


def test_context_audit_binds_current_sources():
    audits = json.loads((REPORT / "context-audit.json").read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    pins = {"constructor": lambda t: BASE.parent / "tasks" / f"task_{t}.py",
            "factory": lambda t: BASE / "direct_factories" / f"task_{t}.py",
            "factory_certificate": lambda t: BASE / "direct_factories" / f"{t}.json",
            "self_tiler_evidence": lambda t: BASE / "self_tiler_evidence.py",
            "colour_evidence": lambda t: BASE / "colour_evidence.py",
            "verified_rules": lambda t: BASE / "verified_rules.py",
            "program_targets": lambda t: BASE / "program_targets.py",
            "prepare_input_orbit": lambda t: BASE / "diversity" / "prepare.py",
            "harness": lambda t: REPORT / "context_audit.py"}
    for tid in FAMILIES:
        for key in (tid, tid + "@min_corner"):
            audit = audits[key]
            assert audit["passed"] and audit["queries_accepted"] == 250
            assert not audit["queries_failed"] and audit["make_record_calls"] == 2000
            for name, path in pins.items():
                assert audit["source_sha256"][name] == sha(path(tid)), (key, name)
