"""Before/after coverage (1000 default draws, same seeds) and 2-band capacity for batch I.

Before = base-96be803 constructors loaded from git (hash recorded); after =
working tree. Each draw's label is checked with the registered checker. The
18447a8d 2-band capacity enumerates every random-domain layout with colours
[1, 2]. prepare.input_orbit relabels colours by first occurrence, so other
colour pairs add no orbits. It reports production orbit identities and
their finite_input_policy split.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-i/batch_i_evidence.py
"""
import hashlib
import importlib
import json
import random
import sys
from collections import Counter
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from legacy_equivalence import old_module  # noqa: E402

from arc_agi2.diversity.prepare import input_orbit
from arc_agi2.finite_input_policy import input_split
from arc_agi2.runtime import BASE, grid, verification_solver

OUT = Path(__file__).resolve().parent
DRAWS = 1000


def sha(b):
    return hashlib.sha256(b).hexdigest()


def hist(values):
    return {str(k): v for k, v in sorted(Counter(values).items())}


def span(values):
    return [min(values), max(values)] if values else None


def draws(module, tid):
    out = []
    for i in range(DRAWS):
        random.seed(int(sha(f"batch-i-coverage:{tid}:{i}".encode())[:12], 16))
        p = module.generate()
        out.append({k: grid(p[k]) for k in ("input", "output")})
    return out


def common_stats(tid, pairs):
    check = verification_solver(tid)
    orbits = [input_orbit(p["input"]) for p in pairs]
    shapes = Counter((len(p["input"]), len(p["input"][0])) for p in pairs)
    return {"unique_inputs": len({json.dumps(p["input"]) for p in pairs}),
            "unique_input_orbits": len(set(orbits)),
            "orbit_split": hist(input_split(o) for o in set(orbits)),
            "input_shapes": len(shapes), "shapes_with_4plus_pairs": sum(v >= 4 for v in shapes.values()),
            "output_shapes": len({(len(p["output"]), len(p["output"][0])) for p in pairs}),
            "checker_disagreements": sum(grid(check(p["input"])) != p["output"] for p in pairs)}


def stats_184(pairs):
    bands, moved, fixed_points = [], [], []
    for p in pairs:
        g, o = p["input"], p["output"]
        n = (len(g) - 1) // 4
        bands.append(n)
        stay = sum(o[4 * b + 1][4] == g[4 * b + 1][10] for b in range(n))  # column 4 is always key
        fixed_points.append(stay)
        moved.append(stay == 0)
    return {"band_count": hist(bands), "key_fixed_points": hist(fixed_points),
            "all_keys_moved": sum(moved), "identity_assignment": sum(
                f == b for f, b in zip(fixed_points, bands))}


def stats_b4(pairs):
    scales, heights, marked, full, motif_cells = [], [], [], 0, []
    for p in pairs:
        g = p["input"]
        w = len(g[0])
        s, h = w // 3, len(g) - w - 1
        scales.append(s)
        heights.append(h)
        mp = g[w + 1:]
        k = sum(v != 0 for r in mp for v in r)
        marked.append(round(k / (h * w), 2))
        full += k == h * w
        motif_cells.append(sum(g[s * r][s * c] != 0 for r in range(3) for c in range(3)))
    return {"scale": hist(scales), "map_height": hist(heights),
            "map_occupancy_fraction": span(marked), "full_maps": full,
            "occupancy_deciles": hist(min(9, int(10 * f)) for f in marked),
            "motif_cells": hist(motif_cells)}


def capacity_two_bands():
    m = importlib.import_module("tasks.task_18447a8d")
    profiles = list(product(range(1, 5), repeat=3))
    layouts, orbits = 0, set()
    for a, b in product(profiles, repeat=2):
        if a == b:
            continue
        for swap in (False, True):
            keys = [[5 - v for v in (b if swap else a)], [5 - v for v in (a if swap else b)]]
            p = m.generate(lefts=list(a) + list(b), rights=keys[0] + keys[1], colors=[1, 2])
            layouts += 1
            orbits.add(input_orbit(p["input"]))
    split = Counter(input_split(o) for o in orbits)
    return {"layouts": layouts, "definition": "64 lock profiles (1..4)^3, ordered distinct pairs, "
            "2 key orders, colours [1, 2]; input_orbit relabels colours",
            "input_orbits": len(orbits), "orbit_split": dict(split)}


def main():
    report = {"draws": DRAWS, "families": {}}
    for tid, extra in (("18447a8d", stats_184), ("b4a43f3b", stats_b4)):
        old, old_sha = old_module(tid)
        new = importlib.import_module("tasks.task_" + tid)
        before, after = draws(old, tid), draws(new, tid)
        report["families"][tid] = {
            "before": {"constructor_sha256": old_sha, **common_stats(tid, before), **extra(before)},
            "after": {"constructor_sha256": sha(Path(new.__file__).read_bytes()),
                      **common_stats(tid, after), **extra(after)}}
    report["capacity_18447a8d_two_bands"] = capacity_two_bands()
    report["source_sha256"] = {"harness": sha(Path(__file__).read_bytes()),
                               "verified_rules": sha((BASE / "verified_rules.py").read_bytes())}
    (OUT / "batch-i-evidence.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
