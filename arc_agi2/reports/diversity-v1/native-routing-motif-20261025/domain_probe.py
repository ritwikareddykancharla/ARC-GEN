"""Before/after default-domain measurement for 7491f3cf and 98c475bf.

Deterministic and source-pinned. The legacy constructors are loaded from git
blobs at LEGACY_COMMIT (never copied into the tree); the current constructors
are the working files. Every source sha256 is recorded with the output.

For each family and version, N default generate() calls are made under fixed
seeds. Exceptions are counted by type and never skipped silently. Scene
statistics are read back from the grids by one decoder used for both
versions, plus the latent draw kinds observed by wrapping the constructor's
own samplers (the wrappers do not change the random stream).

Sections:
  * shapes/aspects/canvas sizes, unique raw inputs and D4/palette orbits;
  * 7491f3cf: wall kinds (all four, and row/column straight walls), pattern
    kinds, wall lengths, pattern sizes, dot placement, wall-evidence share,
    ink density;
  * 98c475bf: widths, heights, marker counts, line/marker colours, line row
    placement, ink density;
  * same-shape support: prepare.query_support (read-only import) on a pool of
    the first POOL draws, as in the uniform/seen policy, and for 98c475bf the
    stricter input-only motif-coverage condition the evidence gate needs;
  * 7491f3cf feasibility: exhaustive wall/dot enumeration for 3x3, 3x4 and
    4x3, with and without the retained two-cells-per-region guard (the 3x3
    exclusion holds only under that guard), and per-shape acceptance with wall evidence required for every
    allowed shape (bounded; RuntimeError counted).

Run from the worktree root:
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-routing-motif-20261025/domain_probe.py
"""
import hashlib
import json
import math
import random
import statistics
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path

from arc_agi2.diversity.prepare import input_orbit, query_support
from arc_agi2.episode_shape_policy import profile_from_task
from arc_agi2.runtime import BASE, reference

LEGACY_COMMIT = "99def42"
N = 2000
POOL = 560          # prepare target pool for --train 200 --validation 20
ACCEPT_CALLS = 60   # per shape, wall evidence required
OUT = Path(__file__).resolve().parent / "domain-measurements.json"
TASKS = ("7491f3cf", "98c475bf")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("routing-motif-domain",) + parts)).encode())[:12], 16)


def load(tid, version):
    path = f"tasks/task_{tid}.py"
    if version == "before":
        text = subprocess.run(["git", "show", f"{LEGACY_COMMIT}:{path}"], check=True,
                              capture_output=True, text=True, cwd=BASE.parent).stdout
    else:
        text = (BASE.parent / path).read_text()
    module = types.ModuleType(f"probe_{tid}_{version}")
    module.__file__ = path
    exec(compile(text, f"{version}/{path}", "exec"), module.__dict__)
    return module, sha(text.encode())


# ----------------------------------------------------------------- decoders
def comps(cells, diag):
    cells, out = set(cells), []
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    while cells:
        stack = [cells.pop()]
        comp = set(stack)
        while stack:
            y, x = stack.pop()
            for dy, dx in steps:
                q = (y + dy, x + dx)
                if q in cells:
                    cells.discard(q)
                    comp.add(q)
                    stack.append(q)
        out.append(comp)
    return out


def decode_7491(g):
    h, w = len(g) - 2, (len(g[0]) - 5) // 4
    panels = [[row[1 + k * (w + 1):1 + k * (w + 1) + w] for row in g[1:1 + h]]
              for k in range(4)]
    bg = Counter(v for p in panels[:3] for row in p for v in row).most_common(1)[0][0]
    ink = [{(r, c) for r in range(h) for c in range(w) if p[r][c] != bg} for p in panels]
    parts = sorted(comps(ink[0], True), key=len, reverse=True)
    wall, dot = parts[0], set().union(*parts[1:])
    regions = comps({(r, c) for r in range(h) for c in range(w)} - wall, False)
    dreg = next(r for r in regions if r & dot)
    p2, p3 = ink[1], ink[2]
    straight = ("row" if len({r for r, _ in wall}) == 1 else
                "column" if len({c for _, c in wall}) == 1 else None)
    (dy, dx), = dot
    return {
        "shape": (h, w), "wall": len(wall), "straight_axis": straight,
        "dot_region_share": len(dreg) / (h * w - len(wall)),
        "dot_on_edge": dy in (0, h - 1) or dx in (0, w - 1),
        "dot": (dy, dx), "p2": len(p2), "p3": len(p3),
        "evidence": bool(wall & p2 & p3) and bool(wall & (p3 - p2)),
        "density": (len(ink[0]) + len(p2) + len(p3)) / (3 * h * w),
    }


def decode_98(pair):
    g = pair["input"]
    h, w = len(g), len(g[0])
    markers = [(y, g[y][1]) for y in range(h) if g[y][1] != 0 and g[y][1] == g[y][w - 2]
               and all(v == 0 for v in g[y][2:w - 2])]
    lines = [(y, g[y][1]) for y in range(h) if g[y][1] != 0 and g[y][1] == g[y][w - 2]
             and any(v == g[y][1] for v in g[y][2:w - 2])]
    (line_row, line_colour), = lines
    ink = sum(v != 0 for row in pair["output"] for v in row[1:w - 1])
    return {"shape": (h, w), "markers": markers, "line_row": line_row,
            "line_colour": line_colour, "border": g[0][0],
            "output_density": ink / (h * (w - 2))}


