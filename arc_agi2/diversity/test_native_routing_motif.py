"""Focused tests for the 7491f3cf rectangular and 98c475bf width expansions.

Report: arc_agi2/reports/diversity-v1/native-routing-motif-20261025/.
"""
import hashlib
import importlib.util
import json
import random
import subprocess
import types
from collections import Counter
from pathlib import Path
from unittest import mock

import pytest

from arc_agi2.colour_evidence import MissingColourEvidence, require_colour_evidence
from arc_agi2.direct_certificates import certified_factory_source
from arc_agi2.direct_factories import task_7491f3cf as factory7491
from arc_agi2.direct_factories import task_98c475bf as factory98
from arc_agi2.line_motif_evidence import solve_visible_motifs
from arc_agi2.runtime import BASE, call, grid, reference, verification_solver
from tasks import task_7491f3cf as route
from tasks import task_98c475bf as motif

LEGACY = "99def42"
REPORT = BASE / "reports/diversity-v1/native-routing-motif-20261025"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def legacy(tid):
    text = subprocess.run(["git", "show", f"{LEGACY}:tasks/task_{tid}.py"], check=True,
                          capture_output=True, text=True, cwd=BASE.parent).stdout
    module = types.ModuleType("legacy_" + tid)
    exec(compile(text, "legacy", "exec"), module.__dict__)
    return module


def program(module, d4=0, palette=None):
    ns = {}
    exec(module.build_program(d4, list(range(10)) if palette is None else palette), ns)
    return ns["solve"]


# ------------------------------------------------------------------ 7491f3cf
def decode(g):
    """Latents of a 7491f3cf input read back from the grid."""
    h, w = len(g) - 2, (len(g[0]) - 5) // 4
    panels = [[row[1 + k * (w + 1):1 + k * (w + 1) + w] for row in g[1:1 + h]] for k in range(4)]
    counts = Counter(v for p in panels[:3] for row in p for v in row)
    (bg, top), (_, second) = counts.most_common(2)
    ink = [{(r, c) for r in range(h) for c in range(w) if p[r][c] != bg} for p in panels]

    def comps(cells, diag):
        cells, out = set(cells), []
        steps = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (1, -1), (-1, 1), (-1, -1)] if diag else [])
        while cells:
            stack = [cells.pop()]
            comp = set(stack)
            while stack:
                y, x = stack.pop()
                for dy, dx in steps:
                    if (y + dy, x + dx) in cells:
                        cells.discard((y + dy, x + dx))
                        comp.add((y + dy, x + dx))
                        stack.append((y + dy, x + dx))
            out.append(comp)
        return out

    parts = sorted(comps(ink[0], True), key=len, reverse=True)
    return dict(h=h, w=w, bg=bg, strict_fill=top > second, wall=parts[0], dots=parts[1:],
                regions=comps({(r, c) for r in range(h) for c in range(w)} - parts[0], False),
                p2=ink[1], p3=ink[2])


def test_7491_canonical_replay():
    fixture = reference("7491f3cf")["canonical"]
    replay = route.validate()
    assert replay["train"] == fixture["train"] and replay["test"] == fixture["test"]


def test_7491_explicit_legacy_panel_size_replay_is_byte_identical():
    old = legacy("7491f3cf")
    for seed in range(40):
        for kw in ({"panel_size": 4}, {"panel_size": 5, "wall_evidence": True},
                   {"panel_size": 6, "wall_evidence": False},
                   {"panel_size": 4, "pattern2": ["####", "#..#", "#..#", "####"]}):
            random.seed(seed)
            a = old.generate(**kw)
            random.seed(seed)
            assert route.generate(**kw) == a, (seed, kw)


@pytest.mark.parametrize("kw", [
    {"panel_size": 3}, {"panel_size": 7}, {"panel_size": True}, {"panel_size": 5.0},
    {"panel_height": 2, "panel_width": 4}, {"panel_height": 29}, {"panel_width": 7},
    {"panel_width": 2}, {"panel_height": "5"},
    {"panel_size": 5, "panel_height": 6}, {"panel_size": 5, "panel_width": 4},
    {"panel_height": 7, "pattern2": ["#..", ".#.", "..#"]},
    {"pattern2": ["#...", ".#."]},
    {"panel_height": 4, "panel_width": 4, "line": [(0, 5), (1, 5)]},
    {"panel_width": 6, "dot": (0, 6)},
])
def test_7491_argument_validation(kw):
    with pytest.raises(ValueError):
        route.generate(**kw)


