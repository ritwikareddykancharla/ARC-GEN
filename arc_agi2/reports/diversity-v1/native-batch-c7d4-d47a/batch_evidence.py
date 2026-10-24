"""Native batch c7d4/d47a evidence: domains, finite competitors, witnesses, probes.

Read-only measurement; writes only batch-evidence.json beside this file.
Seeded, so two runs give the same counts (only ``seconds`` varies).

For c7d4e6ad and d47aa2ff it records:

* domain statistics of the legacy (base 99def42, sha-pinned bytes) and the
  current default samplers, with archived-checker agreement on every draw;
* per-competitor single-pair classification: how often each rule reproduces
  a label (``fits``) and how often its answer differs from the native answer
  (``differs``). A rule with fits == 0 is refuted by any one demonstration; a
  rule with differs == 0 equals the native answer on every sampled input.
  Only rules with both counts > 0 can make a context ambiguous;
* ungated ambiguity of 3-demonstration + 1-query contexts (identity palette,
  d4 = 0): recertify-style independent draws for legacy and current, plus
  same-shape draws (demos at the query's dimensions, as prepare's uniform/seen
  policy prefers) for current. Survivors are chosen on demonstrations only
  and compared on the query INPUT; the label is used only for the soundness
  assertion that the native rule reproduces it;
* contexts in which a learned colour->colour lookup would lack an entry for a
  query colour (assessed, not gated; see README);
* one witness context per ambiguity-causing rule (first seeded occurrence);
* hand-built off-domain probes showing which competitors a dropped invariant
  would let through;
* finite same-shape capacity: an exact enumeration of every valid c7d4e6ad
  3x3 input (its pair domain is valid but has one input orbit), and sampled
  input-orbit counts at small shapes. Capacity is reported, not used to
  narrow the generator.

Usage (worktree root):
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-c7d4-d47a/batch_evidence.py
"""
import collections
import hashlib
import importlib
import importlib.util
import json
import random
import subprocess
import sys
import time
import types
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from arc_agi2.runtime import BASE, grid, verification_solver

OUT = Path(__file__).resolve().parent
BASE_COMMIT = "99def42"
LEGACY_SHA = {"c7d4e6ad": "6c88d33d0ea07a8a0287037d101dcca94647f3be73cf0a746ab224908705dc04",
              "d47aa2ff": "fd5d1120f720c045ea6668bc1690ef50c035540e87d23f5e6b0a9bb81fd135ea"}
TASKS = ("c7d4e6ad", "d47aa2ff")
DOMAIN_DRAWS = 2000
CONTEXTS = 2000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def competitors():
    spec = importlib.util.spec_from_file_location("batch_c7d4_d47a_competitors",
                                                  OUT / "competitors.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def legacy(tid):
    src = subprocess.run(["git", "show", f"{BASE_COMMIT}:tasks/task_{tid}.py"],
                         capture_output=True, check=True, cwd=BASE.parent).stdout
    if sha(src) != LEGACY_SHA[tid]:
        raise RuntimeError("legacy constructor bytes changed")
    module = types.ModuleType(f"legacy_{tid}")
    exec(compile(src, f"legacy/task_{tid}.py", "exec"), module.__dict__)
    return module


def current(tid):
    return importlib.import_module(f"tasks.task_{tid}")


def draw(module, checker, **kw):
    p = module.generate(**kw)
    p = {k: grid(p[k]) for k in ("input", "output")}
    if grid(checker(p["input"])) != p["output"]:
        raise RuntimeError("archived checker disagrees with constructor label")
    return p


def as_list(g):
    return None if g is None else [list(r) for r in g]


def hist(counter):
    return {str(k): v for k, v in sorted(counter.items())}


# ---------------------------------------------------------------- domains
def c7_features(g):
    legend = [r for r in range(len(g)) if g[r][0]]
    runs = []
    for r in legend:
        if not runs or runs[-1][0] != g[r][0]:
            runs.append([g[r][0], 0])
        runs[-1][1] += 1
    grey = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 5]
    cols = [c for _, c in grey]
    return {"legend_height": len(legend), "colours": len(runs),
            "max_run": max(n for _, n in runs), "min_run": min(n for _, n in runs),
            "top_margin": legend[0], "bottom_margin": len(g) - 1 - legend[-1],
            "grey_left": min(cols), "grey_width": max(cols) - min(cols) + 1,
            "grey_cells": len(grey)}