# ------------------------------------------------------------------ helpers
def hist(values):
    return {str(k): v for k, v in sorted(Counter(values).items(), key=lambda kv: str(kv[0]))}


def summary(xs):
    return {"min": min(xs), "median": statistics.median(xs), "mean": round(statistics.fmean(xs), 4),
            "max": max(xs)}


def aspect(shape):
    h, w = shape
    return "square" if h == w else "tall" if h > w else "wide"


def wrap_kinds(module, version, log):
    """Record draw kinds without changing the random stream."""
    line, pattern = module._sample_line, module._sample_pattern
    if version == "after":
        def line_w(h, w):
            kind, cells = line(h, w)
            log["line"].append(kind)
            return kind, cells

        def pattern_w(h, w):
            kind, cells = pattern(h, w)
            log["pattern"].append(kind)
            return kind, cells
    else:
        def line_w(n):
            state = random.getstate()
            log["line"].append(random.choices(['straight', 'diagonal', 'ell', 'path'],
                                              weights=[2, 1, 3, 4])[0])
            random.setstate(state)
            return line(n)

        def pattern_w(n):
            state = random.getstate()
            log["pattern"].append(random.choice(['x', 'plus', 'checker', 'blocks', 'ells', 'stripes',
                                                 'ring', 'diamond', 'sym', 'sym', 'random']))
            random.setstate(state)
            return pattern(n)
    module._sample_line, module._sample_pattern = line_w, pattern_w


def support(tid, pairs, coverage):
    pool = [{"input": p["input"], "id": input_orbit(p["input"])} for p in pairs]
    profile = profile_from_task(reference(tid)["canonical"])
    feasible = query_support(pool, profile, "id")
    rows = sum(len(v) for v in feasible.values())
    out = {"pool_rows": len(pool), "pool_identities": len({p["id"] for p in pool}),
           "shape_bins": len({(len(p["input"]), len(p["input"][0])) for p in pool}),
           "strict_shape_feasible_query_rows": rows,
           "strict_shape_feasible_share": round(rows / len(pool), 4),
           "largest_shape_bin": max(Counter((len(p["input"]), len(p["input"][0]))
                                            for p in pool).values())}
    if coverage:
        # 98c475bf: a query marker colour needs a same-shape demonstration
        # showing its full line (input line colour or output marker colours).
        by_shape = {}
        for p, d in zip(pool, pairs):
            info = decode_98(d)
            shown = {info["line_colour"]} | {c for _, c in info["markers"]}
            by_shape.setdefault(info["shape"], []).append((p["id"], shown))
        covered = 0
        for p, d in zip(pool, pairs):
            info = decode_98(d)
            others = [s for i, s in by_shape[info["shape"]] if i != p["id"]]
            need = {c for _, c in info["markers"]}
            if len(others) >= 3 and need <= set().union(*others):
                covered += 1
        out["motif_coverage_feasible_query_rows"] = covered
        out["motif_coverage_feasible_share"] = round(covered / len(pool), 4)
    return out