def test_7491_3x3_exclusion_is_scoped_to_the_two_cell_guard():
    with pytest.raises(ValueError, match="two-cells-per-region"):
        route.generate(panel_height=3, panel_width=3)
    assert (3, 3) not in route.SHAPES and len(route.SHAPES) == 4 * 26 - 1
    cells = [(r, c) for r in range(3) for c in range(3)]
    counts = Counter()
    for mask in range(1, 512):
        wall = {cells[i] for i in range(9) if mask >> i & 1}
        if len(wall) < 2 or not route._connected8(wall) or len(route._regions(3, 3, wall)) != 2:
            continue
        dot = any(not route._near(c, wall) for reg in route._regions(3, 3, wall) for c in reg)
        guarded = route._wall_regions(3, 3, wall) is not None
        counts.update(two=1, two_dot=dot, guarded=guarded, guarded_dot=guarded and dot)
    assert counts == Counter(two=192, two_dot=16, guarded=40)
    # Supervisor counterexample: valid without the guard, excluded by it.
    wall = {(0, 2), (1, 2), (2, 1), (2, 0)}
    assert sorted(map(len, route._regions(3, 3, wall))) == [1, 4]
    assert not route._near((0, 0), wall) and route._wall_regions(3, 3, wall) is None
    assert "two cells" in route.__doc__ and "not a geometric" in route.__doc__


@pytest.mark.parametrize("shape", [(3, 4), (3, 6), (4, 3), (28, 3), (28, 6), (5, 5), (10, 4)])
def test_7491_rectangular_shapes_and_preserved_scene_semantics(shape):
    h, w = shape
    checker = verification_solver("7491f3cf")
    solve = program(factory7491)
    for seed in range(12):
        random.seed(1000 * h + 10 * w + seed)
        evidence = seed % 2 == 0
        pair = route.generate(panel_height=h, panel_width=w, wall_evidence=evidence)
        g = pair["input"]
        assert (len(g), len(g[0])) == (h + 2, 4 * w + 5)
        d = decode(g)
        wall, (dot,) = d["wall"], [next(iter(x)) for x in d["dots"]]
        assert d["strict_fill"] and len(d["dots"]) == 1 and len(d["dots"][0]) == 1
        assert route._connected8(wall) and len(d["regions"]) == 2
        assert min(map(len, d["regions"])) >= 2 and not route._near(dot, wall)
        dreg = next(r for r in d["regions"] if dot in r)
        other = next(r for r in d["regions"] if dot not in r)
        assert dreg & d["p2"] and other & d["p3"] and d["p2"] != d["p3"]
        if evidence:
            assert wall & d["p2"] & d["p3"] and wall & (d["p3"] - d["p2"])
        out = pair["output"]
        o4 = 1 + 3 * (w + 1)
        v2 = lambda q: g[1 + q[0]][1 + (w + 1) + q[1]]  # noqa: E731
        v3 = lambda q: g[1 + q[0]][1 + 2 * (w + 1) + q[1]]  # noqa: E731
        routed = {q: out[1 + q[0]][o4 + q[1]] for q in dreg | other | wall}
        over2 = {q: v2(q) if q in d["p2"] else v3(q) for q in routed}
        over3 = {q: v3(q) if q in d["p3"] else v2(q) for q in routed}
        assert routed != over2 and routed != over3
        assert grid(call(checker, g)) == out and solve([], g) == out


def test_7491_default_axes_and_kind_coverage():
    seen_aspect, kinds, axes, patterns = Counter(), Counter(), Counter(), Counter()
    line, pattern = route._sample_line, route._sample_pattern
    log = []

    def spy_line(h, w):
        result = line(h, w)
        log.append(("line", result[0]))
        return result

    def spy_pattern(h, w):
        result = pattern(h, w)
        log.append(("pattern", result[0]))
        return result

    with mock.patch.object(route, "_sample_line", spy_line), \
            mock.patch.object(route, "_sample_pattern", spy_pattern):
        for seed in range(400):
            random.seed(77000 + seed)
            log.clear()
            g = route.generate()["input"]
            h, w = len(g) - 2, (len(g[0]) - 5) // 4
            seen_aspect["square" if h == w else "tall" if h > w else "wide"] += 1
            if h != w:
                kinds[[k for t, k in log if t == "line"][-1]] += 1
                patterns.update(k for t, k in log[-2:])
                wall = decode(g)["wall"]
                if len({r for r, _ in wall}) == 1:
                    axes["row"] += 1
                if len({c for _, c in wall}) == 1:
                    axes["column"] += 1
    assert set(seen_aspect) == {"square", "tall", "wide"}
    assert set(kinds) == {"straight", "diagonal", "ell", "path"}
    assert set(axes) == {"row", "column"}
    assert set(patterns) == {"x", "plus", "checker", "blocks", "ells", "stripes", "ring",
                             "diamond", "sym", "random"}
    assert abs(sum(route.DEFAULT_SHAPE_WEIGHTS.values()) - 1) < 1e-12


