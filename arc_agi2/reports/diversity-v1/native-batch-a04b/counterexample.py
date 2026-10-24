"""Archived-verifier counterexamples for a04b2602 (native batch a04b).

The archived reference solver frames the reds inside the bounding box of each
4-connected green component. Reds can cut one rectangle into several green
components (a full red row or column, or a staircase cutting off a corner).
The cut reds then lie outside every component box, so the archived solver
leaves them unframed. The constructor frames them: they are inside the
rectangle it drew, and each has >= 2 orthogonal green neighbours.

This script draws per-draw seeded scenes (random.seed(i); generate()) from the
LEGACY constructor (base 9498a90 bytes, sha-pinned) and from the current one,
and records every scene where the archived solver disagrees with the label.
It also checks the reviewed verifier (verified_rules.rectangle_red_rings) on
every draw. The latent rectangles of each counterexample are captured by
wrapping common.rect during that one draw.

Run from the worktree root:
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-a04b/counterexample.py [N]
"""
import hashlib
import json
import random
import subprocess
import sys
import types
from pathlib import Path

import common
from arc_agi2 import runtime
from arc_agi2.verified_rules import rectangle_red_rings

OUT = Path(__file__).resolve().parent
TID = "a04b2602"
BASE_COMMIT = "9498a906edc8a0ce0ec9e556476f3411714e3d25"
LEGACY_SHA = "bdc127732747d186de38978a1ba859b0ac8783c8b065e7abd791982131f44b7c"
N = int(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else 20000


def sha(b):
    return hashlib.sha256(b).hexdigest()


def legacy():
    src = subprocess.run(["git", "show", f"{BASE_COMMIT}:tasks/task_{TID}.py"],
                         check=True, capture_output=True).stdout
    if sha(src) != LEGACY_SHA:
        raise RuntimeError("legacy constructor bytes changed")
    module = types.ModuleType(f"legacy_{TID}")
    exec(compile(src, f"legacy/task_{TID}.py", "exec"), module.__dict__)
    return module


def latent(module, seed):
    """Replay one draw and return (pair, accepted rectangles as (row, col, h, w))."""
    calls, counts, orig_rect, orig_randint = [], [], common.rect, common.randint

    def rect(grid, wide, tall, row, col, color):
        calls.append((row, col, tall, wide))
        return orig_rect(grid, wide, tall, row, col, color)

    def randint(a, b):
        value = orig_randint(a, b)
        if (a, b) == (2, 3):  # num_boxes; no other call starts at 2
            counts.append(value)
        return value

    common.rect, common.randint = rect, randint
    try:
        random.seed(seed)
        pair = module.generate()
    finally:
        common.rect, common.randint = orig_rect, orig_randint
    # Each attempt that passes placement draws all num_boxes rectangles; the
    # last num_boxes calls belong to the accepted scene.
    return pair, [list(x) for x in calls[-counts[0]:]]


def scan(label, module, archived):
    rows, reviewed_bad = [], 0
    for seed in range(N):
        random.seed(seed)
        pair = module.generate()
        try:
            reviewed_ok = rectangle_red_rings(pair["input"]) == pair["output"]
        except ValueError:
            reviewed_ok = False
        reviewed_bad += not reviewed_ok
        old = runtime.grid(runtime.call(archived, pair["input"]))
        if old != pair["output"]:
            rows.append(seed)
    return rows, reviewed_bad


def detail(module, seed, archived):
    pair, rects = latent(module, seed)
    g = pair["input"]
    old = runtime.grid(runtime.call(archived, g))
    diff = [[r, c] for r in range(len(g)) for c in range(len(g[0]))
            if old[r][c] != pair["output"][r][c]]
    comps = runtime.helpers.components([[v == 3 for v in row] for row in g])
    boxes = [[min(y for y, _ in c), min(x for _, x in c), max(y for y, _ in c), max(x for _, x in c)]
             for c in comps]
    missed = [[r, c] for r0, c0, h, w in rects for r in range(r0, r0 + h) for c in range(c0, c0 + w)
              if g[r][c] == 2 and not any(b[0] <= r <= b[2] and b[1] <= c <= b[3] for b in boxes)]
    return {"seed": seed, "shape": [len(g), len(g[0])], "latent_rectangles_row_col_h_w": rects,
            "green_component_boxes": boxes, "reds_inside_rectangle_outside_component_boxes": missed,
            "cells_where_archived_differs": diff, "input": g, "constructor_label": pair["output"],
            "archived_answer": old, "reviewed_verifier_exact": rectangle_red_rings(g) == pair["output"]}


def main():
    import tasks.task_a04b2602 as current
    archived = runtime.solver(TID)
    report = {"task_id": TID, "draws_per_constructor": N, "seed_rule": "random.seed(i); generate() for i in range(N)",
              "legacy_constructor_sha256": LEGACY_SHA, "base_commit": BASE_COMMIT,
              "current_constructor_sha256": sha(Path(current.__file__).read_bytes()),
              "reviewed_verifier": "arc_agi2.verified_rules.rectangle_red_rings",
              "archived_reference_sha256": sha((runtime.BASE / "references" / f"{TID}.json").read_bytes()),
              "verified_rules_sha256": sha((runtime.BASE / "verified_rules.py").read_bytes())}
    for label, module in (("legacy", legacy()), ("current", current)):
        seeds, reviewed_bad = scan(label, module, archived)
        report[label] = {"archived_disagreements": len(seeds), "disagreeing_seeds": seeds,
                         "reviewed_verifier_disagreements": reviewed_bad}
        if seeds:
            report[label]["first_counterexample"] = detail(module, seeds[0], archived)
        print(label, len(seeds), "archived disagreements;", reviewed_bad, "reviewed", flush=True)
    if "--no-write" not in sys.argv:
        (OUT / f"{TID}-archived-verifier-counterexample.json").write_text(
            json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
