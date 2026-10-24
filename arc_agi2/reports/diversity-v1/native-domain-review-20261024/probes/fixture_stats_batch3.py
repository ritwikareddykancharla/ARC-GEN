"""Batch-3 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Usage: fixture_stats_batch3.py [N_NATIVE] [SEED]

Prints the canonical-fixture statistics and the one small native measurement
quoted in batch-3 reviews:
  * 996ec1f3: zeros per canonical input (noise is random_color 1-9).
  * 9caba7c3: stamped windows, reds per window, reds outside any window.
  * aa300dc3: per pair, the maximal whole-diagonal zero count and its ties.
  * d94c3b52: whether common.letter_map glyphs are pairwise distinct.
  * e0fb7511: canonical black density and azure count per pair.
  * bd283c4a: fraction of N_NATIVE native inputs with tied colour counts.
"""
import sys, random, collections
sys.path.insert(0, '.')
import common
from arc_agi2 import runtime

n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 0)


def pairs(tid):
    c = runtime.reference(tid)["canonical"]
    return c["train"] + c["test"]


print("996ec1f3 zeros per input:", [sum(v == 0 for r in p["input"] for v in r) for p in pairs("996ec1f3")])

for k, p in enumerate(pairs("9caba7c3")):
    I, O = p["input"], p["output"]
    cs = [(r, c) for r in range(19) for c in range(19) if O[r][c] == 4]
    box = {(r + a, c + b) for r, c in cs for a in (-1, 0, 1) for b in (-1, 0, 1)}
    reds = [sum(I[r + a][c + b] == 2 for a in (-1, 0, 1) for b in (-1, 0, 1)) for r, c in cs]
    stray = sum(I[r][c] == 2 and (r, c) not in box for r in range(19) for c in range(19))
    print(f"9caba7c3 pair {k}: windows {len(cs)} reds/window {reds} stray reds {stray}")

for k, p in enumerate(pairs("aa300dc3")):
    g = p["input"]; res = []
    for dd in (1, -1):
        for d in range(-10, 10):
            cnt = sum(1 for r in range(10) for c in [(r - d) if dd == 1 else (9 - r - d)]
                      if 0 <= c < 10 and g[r][c] == 0)
            res.append((cnt, dd, d))
    m = max(res)[0]
    print(f"aa300dc3 pair {k}: max {m} maxima (count, slope, offset) {[x for x in res if x[0] == m]}")

glyphs = {k: tuple(sorted(v)) for k, v in common.letter_map().items()}
print("d94c3b52 letter_map glyphs:", len(glyphs), "distinct:", len(set(glyphs.values())))

print("e0fb7511 black density:", [round(sum(v == 0 for r in p["input"] for v in r) / 169, 3) for p in pairs("e0fb7511")],
      "azure cells:", [sum(v == 8 for r in p["output"] for v in r) for p in pairs("e0fb7511")])

from tasks import task_bd283c4a as bd
ties = 0
for _ in range(n):
    cnt = collections.Counter(v for r in bd.generate()["input"] for v in r)
    ties += len(set(cnt.values())) < len(cnt)
print(f"bd283c4a native inputs with tied colour counts: {ties}/{n}")