# ------------------------------------------------------------------- domains
def measure(tid, version):
    module, source_sha = load(tid, version)
    log = {"line": [], "pattern": []}
    if tid == "7491f3cf":
        wrap_kinds(module, version, log)
    pairs, errors, wall_kinds, pattern_kinds = [], Counter(), [], Counter()
    for i in range(N):
        random.seed(seed_of(tid, "default", i))
        log["line"].clear()
        log["pattern"].clear()
        try:
            pair = module.generate()
        except Exception as exc:  # noqa: BLE001 - counted, never skipped silently
            errors[type(exc).__name__] += 1
            continue
        pairs.append(pair)
        if tid == "7491f3cf":
            # The accepted scene used the last wall and the last two patterns.
            wall_kinds.append(log["line"][-1])
            pattern_kinds.update(log["pattern"][-2:])
    raw = {json.dumps(p["input"]) for p in pairs}
    orbits = {input_orbit(p["input"]) for p in pairs}
    out = {"source_sha256": source_sha, "calls": N, "pairs": len(pairs),
           "errors": dict(errors), "unique_raw_inputs": len(raw), "unique_input_orbits": len(orbits),
           "canvas_heights": summary([len(p["input"]) for p in pairs]),
           "canvas_widths": summary([len(p["input"][0]) for p in pairs])}
    if tid == "7491f3cf":
        info = [decode_7491(p["input"]) for p in pairs]
        shapes = [d["shape"] for d in info]
        out.update({
            "panel_shapes": len(set(shapes)),
            "panel_shape_hist": hist(f"{h}x{w}" for h, w in shapes),
            "panel_heights": hist(h for h, _ in shapes),
            "panel_widths": hist(w for _, w in shapes),
            "aspect_hist": hist(aspect(s) for s in shapes),
            "largest_shape_share": round(max(Counter(shapes).values()) / len(shapes), 4),
            "wall_kind_hist": hist(wall_kinds),
            "wall_kind_by_aspect": {a: hist(k for k, s in zip(wall_kinds, shapes) if aspect(s) == a)
                                    for a in ("square", "tall", "wide")},
            "straight_wall_axis_hist": hist(d["straight_axis"] for d in info if d["straight_axis"]),
            "pattern_kind_hist": dict(sorted(pattern_kinds.items())),
            "wall_length": summary([d["wall"] for d in info]),
            "pattern_cells": summary([d["p2"] for d in info] + [d["p3"] for d in info]),
            "distinct_dot_placements": len({(d["shape"], d["dot"]) for d in info}),
            "dot_on_panel_edge_share": round(sum(d["dot_on_edge"] for d in info) / len(info), 4),
            "dot_region_share": summary([round(d["dot_region_share"], 4) for d in info]),
            "wall_evidence_both_branches_share": round(sum(d["evidence"] for d in info) / len(info), 4),
            "panel_ink_density": summary([round(d["density"], 4) for d in info]),
        })
        out["support"] = support(tid, pairs[:POOL], False)
        out["support_full"] = support(tid, pairs, False)
    else:
        info = [decode_98(p) for p in pairs]
        shapes = [d["shape"] for d in info]
        out.update({
            "shapes": len(set(shapes)),
            "widths_hist": hist(w for _, w in shapes),
            "heights_hist": hist(h for h, _ in shapes),
            "largest_shape_share": round(max(Counter(shapes).values()) / len(shapes), 4),
            "marker_count_hist": hist(len(d["markers"]) for d in info),
            "line_colour_hist": hist(d["line_colour"] for d in info),
            "marker_colour_hist": hist(c for d in info for _, c in d["markers"]),
            "border_colour_hist": hist(d["border"] for d in info),
            "distinct_marker_layouts": len({(d["shape"], tuple(d["markers"])) for d in info}),
            "line_row_relative": summary([round(d["line_row"] / (d["shape"][0] - 1), 4) for d in info]),
            "output_interior_density": summary([round(d["output_density"], 4) for d in info]),
        })
        out["support"] = support(tid, pairs[:POOL], True)
        out["support_full"] = support(tid, pairs, True)
    return out


def feasibility_7491():
    module, source_sha = load("7491f3cf", "after")

    def exhaustive(h, w):
        """Every wall subset; counts with and without the two-cell guard."""
        cells = [(r, c) for r in range(h) for c in range(w)]
        out = Counter()
        for mask in range(1, 1 << len(cells)):
            wall = {cells[i] for i in range(len(cells)) if mask >> i & 1}
            if len(wall) < 2 or not module._connected8(wall):
                continue
            regs = module._regions(h, w, wall)
            if len(regs) != 2:
                continue
            dot = any(not module._near(c, wall) for reg in regs for c in reg)
            guarded = module._wall_regions(h, w, wall) is not None
            out["two_region_walls"] += 1
            out["two_region_walls_with_a_dot_cell"] += dot
            out["guarded_walls_min_region_2"] += guarded
            out["guarded_walls_with_a_dot_cell"] += guarded and dot
        return dict(sorted(out.items()))

    out = {"source_sha256": source_sha,
           "exhaustive_wall_dot_enumeration": {f"{h}x{w}": exhaustive(h, w)
                                               for h, w in ((3, 3), (3, 4), (4, 3))}}
    counter = [0]
    colours = module._colours

    def counted(given):
        counter[0] += 1
        return colours(given)

    module._colours = counted
    rates, failures = {}, 0
    for h, w in module.SHAPES:
        random.seed(seed_of("accept", h, w))
        counter[0] = ok = 0
        for _ in range(ACCEPT_CALLS):
            try:
                module.generate(panel_height=h, panel_width=w, wall_evidence=True)
                ok += 1
            except RuntimeError:
                failures += 1
        rates[f"{h}x{w}"] = round(ok / counter[0], 4)
    worst = min(rates, key=rates.get)
    out["wall_evidence_acceptance"] = {
        "calls_per_shape": ACCEPT_CALLS, "shapes": len(rates), "runtime_errors": failures,
        "worst_shape": worst, "worst_rate": rates[worst],
        "worst_shape_exhaustion_log10_probability_at_max_tries": round(
            module.MAX_TRIES * math.log10(1 - rates[worst]), 2),
        "rates": rates}
    return out


def main():
    result = {"probe": "domain_probe.py", "probe_sha256": sha(Path(__file__).read_bytes()),
              "legacy_commit": LEGACY_COMMIT, "calls_per_version": N, "pool_rows": POOL,
              "families": {}}
    for tid in TASKS:
        result["families"][tid] = {v: measure(tid, v) for v in ("before", "after")}
    result["families"]["7491f3cf"]["feasibility"] = feasibility_7491()
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    result["output_sha256"] = sha(text.encode())
    OUT.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"output_sha256": result["output_sha256"]}))


if __name__ == "__main__":
    sys.exit(main())
