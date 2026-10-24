"""Old-vs-new equivalence of the complete explicit argument paths.

Loads the pre-expansion constructors from git (base 96be803) and compares
them with the working-tree constructors on random complete explicit inputs
that deliberately leave the default palette and domain: repeated or 0/5/7/8
colours, 0..8 bands, out-of-range and trailing lengths, list-typed colours and
patterns, empty maps and all-0 motifs.

Required outcome per input:
* old returns valid ARC grids  -> new returns the identical pair;
* old returns None, crashes, or leaves ARC bounds -> new raises ValueError.

    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-batch-i/legacy_equivalence.py [--write]
"""
import hashlib
import importlib
import importlib.util
import json
import random
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path

BASE_COMMIT = "96be803"
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
DRAWS = 3000


def old_module(tid):
    src = subprocess.run(["git", "show", f"{BASE_COMMIT}:tasks/task_{tid}.py"], cwd=ROOT,
                         check=True, capture_output=True, text=True).stdout
    mod = types.ModuleType(f"old_{tid}")
    exec(compile(src, f"old/task_{tid}.py", "exec"), mod.__dict__)
    return mod, hashlib.sha256(src.encode()).hexdigest()


def valid(pair):
    if not isinstance(pair, dict):
        return False
    for g in (pair.get("input"), pair.get("output")):
        if not isinstance(g, list) or not 1 <= len(g) <= 30:
            return False
        if not all(isinstance(r, list) and 1 <= len(r) <= 30 and len(r) == len(g[0]) for r in g):
            return False
        if not all(type(v) is int and 0 <= v <= 9 for r in g for v in r):
            return False
    return True


def args_184(rng):
    n = rng.choice([0, 1, 1, 2, 2, 2, 3, 4, 5, 6, 7, 8])
    colors = [rng.randint(0, 9) for _ in range(n)]
    if rng.random() < 0.5:                       # usually solvable: complements
        locks = [[rng.randint(1, 4) for _ in range(3)] for _ in range(n)]
        keys = [[5 - v for v in lk] for lk in locks]
        rng.shuffle(keys)
        lefts, rights = sum(locks, []), sum(keys, [])
    else:
        lefts = [rng.randint(-1, 12) for _ in range(3 * n)]
        rights = [rng.randint(-1, 12) for _ in range(3 * n)]
    if rng.random() < 0.2:
        lefts += [rng.randint(0, 4)] * rng.randint(1, 3)
        rights += [rng.randint(0, 4)] * rng.randint(1, 3)
    if rng.random() < 0.05 and lefts:
        lefts = lefts[:-1]
    return dict(lefts=lefts, rights=rights, colors=colors)


def args_b4(rng):
    k = 9 if rng.random() < 0.9 else rng.choice([8, 10])
    colors = [rng.choice([0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]) for _ in range(k)]
    if rng.random() < 0.05:
        colors = [0] * 9
    m = 36 if rng.random() < 0.9 else rng.choice([35, 37, 42])
    dens = rng.random()
    cells = [rng.choice("123456789") if rng.random() < dens else "0" for _ in range(m)]
    if rng.random() < 0.05:
        cells = ["0"] * m
    as_list = rng.random() < 0.3
    colors = colors if as_list else "".join(map(str, colors))
    pattern = cells if rng.random() < 0.2 else "".join(cells)
    return dict(colors=colors, pattern=pattern)


def compare(tid, make_args):
    old, old_sha = old_module(tid)
    new = importlib.import_module("tasks.task_" + tid)
    rng = random.Random(f"legacy-equivalence:{tid}")
    tally, mismatches = Counter(), []
    for i in range(DRAWS):
        kw = make_args(rng)
        try:
            ref = old.generate(**json.loads(json.dumps(kw)))
            ref_state = "valid" if valid(ref) else "none_or_out_of_bounds"
        except Exception as exc:
            ref, ref_state = None, "crash:" + type(exc).__name__
        try:
            got, got_state = new.generate(**json.loads(json.dumps(kw))), "valid"
        except ValueError:
            got, got_state = None, "ValueError"
        except Exception as exc:
            got, got_state = None, "unexpected:" + type(exc).__name__
        ok = (got == ref) if ref_state == "valid" else got_state == "ValueError"
        tally[(ref_state if ref_state == "valid" else "old_" + ref_state.split(":")[0], ok)] += 1
        if not ok and len(mismatches) < 5:
            mismatches.append({"draw": i, "args": kw, "old": ref_state, "new": got_state})
    return {"task_id": tid, "old_constructor_sha256": old_sha, "draws": DRAWS,
            "outcomes": {f"{k[0]}|{'match' if k[1] else 'MISMATCH'}": v
                         for k, v in sorted(tally.items())},
            "mismatches": mismatches, "passed": not mismatches}


if __name__ == "__main__":
    results = [compare("18447a8d", args_184), compare("b4a43f3b", args_b4)]
    for r in results:
        print(json.dumps(r))
    if "--write" in sys.argv:
        (OUT / "legacy-equivalence.json").write_text(json.dumps(results, indent=1) + "\n")
