"""Measure the archived vs reviewed 34b99a2b pair verifiers on constructor draws.

Run: PYTHONPATH=<repo> python -m arc_agi2.reports... or as a script with the
repository on PYTHONPATH. Writes the counterexample and a counts summary next
to this file. Only explicit generator arguments are used for the expanded
sample, so the same draws are reproducible on the legacy and expanded
constructor bytes.
"""

import hashlib
import importlib
import json
import random
from pathlib import Path

from arc_agi2.runtime import BASE, grid, reference, solver
from arc_agi2.verified_rules import midpoint_xor_panels

TID = "34b99a2b"
OUT = Path(__file__).resolve().parent


def label_ok(fn, pair):
    try:
        return grid(fn(pair["input"])) == grid(pair["output"])
    except Exception:
        return False


def full_internal_columns(g):
    w = len(g[0]); mid = w // 2
    return [x for x in range(w) if x != mid and len({r[x] for r in g}) == 1 and g[0][x] != 0]


def main():
    gen = importlib.import_module("tasks.task_" + TID).generate
    archived = solver(TID)
    source = (BASE.parent / "tasks" / ("task_" + TID + ".py")).read_bytes()
    summary = {"task_id": TID,
               "constructor_sha256": hashlib.sha256(source).hexdigest(),
               "verified_rules_sha256": hashlib.sha256(
                   (BASE / "verified_rules.py").read_bytes()).hexdigest()}
    fixtures = reference(TID)
    fixture_rows = []
    for name in ("canonical", "teaching_fixture"):
        for split in ("train", "test"):
            for p in fixtures[name][split]:
                fixture_rows.append((label_ok(archived, p), label_ok(midpoint_xor_panels, p)))
    summary["fixtures"] = {"pairs": len(fixture_rows),
                           "archived_exact": sum(a for a, _ in fixture_rows),
                           "reviewed_exact": sum(b for _, b in fixture_rows)}
    counterexample = None
    for kind in ("legacy_default", "expanded_explicit"):
        stats = {"draws": 1000, "archived_disagree": 0, "reviewed_disagree": 0,
                 "with_full_internal_column": 0, "shapes": set()}
        for i in range(1000):
            seed = int(hashlib.sha256(f"batch-d:{TID}:{kind}:{i}".encode()).hexdigest()[:12], 16)
            random.seed(seed)
            if kind == "legacy_default":
                kw = {"width": 4, "height": 5}
            else:
                kw = {"width": random.randint(3, 14), "height": random.randint(3, 30)}
            pair = gen(**kw)
            stats["shapes"].add((len(pair["input"]), len(pair["input"][0])))
            a, b = label_ok(archived, pair), label_ok(midpoint_xor_panels, pair)
            stats["archived_disagree"] += not a
            stats["reviewed_disagree"] += not b
            stats["with_full_internal_column"] += bool(full_internal_columns(pair["input"]))
            if counterexample is None and not a and b and kind == "legacy_default":
                try:
                    got = grid(archived(pair["input"]))
                except Exception as exc:
                    got = repr(exc)
                counterexample = {
                    "task_id": TID, "seed": seed, "generate_kwargs": kw,
                    "input": pair["input"], "constructor_output": pair["output"],
                    "archived_solver_result": got,
                    "full_internal_columns": full_internal_columns(pair["input"]),
                    "midpoint_column": len(pair["input"][0]) // 2,
                    "explanation": "The archived solver selects the first full single-colour "
                                   "non-zero column; here a left-panel column filled with 8 "
                                   "precedes the midpoint divider of colour 4.",
                }
        stats["shapes"] = len(stats["shapes"])
        summary[kind] = stats
    (OUT / (TID + "-archived-verifier-counterexample.json")).write_text(
        json.dumps(counterexample) + "\n")
    (OUT / (TID + "-verifier-evidence.json")).write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