def test_7491_bounded_failure_keeps_requested_shape():
    shapes = []

    def never(h, w):
        shapes.append((h, w))
        return "straight", {(0, 0)}

    with mock.patch.object(route, "_sample_line", never):
        with pytest.raises(RuntimeError, match=r"3x4-panel .* within 400 tries"):
            route.generate(panel_height=3, panel_width=4)
        with pytest.raises(RuntimeError):
            route.generate()
    assert shapes[:route.MAX_TRIES] == [(3, 4)] * route.MAX_TRIES
    # A default call draws its shape once and keeps it for every retry.
    assert len(shapes) == 2 * route.MAX_TRIES and len(set(shapes[route.MAX_TRIES:])) == 1


# ------------------------------------------------------------------ 98c475bf
def test_98_canonical_and_legacy_height_pinned_replay():
    fixture = reference("98c475bf")["canonical"]
    replay = motif.validate()
    assert replay["train"] == fixture["train"] and replay["test"] == fixture["test"]
    old = legacy("98c475bf")
    for seed in range(40):
        for kw in ({"height": 20}, {"height": 22, "num_markers": 4},
                   {"height": 30, "marker_colours": [3, 7]}):
            random.seed(seed)
            a = old.generate(**kw)
            random.seed(seed)
            assert motif.generate(**kw) == a


def test_98_width_axis_and_argument_validation():
    assert motif.MIN_WIDTH == 18 == max(x for d, _ in motif.MOTIFS.values() for _, x in d) + 2
    for bad in (17, 31, True, "20", 20.0):
        with pytest.raises(ValueError):
            motif.generate(width=bad)
    for width in (18, 30):
        random.seed(width)
        p = motif.generate(width=width, height=12)
        assert (len(p["input"]), len(p["input"][0])) == (12, width)
    random.seed(5)
    assert len(motif.generate(height=17)["input"][0]) == motif.WIDTH == 20
    widths = set()
    for seed in range(200):
        random.seed(seed)
        widths.add(len(motif.generate()["input"][0]))
    assert widths == set(range(18, 31))


def test_98_absolute_decorations_and_fixed_table_at_other_widths():
    for width in (18, 26, 30):
        p = motif.generate(border=9, line_color=2, line_row=3, markers=[(12, 1), (18, 6)],
                           height=24, width=width)
        out = p["output"]
        for row, colour in ((12, 1), (18, 6)):
            deco, gaps = motif.MOTIFS[colour]
            expected = {(row, x) for x in range(1, width - 1) if x not in gaps}
            expected |= {(row + dy, x) for dy, x in deco}
            got = {(r, x) for r in range(24) for x in range(1, width - 1) if out[r][x] == colour}
            assert got == expected
        assert all(row[0] == row[-1] == 9 for row in out)


def test_98_errors_separate_invalid_arguments_from_bounded_exhaustion():
    with pytest.raises(RuntimeError, match=r"26-wide scene of height 12 .* within 500 tries"):
        random.seed(1)
        motif.generate(height=12, line_color=6, line_row=2, num_markers=2, width=26)
    with pytest.raises(ValueError, match="no row fits"):
        motif.generate(height=12, line_color=6, markers=[(2, 7), (8, 2)])
    with pytest.raises(ValueError):
        motif.generate(height=21, num_markers=4)


def same_width_episode(width, seed):
    random.seed(seed)
    query = motif.generate(height=20, width=width, marker_colours=[3])
    demos = [motif.generate(height=20, width=width, line_color=3, marker_colours=[c])
             for c in (1, 2, 7)]
    return demos, query