def d4_features(p):
    g, out = p["input"], p["output"]
    w = (len(g[0]) - 1) // 2
    left = [row[:w] for row in g]
    dots = sum(v != 0 for row in left for v in row)
    colours = len({v for row in left for v in row} - {0})
    gone = [(r, c) for r, row in enumerate(out) for c, v in enumerate(row) if v == 2]
    movers = len(gone)
    right = [row[w + 1:] for row in g]
    steps = []
    for r0, c0 in gone:
        colour = left[r0][c0]
        (r1, c1), = [(r, c) for r, row in enumerate(out) for c, v in enumerate(row)
                     if v == 1 and right[r][c] == colour]
        steps.append((r1 - r0, c1 - c0))
    return {"panel_height": len(g), "panel_width": w, "dots": dots, "colours": colours,
            "movers": movers, "stationary": dots - movers,
            "chebyshev": [max(abs(a), abs(b)) for a, b in steps],
            "knight": sum(1 for a, b in steps if a and b and abs(a) != abs(b))}


def domain_stats(tid, module, seed):
    checker = verification_solver(tid)
    random.seed(seed)
    shapes, inputs = set(), set()
    hists = collections.defaultdict(collections.Counter)
    ranges = collections.defaultdict(lambda: [10 ** 9, -1])
    for _ in range(DOMAIN_DRAWS):
        p = draw(module, checker)
        g = p["input"]
        shapes.add((len(g), len(g[0])))
        inputs.add(json.dumps(g))
        feats = c7_features(g) if tid == "c7d4e6ad" else d4_features(p)
        for k, v in feats.items():
            values = v if isinstance(v, list) else [v]
            for x in values:
                lo_hi = ranges[k]
                lo_hi[0], lo_hi[1] = min(lo_hi[0], x), max(lo_hi[1], x)
                if k not in ("grey_cells",):
                    hists[k][x] += 1
    stats = {"draws": DOMAIN_DRAWS, "archived_checker_agreement": DOMAIN_DRAWS,
             "distinct_inputs": len(inputs), "input_shapes": len(shapes),
             "input_height_range": [min(s[0] for s in shapes), max(s[0] for s in shapes)],
             "input_width_range": [min(s[1] for s in shapes), max(s[1] for s in shapes)],
             "ranges": {k: v for k, v in sorted(ranges.items())}}
    keep = (("legend_height", "colours", "max_run", "top_margin", "bottom_margin",
             "grey_left", "grey_width") if tid == "c7d4e6ad" else
            ("panel_height", "panel_width", "dots", "colours", "movers", "stationary",
             "chebyshev", "knight"))
    stats["histograms"] = {k: hist(hists[k]) for k in keep}
    return stats


# ------------------------------------------------- competing hypotheses
def classify(tid, module, seed, comp):
    """Single-pair fits/differs per rule on the default domain."""
    checker = verification_solver(tid)
    random.seed(seed)
    fits, differs = collections.Counter(), collections.Counter()
    for _ in range(DOMAIN_DRAWS):
        p = draw(module, checker)
        opts = comp.answers(tid, p["input"])
        native = opts[comp.NATIVE[tid]]
        if as_list(native) != p["output"]:
            raise RuntimeError("native rule disagrees with the label")
        for name, ans in opts.items():
            fits[name] += ans is not None and as_list(ans) == p["output"]
            differs[name] += ans != native
    out = {}
    for name in comp.RULES[tid]:
        kind = ("native" if name == comp.NATIVE[tid] else
                "refuted_by_any_demo" if fits[name] == 0 else
                "identical_on_domain" if differs[name] == 0 else "separable")
        out[name] = {"fits": fits[name], "differs": differs[name], "class": kind}
    return out


