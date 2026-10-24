"""Batch evidence for a04b2602 (native batch a04b). Read-only on production code.

Sections (each persisted to batch-evidence.json as soon as it completes):

* ``canonical``: latent-free measurements of the 4 canonical pairs (shape,
  rectangles, pairwise gaps, red density) and reachability under the legacy
  and current spacing; competitor survivors of the canonical train pairs.
* ``domain``: DRAWS per-draw-seeded default draws (random.seed(i)) from the
  LEGACY constructor (base 9498a90, sha-pinned) and from the current one.
  Latent rectangles, box count and red period are captured by wrapping
  common.rect / common.randint / common.overlaps for that draw only. Reported:
  shapes, dimensions, box count, box sizes, minimum and all pairwise gaps,
  red period and realised density, framed reds, attempts with every
  placement and guard rejection, RuntimeErrors, and agreement of the archived
  checker, the reviewed checker (verification_solver) and the factory
  program (d4 = 0, identity palette).
* ``competitors``: single-pair classification of the competitor readings
  (competitors.py) over both domains, and three-demonstration context
  ambiguity (ungated): legacy independent, current independent, and current
  same-shape (demos at the query's dimensions). Survivors are chosen from
  demonstrations and the query INPUT only. For every reading that separates
  in some context, the smallest witness (by total cells) is stored.
* ``probes``: explicit off-domain scenes showing what the kept invariants
  protect (gap-1 red touching two rectangles; touching rectangles).
* ``capacity``: sampled input orbits (prepare.input_orbit) at the smallest
  and largest shapes.

Run from the worktree root (two worker processes at most):
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-a04b/batch_evidence.py
"""
import collections
import hashlib
import importlib.util
import json
import random
import statistics
import subprocess
import sys
import time
import types
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import common
from arc_agi2 import runtime
from arc_agi2.diversity.prepare import input_orbit

OUT = Path(__file__).resolve().parent
PATH = OUT / "batch-evidence.json"
TID = "a04b2602"
BASE_COMMIT = "9498a906edc8a0ce0ec9e556476f3411714e3d25"
LEGACY_SHA = "bdc127732747d186de38978a1ba859b0ac8783c8b065e7abd791982131f44b7c"
DRAWS = 2000
CONTEXTS = 2000
CAPACITY_DRAWS = 3000
CAPACITY_SHAPES = ((10, 10), (10, 30), (30, 10), (30, 30))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def seed_of(*parts):
    return int(sha(":".join(map(str, ("batch-a04b",) + parts)).encode())[:12], 16)


