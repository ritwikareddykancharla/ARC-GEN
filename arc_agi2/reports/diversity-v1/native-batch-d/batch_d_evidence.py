"""Before/after domain coverage and demonstration-witness rates for batch D.

"Before" draws use the legacy dimensions explicitly. With explicit dimensions
the constructors consume the RNG exactly like the pre-batch-D defaults (see
test_native_batch_d.test_explicit_dims_replay_legacy_stream), so they reproduce
the old default distribution. Writes batch-d-evidence.json next to this file.
"""

import hashlib
import importlib
import json
import random
from collections import Counter
from itertools import combinations
from pathlib import Path

from arc_agi2.runtime import BASE, grid, verification_solver

OUT = Path(__file__).resolve().parent
LEGACY = {"195ba7dc": (6, 5), "281123b4": (4, 4), "31d5ba1a": (5, 3), "34b99a2b": (4, 5)}
PRIORITY = [9, 4, 8, 5]  # highest first (paint order upper 5, top 8, bottom 4, lower 9)


def panels(tid, g):
    """Per-cell panel memberships from the INPUT, by native geometry."""
    h, W = len(g), len(g[0])
    if tid == "31d5ba1a":
        n = h // 2
        return [[(g[r][c] != 0, g[n + r][c] != 0) for c in range(W)] for r in range(n)]
    if tid == "281123b4":
        w = (W - 3) // 4
        return [[tuple(g[r][k * (w + 1) + c] for k in range(4)) for c in range(w)]
                for r in range(h)]
    w = W // 2
    return [[(g[r][c] != 0, g[r][w + 1 + c] != 0) for c in range(w)] for r in range(h)]


def witnessed(tid, demos):
    """Truth-table rows (binary families) or pairwise priorities (281123b4) shown."""
    seen = set()
    for p in demos:
        for row in panels(tid, p["input"]):
            for cell in row:
                if tid != "281123b4":
                    seen.add(cell)
                    continue
                present = [c for c in cell if c]
                if len(present) >= 2:
                    win = min(present, key=PRIORITY.index)
                    seen.update(frozenset((win, c)) for c in present if c != win)
    need = 6 if tid == "281123b4" else 4
    return len(seen) == need


def draws(tid, mode, n):
    gen = importlib.import_module("tasks.task_" + tid).generate
    out = []
    for i in range(n):
        random.seed(int(hashlib.sha256(f"batch-d-evidence:{tid}:{i}".encode()).hexdigest()[:12], 16))
        w, h = LEGACY[tid]
        out.append(gen(width=w, height=h) if mode == "before" else gen())
    return out


def stats(tid, pairs):
    checker = verification_solver(tid)
    ishape = Counter((len(p["input"]), len(p["input"][0])) for p in pairs)
    hs = [s[0] for s in ishape.elements()]; ws = [s[1] for s in ishape.elements()]
    oh = [len(p["output"]) for p in pairs]; ow = [len(p["output"][0]) for p in pairs]
    disagree = sum(grid(checker(p["input"])) != p["output"] for p in pairs)
    episodes = [pairs[i:i + 4] for i in range(0, len(pairs), 4)]
    # uniform-shape episodes as prepare's canonical profile requests
    by_shape = {}
    for p in pairs:
        by_shape.setdefault((len(p["input"]), len(p["input"][0])), []).append(p)
    uniform = [g[i:i + 4] for g in by_shape.values() for i in range(0, len(g) - 3, 4)]
    return {
        "draws": len(pairs),
        "unique_inputs": len({json.dumps(p["input"]) for p in pairs}),
        "input_shapes": len(ishape), "output_shapes": len({(a, b) for a, b in zip(oh, ow)}),
        "input_h": [min(hs), max(hs)], "input_w": [min(ws), max(ws)],
        "output_h": [min(oh), max(oh)], "output_w": [min(ow), max(ow)],
        "shapes_with_4_or_more_pairs": sum(v >= 4 for v in ishape.values()),
        "registered_verifier_disagreements": disagree,
        "episodes_demo_witness_complete": [sum(witnessed(tid, e[:3]) for e in episodes),
                                           len(episodes)],
        "uniform_shape_episodes_witness_complete": [sum(witnessed(tid, e[:3]) for e in uniform),
                                                    len(uniform)],
    }


def main():
    result = {"witness_definition": {
        "binary": "the three demonstrations show all four (panel A, panel B) cell states",
        "281123b4": "the three demonstrations show all six pairwise colour conflicts"}}
    for tid in LEGACY:
        src = (BASE.parent / "tasks" / ("task_" + tid + ".py")).read_bytes()
        result[tid] = {"constructor_sha256": hashlib.sha256(src).hexdigest(),
                       "before": stats(tid, draws(tid, "before", 1000)),
                       "after": stats(tid, draws(tid, "after", 1000)),
                       "after_shape_support_4000_draws": stats(tid, draws(tid, "after", 4000))[
                           "shapes_with_4_or_more_pairs"]}
    (OUT / "batch-d-evidence.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
