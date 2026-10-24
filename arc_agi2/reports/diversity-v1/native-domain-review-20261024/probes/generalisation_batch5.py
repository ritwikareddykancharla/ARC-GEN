"""Batch-5 follow-up probe, read-only. Run from the worktree root with PYTHONPATH=.

Usage: generalisation_batch5.py [N] [SEED]

Tests whether restrictions that the first batch-5 draft treated as adequate are
rule-derived or incidental, by running the CURRENT certified factory programs
(build_program(d4=0, identity palette), demonstrations unused) on inputs the
native constructors cannot produce, against an independent re-implementation of
each rule. Nothing is written; no constructor, factory or verifier is changed.
A pass here is evidence about program support, not a certificate.

  * 27f8ce4f / 48f8583b / 5b6cbef5 / 8e2edd66: H x W inputs, H, W in 2..5
    independently (the rule-derived bound is H*H, W*W <= 30), with each
    family's own selection guard (unique modal colour / unique minority colour /
    non-empty binary mask). Also replays every canonical pair through the
    independent reference.
  * 4cd1b7b2: blank counts 1..8 produced by the constructor's own strip-blanking
    scheme (one blank per still-complete row or column); checks that the
    constructor's propagation solver restores the Latin square and that the
    factory agrees.
  * 8ba14f53: native scenes padded with 0..4 blank rows/columns on each side;
    checks the factory still returns the constructor's output.
  * 833966f4: 5 x W inputs (W 1..30); checks the factory swaps rows 0/1 and 3/4.
"""
import collections
import random
import sys

sys.path.insert(0, '.')
from arc_agi2 import runtime  # noqa: E402

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
N = int(ARGS[0]) if ARGS else 400
SEED = int(ARGS[1]) if len(ARGS) > 1 else 0


def program(tid):
    ns = {}
    src = open(f"arc_agi2/direct_factories/task_{tid}.py").read()
    exec(src, ns)
    prog = {}
    exec(ns["build_program"](0, list(range(10))), prog)
    return lambda g: [list(map(int, r)) for r in prog["solve"]([], g)]


def pairs(tid):
    c = runtime.reference(tid)["canonical"]
    return c["train"] + c["test"]


def tile(g, sel, invert=False):
    """Self-tiling reference: block (r, c) holds g (or its inverse) where sel(r, c)."""
    h, w = len(g), len(g[0])
    out = [[0] * (w * w) for _ in range(h * h)]
    ink = next((v for r in g for v in r if v), 0)
    for r in range(h):
        for c in range(w):
            if not sel(r, c):
                continue
            for y in range(h):
                for x in range(w):
                    v = g[y][x]
                    out[r * h + y][c * w + x] = (0 if v else ink) if invert else v
    return out


def modal(g):
    cnt = collections.Counter(v for r in g for v in r)
    top = sorted(cnt.values())[-2:]
    return None if len(top) > 1 and top[0] == top[1] else cnt.most_common(1)[0][0]


def minority(g):
    cnt = collections.Counter(v for r in g for v in r)
    low = sorted(cnt.values())
    return None if len(low) > 1 and low[0] == low[1] else min(cnt, key=cnt.get)


def ref(tid, g):
    if tid == "27f8ce4f":
        m = modal(g)
        return tile(g, lambda r, c: g[r][c] == m)
    if tid == "48f8583b":
        m = minority(g)
        return tile(g, lambda r, c: g[r][c] == m)
    if tid == "5b6cbef5":
        return tile(g, lambda r, c: g[r][c] != 0)
    if tid == "8e2edd66":
        return tile(g, lambda r, c: g[r][c] == 0, invert=True)


def draw(tid, h, w, rng):
    while True:
        if tid in ("27f8ce4f", "48f8583b"):
            k = rng.randint(2 if tid == "48f8583b" else 3, 5)
            cols = rng.sample(range(1, 10), k)
            g = [[rng.choice(cols) for _ in range(w)] for _ in range(h)]
            if (modal if tid == "27f8ce4f" else minority)(g) is not None:
                return g
        else:
            ink = rng.randint(1, 9)
            g = [[ink if rng.random() < 0.5 else 0 for _ in range(w)] for _ in range(h)]
            if any(v for r in g for v in r) and (tid != "8e2edd66" or any(0 in r for r in g)):
                return g


