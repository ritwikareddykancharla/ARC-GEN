"""Find saved solvers that already operate directly on augmented grids.

This is a screening audit, not permission to skip fresh-example verification.
No undo/redo augmentation wrapper is added and no target labels enter programs.
"""
import argparse
import ast
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
from .runtime import BASE, reference
from .fixture_policy import fixture_basis
from .program_targets import native_program, audit_target, verify
from .augmentation import transformed


def candidate(task_id):
    source, basis = native_program(task_id)
    class Entry(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name == "_native_solve":
                node.name = "solve"
            return self.generic_visit(node)
    tree = Entry().visit(ast.parse(source))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n", basis


def check(tid):
    result = dict(task_id=tid, passed=False, checked_variants=0)
    try:
        source, basis = candidate(tid)
        audit_target(tid, source)
        result.update(program_sha256=hashlib.sha256(source.encode()).hexdigest(), basis=basis)
        fixture = fixture_basis(tid)
        task = reference(tid)[fixture["fixture"]]
        for palette in (list(range(10)), [3, 9, 0, 7, 2, 8, 1, 6, 4, 5]):
            for d4 in range(8):
                episode = {
                    "train": [{k: transformed(p[k], d4, palette) for k in ("input", "output")}
                              for p in task["train"]],
                    "test": [{"input": transformed(p["input"], d4, palette)} for p in task["test"]],
                    "solutions": [transformed(p["output"], d4, palette) for p in task["test"]],
                }
                result["current_variant"] = {"d4": d4, "palette": palette}
                verify(source, episode, seconds=1)
                result["checked_variants"] += 1
        result.update(passed=True, fixture=fixture["fixture"])
        result.pop("current_variant", None)
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)[:500]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ids = sorted(r["task_id"] for r in json.loads((BASE/"reference_index.json").read_text())["tasks"])
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(check, tid) for tid in ids]
        for future in as_completed(futures):
            rows.append(future.result())
            if len(rows) % 100 == 0:
                print(json.dumps({"checked": len(rows), "compatible_candidates": sum(r["passed"] for r in rows)}), flush=True)
    report = {
        "scope": "Saved direct-coordinate programs on approved supplied fixtures under all D4 transforms and two palettes. Candidates require fresh-example validation before use.",
        "total": len(rows), "passed": sum(r["passed"] for r in rows),
        "failures": dict(Counter(r.get("error", "").split(":")[0] for r in rows if not r["passed"])),
        "tasks": sorted(rows, key=lambda r:r["task_id"]),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="tasks"}), flush=True)


if __name__ == "__main__":
    main()