def competitors():
    spec = importlib.util.spec_from_file_location("batch_a04b_competitors", OUT / "competitors.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def legacy():
    src = subprocess.run(["git", "show", f"{BASE_COMMIT}:tasks/task_{TID}.py"],
                         check=True, capture_output=True).stdout
    if sha(src) != LEGACY_SHA:
        raise RuntimeError("legacy constructor bytes changed")
    module = types.ModuleType(f"legacy_{TID}")
    exec(compile(src, f"legacy/task_{TID}.py", "exec"), module.__dict__)
    return module


def current():
    import tasks.task_a04b2602 as module
    return module


def module_for(label):
    return legacy() if label == "legacy" else current()


def gap(a, b):
    """Background cells between two boxes (r0, c0, r1, c1) along the separating axis."""
    return max(max(a[0] - b[2], b[0] - a[2]) - 1, max(a[1] - b[3], b[1] - a[3]) - 1)


def traced(module, seed, **kw):
    """One draw with its latent parameters (or the exception it raised)."""
    rects, counts, periods, placements = [], [], [], [0, 0]
    o_rect, o_randint, o_overlaps = common.rect, common.randint, common.overlaps

    def rect(grid, wide, tall, row, col, color):
        rects.append((row, col, row + tall - 1, col + wide - 1))
        return o_rect(grid, wide, tall, row, col, color)

    def randint(a, b):
        value = o_randint(a, b)
        if (a, b) == (2, 3):
            counts.append(value)
        elif (a, b) == (12, 30):
            periods.append(value)
        return value

    def overlaps(*args, **kwargs):
        hit = o_overlaps(*args, **kwargs)
        placements[bool(hit)] += 1
        return hit

    common.rect, common.randint, common.overlaps = rect, randint, overlaps
    try:
        random.seed(seed)
        pair = module.generate(**kw)
        error = None
    except Exception as exc:  # recorded, never hidden
        pair, error = None, repr(exc)
    finally:
        common.rect, common.randint, common.overlaps = o_rect, o_randint, o_overlaps
    n = counts[0] if counts else 0
    return {"pair": pair, "error": error, "boxes": rects[-n:] if pair else [],
            "period": periods[0] if periods else 20,
            "placement_rejections": placements[1],
            "guard_rejections": max(0, placements[0] - (1 if pair else 0))}


def summarise(values):
    values = list(values)
    if not values:
        return {}
    return {"min": min(values), "max": max(values), "mean": round(statistics.fmean(values), 4),
            "median": statistics.median(values)}


def hist(values):
    return dict(sorted(collections.Counter(values).items(), key=lambda kv: str(kv[0])))


def program():
    from arc_agi2.direct_certificates import certified_factory_source
    src = certified_factory_source(TID, 0, list(range(10)))
    if src is None:
        raise RuntimeError("no certified factory program for the current bytes")
    ns = {}
    exec(src, ns)
    return lambda g: [list(map(int, r)) for r in ns["solve"]([], g)]


def domain(label):
    started = time.monotonic()
    module = module_for(label)
    archived = runtime.solver(TID)
    reviewed = runtime.verification_solver(TID)
    solve = program()
    rows, errors = [], []
    agree = collections.Counter()
    for i in range(DRAWS):
        t = traced(module, seed_of("domain", i))
        if t["error"]:
            errors.append({"draw": i, "error": t["error"]})
            continue
        g, out = t["pair"]["input"], t["pair"]["output"]
        h, w = len(g), len(g[0])
        boxes = t["boxes"]
        gaps = [gap(a, b) for k, a in enumerate(boxes) for b in boxes[:k]]
        reds = sum(v == 2 for row in g for v in row)
        framed = sum(1 for r in range(h) for c in range(w) if g[r][c] == 2 and out[r][c] == 2
                     and sum(0 <= r + dy < h and 0 <= c + dx < w and g[r + dy][c + dx] == 3
                             for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 2)
        agree["archived"] += runtime.grid(runtime.call(archived, g)) == out
        agree["reviewed"] += runtime.grid(runtime.call(reviewed, g)) == out
        if solve:
            agree["factory_program"] += solve(g) == out
        rows.append({"shape": (h, w), "boxes": len(boxes),
                     "sizes": [(b[2] - b[0] + 1, b[3] - b[1] + 1) for b in boxes],
                     "min_gap": min(gaps), "gaps": gaps, "period": t["period"],
                     "density": reds / (h * w), "framed": framed,
                     "placement_rejections": t["placement_rejections"],
                     "guard_rejections": t["guard_rejections"],
                     "input": sha(json.dumps(g).encode())})
    n = len(rows)
    sizes = [s for r in rows for s in r["sizes"]]
    report = {
        "draws": DRAWS, "accepted": n, "runtime_errors": errors,
        "unique_inputs": len({r["input"] for r in rows}),
        "distinct_shapes": len({r["shape"] for r in rows}),
        "height": summarise(r["shape"][0] for r in rows),
        "width": summarise(r["shape"][1] for r in rows),
        "rectangle_count": hist(r["boxes"] for r in rows),
        "rectangle_height": summarise(s[0] for s in sizes),
        "rectangle_width": summarise(s[1] for s in sizes),
        "distinct_rectangle_sizes": len(set(sizes)),
        "min_gap_histogram": hist(min(r["min_gap"], 6) for r in rows),
        "min_gap_note": "key 6 means >= 6",
        "scenes_with_gap_1": sum(r["min_gap"] == 1 for r in rows),
        "pairwise_gap_histogram": hist(min(x, 6) for r in rows for x in r["gaps"]),
        "red_period_histogram": hist(r["period"] for r in rows),
        "red_density": summarise(round(r["density"], 4) for r in rows),
        "framed_reds": summarise(r["framed"] for r in rows),
        "placement_rejections": {"total": sum(r["placement_rejections"] for r in rows),
                                 **summarise(r["placement_rejections"] for r in rows)},
        "guard_rejections": {"total": sum(r["guard_rejections"] for r in rows),
                             **summarise(r["guard_rejections"] for r in rows)},
        "checker_agreement": dict(agree),
        "seconds": round(time.monotonic() - started, 2),
    }
    return label, report


def canonical(comp):
    can = runtime.reference(TID)["canonical"]
    pairs = can["train"] + can["test"]
    rows = []
    for name, p in zip(["train0", "train1", "train2", "test0"], pairs):
        g = p["input"]
        boxes = comp.rectangles(g)
        gaps = [gap(a, b) for k, a in enumerate(boxes) for b in boxes[:k]]
        reds = sum(v == 2 for row in g for v in row)
        rows.append({"pair": name, "shape": [len(g), len(g[0])],
                     "rectangles_h_w": [[b[2] - b[0] + 1, b[3] - b[1] + 1] for b in boxes],
                     "pairwise_gaps": sorted(gaps), "red_density": round(reds / (len(g) * len(g[0])), 4),
                     "reachable_legacy_spacing_2": min(gaps) >= 2,
                     "reachable_current_spacing_1": min(gaps) >= 1})
    return {"pairs": rows,
            "train_survivors": comp.surviving(can["train"]),
            "train_context_ambiguous_on_test": comp.ambiguous(can["train"], can["test"][0]["input"]),
            "per_pair_survivors": {r["pair"]: comp.surviving([p]) for r, p in zip(rows, pairs)}}


def contexts(job):
    label, same_shape = job
    started = time.monotonic()
    comp = competitors()
    module = module_for(label)
    fits = collections.Counter()
    ambiguous, separating, witnesses = 0, collections.Counter(), {}
    for i in range(CONTEXTS):
        random.seed(seed_of("context", label, same_shape, i))
        query = module.generate()
        kw = ({"height": len(query["input"]), "width": len(query["input"][0])}
              if same_shape else {})
        demos = [module.generate(**kw) for _ in range(3)]
        for p in demos + [query]:
            for name, f in comp.RULES.items():
                fits[name] += comp._key(f(p["input"])) == comp._key(p["output"])
        sep = comp.separating(demos, query["input"])
        if comp.ambiguous(demos, query["input"]):
            ambiguous += 1
        for name in sep:
            separating[name] += 1
            size = sum(len(p["input"]) * len(p["input"][0]) for p in demos + [query])
            if name not in witnesses or size < witnesses[name]["cells"]:
                witnesses[name] = {"context": i, "cells": size, "demonstrations": demos,
                                   "query_input": query["input"],
                                   "survivors": comp.surviving(demos)}
    return (label, same_shape), {
        "contexts": CONTEXTS, "ambiguous": ambiguous,
        "separating_rule_counts": dict(sorted(separating.items())),
        "single_pair_fit_counts": dict(sorted(fits.items())),
        "single_pairs": 4 * CONTEXTS, "witnesses": witnesses,
        "seconds": round(time.monotonic() - started, 2)}


def probes(comp):
    """Explicit off-domain scenes (constructor explicit path, no guard)."""
    reviewed = runtime.verification_solver(TID)
    module = current()

    def scene(h, w, boxes, reds):
        g = [[0] * w for _ in range(h)]
        for r0, c0, r1, c1 in boxes:
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    g[r][c] = 3
        for r, c in reds:
            g[r][c] = 2
        return g

    out = {}
    cases = {
        # Two rectangles one row apart; a red in the gap touches both.
        "gap1_red_touching_two_rectangles": scene(12, 12, [(1, 1, 4, 8), (6, 1, 9, 8)],
                                                  [(5, 4), (2, 3)]),
        # Same geometry with the gap red outside the facing span: valid.
        "gap1_red_outside_facing_span": scene(12, 12, [(1, 1, 4, 8), (6, 1, 9, 8)],
                                              [(5, 10), (2, 3)]),
        # Touching rectangles merge into one green shape (gap 0).
        "touching_rectangles": scene(12, 12, [(1, 1, 4, 5), (5, 3, 9, 8)], [(2, 2), (7, 6)]),
    }
    for name, g in cases.items():
        pair = module.generate(width=len(g[0]), height=len(g), colors=sum(g, []))
        native = comp._key(comp.RULES["native"](g))
        inside = comp._key(comp.RULES["select:inside_rectangle"](g))
        try:
            reviewed_answer = comp._key(reviewed(g))
            reviewed_status = "answer"
        except ValueError as exc:
            reviewed_answer, reviewed_status = None, "raised: " + str(exc)
        out[name] = {
            "constructor_label_equals_native_neighbour_rule": comp._key(pair["output"]) == native,
            "native_neighbour_rule_equals_inside_rectangle": native == inside,
            "reviewed_checker": reviewed_status,
            "reviewed_equals_label": reviewed_answer == comp._key(pair["output"]),
        }
    return out


def capacity():
    module = current()
    out = {}
    for h, w in CAPACITY_SHAPES:
        random.seed(seed_of("capacity", h, w))
        orbits = {input_orbit(module.generate(height=h, width=w)["input"])
                  for _ in range(CAPACITY_DRAWS)}
        out[f"{h}x{w}"] = len(orbits)
    return {"draws_per_shape": CAPACITY_DRAWS, "distinct_input_orbits": out}


def persist(report):
    PATH.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")


def main():
    write = "--no-write" not in sys.argv
    comp = competitors()
    files = {"constructor": Path(current().__file__),
             "factory": runtime.BASE / "direct_factories" / f"task_{TID}.py",
             "factory_certificate": runtime.BASE / "direct_factories" / f"{TID}.json",
             "verified_rules": runtime.BASE / "verified_rules.py",
             "gate": runtime.BASE / "rect_ring_a04b2602_evidence.py",
             "colour_evidence": runtime.BASE / "colour_evidence.py",
             "competitors": OUT / "competitors.py", "harness": Path(__file__)}
    report = {"task_id": TID, "base_commit": BASE_COMMIT, "legacy_constructor_sha256": LEGACY_SHA,
              "source_sha256": {k: sha(p.read_bytes()) for k, p in files.items()},
              "draws": DRAWS, "contexts": CONTEXTS}
    report["canonical"] = canonical(comp)
    report["probes"] = probes(comp)
    print("canonical/probes done", flush=True)
    if write:
        persist(report)
    with ProcessPoolExecutor(max_workers=2) as pool:
        report["domain"] = {}
        for label, rep in pool.map(domain, ("legacy", "current")):
            report["domain"][label] = rep
            print("domain", label, {k: rep[k] for k in ("accepted", "unique_inputs", "scenes_with_gap_1",
                                                         "checker_agreement", "seconds")}, flush=True)
            if write:
                persist(report)
        report["contexts_ungated"] = {}
        candidates = {}
        for (label, same), rep in pool.map(contexts, (("legacy", False), ("current", False),
                                                      ("current", True))):
            key = label + ("_same_shape" if same else "_independent")
            for name, w in rep.pop("witnesses").items():
                w = dict(w, source=key)
                best = candidates.get(name)
                if best is None or w["cells"] < best["cells"]:
                    candidates[name] = w
            report["contexts_ungated"][key] = rep
            print("contexts", key, rep["ambiguous"], rep["separating_rule_counts"], rep["seconds"],
                  flush=True)
            if write:
                persist(report)
    fits = collections.Counter()
    total = 0
    for rep in report["contexts_ungated"].values():
        fits.update(rep["single_pair_fit_counts"])
        total += rep["single_pairs"]
    separable = sorted({n for rep in report["contexts_ungated"].values()
                        for n in rep["separating_rule_counts"]})
    report["single_pair_classes"] = {
        "pairs": total,
        "identical_on_every_sampled_pair": sorted(n for n in comp.RULES if fits[n] == total and n != "native"),
        "refuted_by_every_sampled_pair": sorted(n for n in comp.RULES if fits[n] == 0),
        "separable_in_some_context": separable,
    }
    # One stored context per separable reading: the smallest found, deduplicated.
    unique = {}
    for name in sorted(candidates):
        w = candidates[name]
        key = (w["source"], w["context"])
        if key not in unique:
            unique[key] = {"source": w["source"], "context": w["context"], "cells": w["cells"],
                           "survivors": w["survivors"],
                           "separating": comp.separating(w["demonstrations"], w["query_input"]),
                           "demonstrations": w["demonstrations"], "query_input": w["query_input"]}
    report["witnesses"] = sorted(unique.values(), key=lambda w: (w["source"], w["context"]))
    report["witness_note"] = ("Smallest stored context per separable reading. 'separating' lists the "
                              "surviving readings whose query answer differs from the native one. Query "
                              "answers are omitted: selection never reads them.")
    report["capacity"] = capacity()
    print("capacity", report["capacity"], flush=True)
    if write:
        persist(report)


if __name__ == "__main__":
    main()
