"""Read-only, seeded probe for two implementation-priority candidates.

Run from the worktree root:
    PYTHONPATH=. python arc_agi2/reports/diversity-v1/native-domain-review-20261024/probes/priority_candidates.py

Both candidates have an explicit constructor path that already reaches the
proposed canonical-restoring domain, so no constructor is changed or copied:

  18447a8d  band count n in 2..7 through generate(lefts, rights, colors).
            fixture_stats_batch6.py (lines 686-707) checked only the d4=0
            factory for n in {2,5,6,7}. This adds the production pair
            verifier (runtime.verification_solver, applied to native pairs by
            prepare.py line 330), the certified factory under all 8 D4
            transforms with a seeded palette, and the constructor's own
            uniqueness-guard acceptance per n (draw() returns None when a key
            fits several locks; the random loop at lines 53-64 is unbounded).
  b4a43f3b  6x6 maps of k = 1..8 axis segments plus 0..2 free cells through
            generate(colors, pattern). The random path draws exactly 3
            segments (line 35); canonical train[1] needs 4. Same verifier and
            factory checks. Maps other than 6x6 are NOT probed: the input
            layout ties the motif region to the map width (line 44) and the
            factory samples the motif as region // 3 (factory lines 51-53), so
            a resized layout must be designed first.

Nothing is written. No timing is reported, so two runs print identical output.
This is evidence for a review queue, not a certificate.
"""
import collections
import json
import random
import sys

sys.path.insert(0, ".")

from arc_agi2 import runtime  # noqa: E402
from arc_agi2.augmentation import transformed  # noqa: E402
from arc_agi2.direct_certificates import certified_factory_source  # noqa: E402

N = 300


def factory_ok(tid, pair, rng):
    """Certified factory program on all 8 D4 transforms with one seeded palette."""
    palette = rng.sample(range(10), 10)
    ok = 0
    for d4 in range(8):
        ns = {}
        exec(certified_factory_source(tid, d4, palette), ns)
        got = [list(map(int, r)) for r in ns["solve"]([], transformed(pair["input"], d4, palette))]
        ok += got == transformed(pair["output"], d4, palette)
    return ok == 8


def probe_18447a8d():
    m = __import__("tasks.task_18447a8d", fromlist=["generate"])
    check = runtime.verification_solver("18447a8d")
    rng = random.Random(18447)
    per_n = {n: collections.Counter() for n in range(2, 8)}
    for i in range(N * 6):
        n = 2 + i % 6
        colors = rng.sample([1, 2, 3, 4, 5, 6, 9], n)        # random_colors(n, exclude=[7, 8])
        lefts = [[rng.randint(1, 4) for _ in range(3)] for _ in colors]
        rights = [[5 - v for v in left] for left in lefts]
        rng.shuffle(rights)
        p = m.generate(lefts=sum(lefts, []), rights=sum(rights, []), colors=colors)
        c = per_n[n]
        c["layouts"] += 1
        if p["input"] is None:
            c["rejected_by_uniqueness_guard"] += 1
            continue
        c["scenes"] += 1
        c["verifier_agrees"] += runtime.grid(check(p["input"])) == p["output"]
        c["factory_8_d4_agrees"] += factory_ok("18447a8d", p, rng)
    return {"verifier": "archived_reference" if "18447a8d" not in
            __import__("arc_agi2.verified_rules", fromlist=["VERIFIERS"]).VERIFIERS else "verified_rules",
            "by_band_count": {str(n): dict(c) for n, c in per_n.items()}}


def probe_b4a43f3b():
    import common
    m = __import__("tasks.task_b4a43f3b", fromlist=["generate"])
    check = runtime.verification_solver("b4a43f3b")
    rng = random.Random(4434)
    by_k = {k: collections.Counter() for k in range(1, 9)}
    random.seed(4434)                                       # common.diagonally_connected_sprite
    for i in range(N * 8):
        k = 1 + i % 8
        sprite = common.diagonally_connected_sprite(3, 3)
        colors = "".join(str(rng.choice([1, 2, 3, 6]) if (r, c) in sprite else 0)
                         for r in range(3) for c in range(3))
        g = [[0] * 6 for _ in range(6)]
        for _ in range(k):                                  # constructor lines 36-41
            length = rng.randint(1, 6)
            pos = rng.randint(0, 6 - length)
            val = rng.randint(0, 5)
            cdir = rng.randint(0, 1)
            for j in range(pos, pos + length):
                g[val if cdir else j][j if cdir else val] = 2
        for _ in range(rng.randint(0, 2)):                  # free cells
            g[rng.randint(0, 5)][rng.randint(0, 5)] = 2
        pattern = "".join(str(v) for row in g for v in row)
        p = m.generate(colors=colors, pattern=pattern)
        c = by_k[k]
        c["scenes"] += 1
        c["verifier_agrees"] += runtime.grid(check(p["input"])) == p["output"]
        c["factory_8_d4_agrees"] += factory_ok("b4a43f3b", p, rng)
    can = runtime.reference("b4a43f3b")["canonical"]
    pairs = can["train"] + can["test"]
    return {"verifier": "archived_reference",
            "by_segment_count_plus_free_cells": {str(k): dict(c) for k, c in by_k.items()},
            "canonical_verifier_exact": sum(runtime.grid(check(p["input"])) == p["output"] for p in pairs),
            "canonical_pairs": len(pairs)}


if __name__ == "__main__":
    print(json.dumps({"18447a8d": probe_18447a8d(), "b4a43f3b": probe_b4a43f3b()},
                     indent=1, sort_keys=True))