def test_98_gate_accepts_same_width_and_refuses_cross_width_and_missing_motif():
    for width in (18, 24, 30):
        demos, query = same_width_episode(width, 4000 + width)
        require_colour_evidence("98c475bf", demos, [{"input": query["input"]}], list(range(10)), 0)
        assert solve_visible_motifs(demos, query["input"], 0) == query["output"]
        assert program(factory98)(demos, query["input"]) == query["output"]
        other = 20 if width != 20 else 24
        wrong = [motif.generate(height=20, width=other, line_color=3) for _ in range(3)]
        with pytest.raises(MissingColourEvidence):
            require_colour_evidence("98c475bf", wrong, [{"input": query["input"]}], list(range(10)), 0)
        with pytest.raises(ValueError):
            program(factory98)(wrong, query["input"])
        unshown = [motif.generate(height=20, width=width, line_color=1, marker_colours=[2])
                   for _ in range(3)]
        with pytest.raises(MissingColourEvidence):
            require_colour_evidence("98c475bf", unshown, [{"input": query["input"]}], list(range(10)), 0)


# ------------------------------------------------------------ certificates
def load_adapter():
    spec = importlib.util.spec_from_file_location("certify_98c475bf", REPORT / "certify_98c475bf.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("tid", ["7491f3cf", "98c475bf"])
def test_records_are_bound_to_current_bytes_and_keep_history(tid):
    record = json.loads((BASE / "direct_factories" / f"{tid}.json").read_text())
    mirror = json.loads((BASE / "reports/diversity-v1/native-certificates" / f"{tid}.json").read_text())
    assert record == mirror and record["passed"] is True
    assert record["constructor_sha256"] == sha((BASE.parent / "tasks" / f"task_{tid}.py").read_bytes())
    assert record["factory_sha256"] == sha((BASE / "direct_factories" / f"task_{tid}.py").read_bytes())
    assert (record["fresh_pairs_checked"], record["augmented_pair_checks"],
            record["fixture_variants_checked"]) == (1000, 8000, 16)
    assert all(certified_factory_source(tid, d4, list(range(10))) for d4 in range(8))
    old = json.loads(subprocess.run(["git", "show", f"{LEGACY}:arc_agi2/direct_factories/{tid}.json"],
                                    check=True, capture_output=True, text=True,
                                    cwd=BASE.parent).stdout)
    assert record["provenance"] == old["provenance"] and record["draft_notes"] == old["draft_notes"]
    assert record["draft_notes_status"].startswith("historical")
    assert record["previous_certificate"]["constructor_sha256"] == old["constructor_sha256"]
    assert record["previous_certificate"]["status"].startswith("superseded")


def test_98_dedicated_certificate_counts_and_hash_pins():
    record = json.loads((BASE / "direct_factories" / "98c475bf.json").read_text())
    adapter = load_adapter()
    for name, path in adapter.PINNED.items():
        assert record["source_sha256"][name] == sha(path.read_bytes()), name
    assert record["adapter_sha256"] == sha((REPORT / "certify_98c475bf.py").read_bytes())
    assert record["queries_requested"] == record["queries_accepted"] == 1000
    assert record["fresh_pairs_checked"] == 1000 and not record["queries_failed"]
    assert record["distinct_episode_identities"] == 1000 == record["unique_base_inputs"]
    assert record["augmented_demo_pair_checks"] == 24000 == 8 * record["accepted_demo_pairs"]
    rejected = sum(record["rejected_context_draws"].values())
    assert rejected == record["context_retries"]
    cross = record["cross_width_negative_control"]
    assert cross["gate_refused"] == cross["factory_raised"] == cross["pairs"] == 20
    exhausted = record["rejected_context_draws"].get("sampler_exhausted", 0)
    assert record["demo_pair_draws"] == 3 * (1000 + rejected - exhausted)
    assert record["pair_labels_verified"] == 1000 + record["demo_pair_draws"] + 3 * cross["pairs"]
    standard = json.loads((REPORT / "standard-recertify-98c475bf.json").read_text())
    assert standard["passed"] is False and "error" in standard
    assert standard["constructor_sha256"] == record["constructor_sha256"]


def test_98_adapter_holds_queries_fixed_and_never_reads_labels_to_select():
    adapter = load_adapter()
    report = adapter.audit_domain({"height": 14, "width": 18}, 3, "unit-test")
    assert report["queries_accepted"] == 3 and not report["queries_failed"]
    assert report["query_widths"] == {"18": 3} and report["unique_query_raw_inputs"] == 3
    with mock.patch.object(adapter, "require_colour_evidence",
                           side_effect=MissingColourEvidence("forced")):
        report = adapter.audit_domain({"height": 14, "width": 18}, 2, "unit-test-refused")
    assert report["queries_accepted"] == 0 and len(report["queries_failed"]) == 2
    # Failed queries are listed, never replaced; every context was rejected.
    assert report["context_retries"] == 0 and report["queries_requested"] == 2
    assert sum(report["rejected_context_draws"].values()) == 2 * adapter.MAX_CONTEXTS