def ambiguity(tid, module, seed, same_shape, comp):
    checker = verification_solver(tid)
    native = comp.NATIVE[tid]
    random.seed(seed)
    amb, by_rule, witnesses, lookup = 0, collections.Counter(), {}, 0
    survivor_sets = collections.Counter()
    for n in range(CONTEXTS):
        query = draw(module, checker)
        kw = {}
        if same_shape:
            g = query["input"]
            kw = ({"height": len(g), "width": len(g[0])} if tid == "c7d4e6ad"
                  else {"height": len(g), "width": (len(g[0]) - 1) // 2})
        demos = [draw(module, checker, **kw) for _ in range(3)]
        alive = comp.surviving(tid, demos)
        if native not in alive:
            raise RuntimeError("native rule does not fit native demonstrations")
        survivor_sets[len(alive)] += 1
        opts = comp.answers(tid, query["input"])
        if as_list(opts[native]) != query["output"]:
            raise RuntimeError("native rule disagrees with the label")
        wrong = sorted(i for i in alive if opts[i] != opts[native])
        amb += bool(wrong)
        by_rule.update(wrong)
        lookup += bool(comp.unseen_lookup_colours(tid, demos, query["input"]))
        for name in wrong:
            witnesses.setdefault(name, {
                "context": n, "rule": name, "demonstrations": demos,
                "query_input": query["input"], "native_answer": query["output"],
                "competitor_answer": as_list(opts[name])})
    return {"contexts": CONTEXTS, "context_kind": "same_shape" if same_shape else "independent",
            "palette": "identity", "d4": 0, "ambiguous_contexts": amb,
            "by_rule_contexts": dict(sorted(by_rule.items())),
            "surviving_rule_count_histogram": hist(survivor_sets),
            "learned_lookup_unseen_query_colour_contexts": lookup}, witnesses


# ------------------------------------------------------ off-domain probes
def _c7_grid(h, w, legend, grey):
    g = [[0] * w for _ in range(h)]
    for r, colour in legend.items():
        g[r][0] = colour
    for r, c in grey:
        g[r][c] = 5
    return g


def _d4_grid(h, w, left, right):
    g = [[0] * (2 * w + 1) for _ in range(h)]
    for r in range(h):
        g[r][w] = 5
    for (r, c), colour in left.items():
        g[r][c] = colour
    for (r, c), colour in right.items():
        g[r][w + 1 + c] = colour
    return g


def probes(comp):
    """Off-domain inputs (each breaks ONE preserved invariant) and their readings."""
    c7, d4 = "c7d4e6ad", "d47aa2ff"
    valid_c7 = _c7_grid(6, 6, {1: 3, 2: 3, 3: 4, 4: 4},
                        [(1, 3), (2, 3), (3, 3), (3, 4), (4, 4)])
    valid_d4 = _d4_grid(5, 5, {(0, 0): 3, (2, 3): 4, (4, 1): 3},
                        {(0, 0): 3, (2, 3): 4, (3, 1): 3})
    cases = {
        "c7d4e6ad:grey_row_outside_legend": (c7, None, _c7_grid(
            6, 5, {1: 3, 2: 4}, [(1, 3), (2, 3), (3, 3)])),
        "c7d4e6ad:legend_row_without_grey": (c7, None, _c7_grid(
            6, 5, {1: 3, 2: 3, 3: 4}, [(1, 3), (2, 3)])),
        "c7d4e6ad:single_colour_legend_demo": (c7, _c7_grid(
            5, 5, {1: 3, 2: 3}, [(1, 3), (2, 3)]), valid_c7),
        "d47aa2ff:no_stationary_dot_demo": (d4, _d4_grid(
            5, 5, {(1, 1): 3}, {(2, 1): 3}), valid_d4),
        "d47aa2ff:two_movers_same_colour": (d4, None, _d4_grid(
            5, 5, {(0, 0): 3, (0, 3): 3, (4, 4): 4}, {(1, 0): 3, (1, 3): 3, (4, 4): 4})),
    }
    report = {}
    for name, (tid, demo_input, query_input) in cases.items():
        opts = comp.answers(tid, query_input)
        native = opts[comp.NATIVE[tid]]
        entry = {"query_input": query_input,
                 "rules_differing_from_native": sorted(k for k, v in opts.items() if v != native)}
        if demo_input is not None:
            demo = {"input": demo_input, "output": as_list(comp.answers(tid, demo_input)[comp.NATIVE[tid]])}
            alive = comp.surviving(tid, [demo] * 3)
            entry.update(demo=demo, survivors_of_demo=sorted(alive),
                         ambiguous_with_three_copies=comp.ambiguous(tid, [demo] * 3, query_input))
        report[name] = entry
    return report


SMALL_SHAPES = {"c7d4e6ad": ((3, 3), (3, 4), (4, 3), (4, 4), (3, 30), (30, 3)),
                "d47aa2ff": ((3, 3), (3, 4), (4, 3), (4, 4))}
CAPACITY_DRAWS = 3000


def capacity():
    from itertools import product
    from arc_agi2.diversity.prepare import input_orbit
    c7, d4 = current("c7d4e6ad"), current("d47aa2ff")
    valid, orbits = 0, set()
    legend_values = (0, 1, 2, 3, 4, 6, 7, 8, 9)
    for col0 in product(legend_values, repeat=3):
        for rest in product((0, 5), repeat=6):
            g = [[col0[r], rest[2 * r], rest[2 * r + 1]] for r in range(3)]
            try:
                c7.check_scene(g)
            except ValueError:
                continue
            valid += 1
            orbits.add(input_orbit(g))
    out = {"c7d4e6ad_3x3_exact": {
        "candidates_enumerated": len(legend_values) ** 3 * 2 ** 6,
        "valid_inputs": valid, "input_orbits": len(orbits),
        "method": "all column-0 values in {0,1,2,3,4,6,7,8,9} x all {0,5} cells "
                  "elsewhere, filtered by the constructor's check_scene"},
        "sampled_orbits": {}, "capacity_draws": CAPACITY_DRAWS}
    for tid, module in (("c7d4e6ad", c7), ("d47aa2ff", d4)):
        for h, w in SMALL_SHAPES[tid]:
            random.seed(int(sha(f"capacity:{tid}:{h}x{w}".encode())[:12], 16))
            seen = {input_orbit(module.generate(height=h, width=w)["input"])
                    for _ in range(CAPACITY_DRAWS)}
            out["sampled_orbits"][f"{tid}@{h}x{w}"] = len(seen)
    return out


def family(tid):
    comp = competitors()
    k = TASKS.index(tid)
    fam = {"domain": {}, "competitors": {}, "ambiguity": {}, "witnesses": {}}
    for j, (label, module) in enumerate((("legacy", legacy(tid)), ("current", current(tid)))):
        fam["domain"][label] = domain_stats(tid, module, 1000 + 10 * k + j)
        fam["competitors"][label] = classify(tid, module, 3000 + 10 * k + j, comp)
        for same in ([False, True] if label == "current" else [False]):
            rep, wit = ambiguity(tid, module, 2000 + 10 * k + j + 5 * same, same, comp)
            fam["ambiguity"][label + ("@same_shape" if same else "")] = rep
            for key, w in wit.items():
                fam["witnesses"].setdefault(key, dict(w, domain=label + ("@same_shape" if same else "")))
    return tid, fam


def main():
    started = time.monotonic()
    files = {"constructor_c7d4e6ad": BASE.parent / "tasks/task_c7d4e6ad.py",
             "constructor_d47aa2ff": BASE.parent / "tasks/task_d47aa2ff.py",
             "factory_c7d4e6ad": BASE / "direct_factories/task_c7d4e6ad.py",
             "factory_d47aa2ff": BASE / "direct_factories/task_d47aa2ff.py",
             "factory_certificate_c7d4e6ad": BASE / "direct_factories/c7d4e6ad.json",
             "factory_certificate_d47aa2ff": BASE / "direct_factories/d47aa2ff.json",
             "dot_motion_d47aa2ff_evidence": BASE / "dot_motion_d47aa2ff_evidence.py",
             "colour_evidence": BASE / "colour_evidence.py",
             "verified_rules": BASE / "verified_rules.py",
             "competitors": OUT / "competitors.py",
             "harness": Path(__file__)}
    comp = competitors()
    out = {"base_commit": BASE_COMMIT, "legacy_constructor_sha256": LEGACY_SHA,
           "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()},
           "rule_counts": {t: len(comp.RULES[t]) for t in TASKS},
           "probes": probes(comp), "capacity": capacity(), "families": {}}
    with ProcessPoolExecutor(max_workers=2) as pool:
        for tid, fam in pool.map(family, TASKS):
            out["families"][tid] = fam
    out["seconds"] = round(time.monotonic() - started, 1)
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    if "--no-write" not in sys.argv:
        (OUT / "batch-evidence.json").write_text(text)
    for tid, fam in out["families"].items():
        print(tid, json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "histograms"}
                               for k, v in fam["domain"].items()}))
        print(tid, json.dumps({k: {n: c["class"] for n, c in v.items()}
                               for k, v in fam["competitors"].items()}))
        print(tid, json.dumps(fam["ambiguity"]))
        print(tid, "witnesses:", sorted(fam["witnesses"]))
    print(json.dumps(out["capacity"]))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("query_input", "demo")}
                      for k, v in out["probes"].items()}, indent=1))


if __name__ == "__main__":
    main()
