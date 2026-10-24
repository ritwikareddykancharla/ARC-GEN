"""Archived vs reviewed geometric pair verifiers for 195ba7dc and 281123b4.

Run with the repository on PYTHONPATH. Only explicit generator arguments are
used, so draws are identical on the legacy and expanded constructor bytes.
"Expanded" draws cover the FULL explicit range (from 1x1 to the 30-cell
limit), not just the random sampling range. The adversarial set enumerates
empty, sparse and full panel rows/columns across even/odd panel shapes.
"""

import hashlib
import importlib
import json
import random
from pathlib import Path

from arc_agi2.runtime import BASE, grid, reference, solver
from arc_agi2.verified_rules import midpoint_or_panels, separated_priority_panels

OUT = Path(__file__).resolve().parent
SPEC = {"195ba7dc": {"fn": midpoint_or_panels, "legacy": (6, 5), "max": (14, 30),
                     "masks": ("top", "bottom")},
        "281123b4": {"fn": separated_priority_panels, "legacy": (4, 4), "max": (6, 30),
                     "masks": ("top", "upper", "lower", "bottom")}}


def ok(fn, pair):
    try:
        return grid(fn(pair["input"])) == grid(pair["output"])
    except Exception:
        return False


def shapes(w, h):
    """Named adversarial single-panel masks of size w x h."""
    n = w * h
    yield "empty", [0] * n
    yield "full", [1] * n
    for c in sorted({0, w - 1, w // 2}):
        yield f"full_col{c}", [int(i % w == c) for i in range(n)]
    for r in sorted({0, h - 1, h // 2}):
        yield f"full_row{r}", [int(i // w == r) for i in range(n)]
    yield "single_cell", [int(i == 0) for i in range(n)]
    yield "checker", [int((i // w + i % w) % 2 == 0) for i in range(n)]


def adversarial(tid):
    spec = SPEC[tid]
    mw, mh = spec["max"]
    dims = sorted({(1, 1), (1, 2), (2, 1), (2, 2), (3, 3), (4, 4), (3, 4), (4, 3), (4, 5),
                   (min(5, mw), 6), (mw, 1), (1, mh), (mw, mh), (mw - 1, mh - 1)})
    for w, h in dims:
        for slot in spec["masks"]:
            for name, mask in shapes(w, h):
                masks = {m: (mask if m == slot else [0] * (w * h)) for m in spec["masks"]}
                yield f"{w}x{h}:{slot}:{name}", dict(width=w, height=h, **masks)
        # everything full, everything empty, and one full column per panel
        for name, _ in (("all_full", 1), ("all_empty", 0)):
            yield f"{w}x{h}:{name}", dict(width=w, height=h,
                                          **{m: [_] * (w * h) for m in spec["masks"]})
        yield f"{w}x{h}:col_each", dict(width=w, height=h, **{
            m: [int(i % w == k % w) for i in range(w * h)] for k, m in enumerate(spec["masks"])})


def main():
    summary = {"verified_rules_sha256": hashlib.sha256(
        (BASE / "verified_rules.py").read_bytes()).hexdigest()}
    for tid, spec in SPEC.items():
        gen = importlib.import_module("tasks.task_" + tid).generate
        archived, reviewed = solver(tid), spec["fn"]
        src = (BASE.parent / "tasks" / ("task_" + tid + ".py")).read_bytes()
        res = {"constructor_sha256": hashlib.sha256(src).hexdigest()}
        packet = reference(tid)
        fx = [p for name in ("canonical", "teaching_fixture") for s in ("train", "test")
              for p in packet[name][s]]
        res["fixtures"] = {"pairs": len(fx), "archived_exact": sum(ok(archived, p) for p in fx),
                           "reviewed_exact": sum(ok(reviewed, p) for p in fx)}
        for kind in ("legacy_dims", "expanded_explicit"):
            a = b = 0
            for i in range(1000):
                random.seed(int(hashlib.sha256(f"batch-d:{tid}:{kind}:{i}".encode()).hexdigest()[:12], 16))
                w, h = (spec["legacy"] if kind == "legacy_dims"
                        else (random.randint(1, spec["max"][0]), random.randint(1, spec["max"][1])))
                p = gen(width=w, height=h)
                a += not ok(archived, p); b += not ok(reviewed, p)
            res[kind] = {"draws": 1000, "archived_disagree": a, "reviewed_disagree": b}
        cases = list(adversarial(tid))
        bad_a = [name for name, kw in cases if not ok(archived, gen(**kw))]
        bad_b = [name for name, kw in cases if not ok(reviewed, gen(**kw))]
        res["adversarial"] = {"cases": len(cases), "archived_disagree": len(bad_a),
                              "reviewed_disagree": len(bad_b),
                              "archived_disagree_at_4x4_or_larger": sum(
                                  1 for n in bad_a if min(map(int, n.split(":")[0].split("x"))) >= 4),
                              "archived_examples": bad_a[:12]}
        col0 = [int(i % 4 == 0) for i in range(16)]
        kw = dict(width=4, height=4, **{m: (col0 if m == "top" else [0] * 16) for m in spec["masks"]})
        pair = gen(**kw)
        try:
            got = grid(archived(pair["input"]))
        except Exception as exc:
            got = None
            err = repr(exc)
        try:
            import numpy as np
            shape = list(np.asarray(archived(pair["input"])).shape)
        except Exception:
            shape = None
        cx = {"task_id": tid, "generate_kwargs": kw, "input": pair["input"],
              "constructor_output": pair["output"], "archived_solver_result": got,
              "archived_solver_shape": shape,
              "reviewed_result": grid(reviewed(pair["input"])),
              "explanation": ("Sparse valid scene: the only foreground cells fill one full "
                              "column of the first panel. The archived first-full-column "
                              "heuristic takes that column as the divider/separator.")}
        if got is None:
            cx["archived_solver_error"] = err
        (OUT / (tid + "-archived-verifier-counterexample.json")).write_text(json.dumps(cx) + "\n")
        summary[tid] = res
    (OUT / "geometric-verifier-evidence-195ba7dc-281123b4.json").write_text(
        json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
