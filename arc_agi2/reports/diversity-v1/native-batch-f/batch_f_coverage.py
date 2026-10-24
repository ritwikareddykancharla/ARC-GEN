"""Before/after default-draw coverage for native batch F (1000 draws each, same seeds).

"Before" runs the LEGACY constructor bytes from BASE_REV (hash-checked);
"after" runs the current constructors with default arguments. Every label is
checked by runtime.verification_solver. Bounded draws, not a capacity claim.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-f/batch_f_coverage.py
"""
import hashlib
import importlib
import json
import random
import subprocess
import types
from collections import Counter
from pathlib import Path

from arc_agi2.runtime import BASE, call, grid, verification_solver

OUT = Path(__file__).resolve().parent
BASE_REV = "e72190b"
DRAWS = 1000
TASKS = ("27f8ce4f", "48f8583b", "5b6cbef5")
LEGACY_SHA = {"27f8ce4f": "70c1d22e63c495fb6406e92fc0f616939995b39333bc8cf2fee2d2a62b1e3e78",
              "48f8583b": "e03a032ed0ebe4f6481595d20554648bb8fc2fe34d2556c4b8ad6fbf895cf0e6",
              "5b6cbef5": "7037789f7a5655b1bd06bcfbad383bdfc7b8c9d91f7a6b4c04c4f73df692aa24"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def legacy_module(tid):
    src = subprocess.run(["git", "show", f"{BASE_REV}:tasks/task_{tid}.py"], check=True,
                         capture_output=True, cwd=BASE.parent).stdout
    if sha(src) != LEGACY_SHA[tid]:
        raise RuntimeError(f"{tid}: legacy bytes do not match the recorded hash")
    module = types.ModuleType(f"legacy_{tid}")
    exec(compile(src, f"legacy/task_{tid}.py", "exec"), module.__dict__)
    return module


def hist(values):
    return dict(sorted(Counter(values).items()))


def bucket(x):
    return round(int(x * 10) / 10, 1)


def stats(tid, module):
    checker = verification_solver(tid)
    rows, disagree, seen = [], 0, set()
    for i in range(DRAWS):
        random.seed(int(sha(f"batch-f-coverage:{tid}:{i}".encode())[:12], 16))
        p = call(module.generate, seconds=3)
        p = {k: grid(p[k]) for k in ("input", "output")}
        disagree += grid(checker(p["input"])) != p["output"]
        g = p["input"]
        seen.add(json.dumps(g))
        h, w = len(g), len(g[0])
        counts = Counter(v for r in g for v in r)
        selected = sum(1 for r in range(h) for c in range(w)
                       if any(p["output"][r * h + y][c * w + x] for y in range(h) for x in range(w)))
        rows.append((h, w, counts, selected / (h * w)))
    out = {"unique_inputs": len(seen), "checker_disagreements": disagree,
           "height": hist(r[0] for r in rows), "width": hist(r[1] for r in rows),
           "input_shapes": len({(r[0], r[1]) for r in rows}),
           "non_square": sum(r[0] != r[1] for r in rows),
           "max_output_height": max(r[0] ** 2 for r in rows),
           "max_output_width": max(r[1] ** 2 for r in rows),
           "outputs_25x25": sum(r[0] == r[1] == 5 for r in rows),
           "selected_cell_fraction_decile": hist(bucket(r[3]) for r in rows)}
    if tid == "5b6cbef5":
        out["ink_colour"] = hist(next(iter(set(r[2]) - {0})) for r in rows)
        out["ink_density_decile"] = hist(bucket(1 - r[2][0] / (r[0] * r[1])) for r in rows)
        out["full_masks"] = sum(0 not in r[2] for r in rows)
    else:
        out["used_colours"] = hist(len(r[2]) for r in rows)
        out["monochrome"] = sum(len(r[2]) == 1 for r in rows)
    return out


def main():
    report = {"draws": DRAWS, "base_rev": BASE_REV,
              "source_sha256": {f"tasks/task_{t}.py": sha((BASE.parent / "tasks" / f"task_{t}.py")
                                                         .read_bytes()) for t in TASKS},
              "legacy_sha256": LEGACY_SHA, "families": {}}
    for tid in TASKS:
        report["families"][tid] = {
            "before": stats(tid, legacy_module(tid)),
            "after": stats(tid, importlib.import_module("tasks.task_" + tid))}
        print(tid, json.dumps(report["families"][tid]), flush=True)
    (OUT / "batch-f-coverage.json").write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