print("== self-tiling families: canonical replay through the independent reference, then 2..5 x 2..5")
for i, tid in enumerate(("27f8ce4f", "48f8583b", "5b6cbef5", "8e2edd66")):
    rng = random.Random(SEED * 100 + i)
    solve = program(tid)
    can = all(ref(tid, p["input"]) == p["output"] for p in pairs(tid))
    agree = total = 0
    shapes = set()
    for _ in range(N):
        h, w = rng.randint(2, 5), rng.randint(2, 5)
        g = draw(tid, h, w, rng)
        shapes.add((h, w))
        total += 1
        agree += solve(g) == ref(tid, g)
    print(f"{tid}: reference reproduces canonical {can}; factory == reference on {agree}/{total} "
          f"inputs over {len(shapes)} H x W shapes (2..5 each)")

print("== 4cd1b7b2: blank counts reachable by the strip scheme and solved by propagation")
from tasks import task_4cd1b7b2 as m4  # noqa: E402
solve4 = program("4cd1b7b2")
rng = random.Random(SEED * 100 + 10)


def latin(rng):
    rows = []
    for _ in range(4):
        while True:
            cand = rng.sample([1, 2, 3, 4], 4)
            if all(r[c] != cand[c] for r in rows for c in range(4)):
                break
        rows.append(cand)
    return rows


res = collections.defaultdict(lambda: [0, 0, 0])
for _ in range(N * 10):
    sq = latin(rng)
    g = [r[:] for r in sq]
    strips = rng.sample([(d, v) for d in (0, 1) for v in range(4)], 8)
    k_target = rng.randint(1, 8)
    k = 0
    for d, v in strips:
        if k == k_target:
            break
        if d == 1 and sum(g[v]) == 10:
            g[v][rng.randint(0, 3)] = 0
            k += 1
        if d == 0 and k < k_target and sum(g[r][v] for r in range(4)) == 10:
            g[rng.randint(0, 3)][v] = 0
            k += 1
    out = m4.generate(colors=[x for r in g for x in r])["output"]
    res[k][0] += 1
    res[k][1] += out == sq
    res[k][2] += solve4(g) == sq
print("4cd1b7b2: blanks -> (scenes, constructor solver restores square, factory restores square): "
      + ", ".join(f"{k}: {tuple(v)}" for k, v in sorted(res.items())))

print("== 8ba14f53: native scenes padded with blank margins")
from tasks import task_8ba14f53 as m8  # noqa: E402
solve8 = program("8ba14f53")
rng = random.Random(SEED * 100 + 20)
random.seed(SEED * 100 + 21)
agree = 0
shapes = set()
for _ in range(N):
    p = m8.generate()
    t, b, l, r = (rng.randint(0, 4) for _ in range(4))
    w = 9 + l + r
    g = [[0] * w for _ in range(t)] + [[0] * l + row + [0] * r for row in p["input"]] + [[0] * w for _ in range(b)]
    shapes.add((len(g), w))
    agree += solve8(g) == p["output"]
print(f"8ba14f53: factory returns the constructor output on {agree}/{N} padded scenes over {len(shapes)} canvas shapes")

print("== 833966f4: 5 x W grids (each column five distinct colours), row swaps 0<->1 and 3<->4")
solve83 = program("833966f4")
rng = random.Random(SEED * 100 + 30)
agree = 0
for _ in range(N):
    w = rng.randint(1, 30)
    cols = [rng.sample(range(10), 5) for _ in range(w)]
    g = [[cols[c][r] for c in range(w)] for r in range(5)]
    want = [g[1], g[0], g[2], g[4], g[3]]
    agree += solve83(g) == want
print(f"833966f4: factory applies the row swaps to {agree}/{N} 5 x W inputs (W 1..30)")
