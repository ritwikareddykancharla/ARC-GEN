"""Batch-4 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Usage: fixture_stats_batch4.py [N_NATIVE] [SEED]

Prints the canonical-fixture statistics and small native measurements quoted
in batch-4 reviews. Nothing is written; constructors are only called.
  * e45ef808: native rate of tied tallest / tied shortest bars; fixture ties.
  * f1bcbc2c: exhaustive count of distinct native inputs (all parameters).
  * f3e62deb / 17cae0c1: native domain size and the rate at which a query
    (independent native draw) shows a colour/symbol absent from 3 demos.
  * fd02da9e: exhaustive count of distinct native inputs.
  * 0692e18c: distinct conway_sprite(3, 3) masks reached; fixture masks.
  * 15696249: per-colour cell counts in canonical inputs vs native.
  * 31adaf00: grey fraction of canonical vs current native inputs.
  * edcc2ff0: native rate of zero-count legend colours; canonical bar lengths.
  * ff2825db: share of line-64/65 parameter draws whose clutter box is clipped.
"""
import collections
import itertools
import random
import sys

sys.path.insert(0, '.')
import common  # noqa: E402
from arc_agi2 import runtime  # noqa: E402

n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 0)


def pairs(tid):
    c = runtime.reference(tid)["canonical"]
    return c["train"] + c["test"]


def key(g):
    return tuple(map(tuple, g))


# e45ef808 -----------------------------------------------------------------
from tasks import task_e45ef808 as m  # noqa: E402


def bar_lengths(g):
    return [sum(g[r][c] == 6 for r in range(12)) for c in range(12)]


def ties(ls):
    return ls.count(max(ls)) > 1, ls.count(min(ls)) > 1


fx = [ties(bar_lengths(p["input"])) for p in pairs("e45ef808")]
tt = ts = 0
for _ in range(n):
    a, b = ties(bar_lengths(m.generate()["input"]))
    tt += a
    ts += b
print(f"e45ef808 fixture (tallest tied, shortest tied): {fx}; native tallest tied {tt}/{n}, shortest tied {ts}/{n}")

# f1bcbc2c -----------------------------------------------------------------
from tasks import task_f1bcbc2c as m  # noqa: E402

seen = set()
valid = 0
for k in (3, 4, 5):
    for lengths in itertools.product(range(3, 8), repeat=k):
        for col in range(1, 5):
            for pos in [-1, 6, 7, 8, 9]:
                g = m.generate(flop=0, col=col, pos=pos, lengths=list(lengths))["input"]
                if g is None:
                    continue
                valid += 1
                seen.add(key(g))
flopped = {key(common.flop([list(r) for r in g])) for g in seen}
fix = [key(p["input"]) for p in pairs("f1bcbc2c")]
print(f"f1bcbc2c valid parameter sets (flop=0): {valid}; distinct inputs flop=0: {len(seen)}; "
      f"with flop: {len(seen | flopped)}; fixtures inside: {sum(f in seen | flopped for f in fix)}/{len(fix)}")


# f3e62deb, 17cae0c1 episode coverage ---------------------------------------
def episode_unseen(gen, symbols, episodes):
    miss = 0
    for _ in range(episodes):
        demos = [symbols(gen()) for _ in range(3)]
        query = symbols(gen())
        if not set(query) <= set().union(*demos):
            miss += 1
    return miss


from tasks import task_f3e62deb as m  # noqa: E402

dom = {key(m.generate(row=r, col=c, color=k)["input"]) for r in range(2, 6) for c in range(2, 6) for k in (3, 4, 6, 8)}
sym = lambda p: {v for row in p["input"] for v in row if v}  # noqa: E731
print(f"f3e62deb native domain: {len(dom)} inputs; canonical colours train {[sorted(sym(p)) for p in pairs('f3e62deb')[:6]]} "
      f"test {[sorted(sym(p)) for p in pairs('f3e62deb')[6:]]}; "
      f"episodes whose query colour is absent from 3 demos: {episode_unseen(m.generate, sym, 10 * n)}/{10 * n}")

from tasks import task_17cae0c1 as m  # noqa: E402

dom = {key(m.generate(colors=list(c))["input"]) for c in itertools.permutations([1, 3, 4, 6, 9], 3)}
osym = lambda p: {p["output"][0][3 * i] for i in range(3)}  # noqa: E731
print(f"17cae0c1 native domain: {len(dom)} inputs; canonical train symbols {sorted(set().union(*[osym(p) for p in pairs('17cae0c1')[:4]]))}; "
      f"episodes whose query has a symbol absent from 3 demos: {episode_unseen(m.generate, osym, 10 * n)}/{10 * n}")

# fd02da9e ------------------------------------------------------------------
dom = set()
for cs in itertools.permutations(range(1, 10), 4):
    cs = [c if c != 7 else 0 for c in cs]
    for mask in itertools.product((0, 1), repeat=4):
        t = tuple(c if keep else 7 for c, keep in zip(cs, mask))
        if len(set(t)) > 1:
            dom.add(t)
pat = collections.Counter(tuple(v != 7 for v in t) for t in dom)
print(f"fd02da9e native domain: {len(dom)} inputs over {len(pat)} occupied-corner patterns; "
      f"canonical corners {[(p['input'][0][0], p['input'][0][7], p['input'][7][0], p['input'][7][7]) for p in pairs('fd02da9e')]}")

# 0692e18c ------------------------------------------------------------------
masks = collections.Counter()
for _ in range(20 * n):
    rows, cols = common.conway_sprite(3, 3)
    masks[frozenset(zip(rows, cols))] += 1
full_cover = 0
for bits in itertools.product((0, 1), repeat=9):
    cells = {(i // 3, i % 3) for i in range(9) if bits[i]}
    if all(any((r, c) in cells for c in range(3)) for r in range(3)) and \
            all(any((r, c) in cells for r in range(3)) for c in range(3)):
        full_cover += 1
fixm = [frozenset((r, c) for r in range(3) for c in range(3) if p["input"][r][c]) for p in pairs("0692e18c")]
sizes = collections.Counter(len(k) for k in masks)
print(f"0692e18c distinct masks in {20 * n} sprites: {len(masks)} (masks with every row and column occupied: {full_cover}); "
      f"cells per reached mask {dict(sorted(sizes.items()))}; fixture masks reached {sum(f in masks for f in fixm)}/{len(fixm)}")

# 15696249 ------------------------------------------------------------------
from tasks import task_15696249 as m  # noqa: E402

fxc = [sorted(collections.Counter(v for r in p["input"] for v in r).values()) for p in pairs("15696249")]
nat = collections.Counter(tuple(sorted(collections.Counter(v for r in m.generate()["input"] for v in r).values())) for _ in range(n))
print(f"15696249 canonical colour counts per input: {fxc}; native: {dict(nat)}")

# 31adaf00 ------------------------------------------------------------------
from tasks import task_31adaf00 as m  # noqa: E402

frac = lambda g: sum(v == 5 for r in g for v in r) / (len(g) * len(g[0]))  # noqa: E731
fxg = [round(frac(p["input"]), 2) for p in pairs("31adaf00")]
k = max(50, n // 10)
n10 = sorted(frac(m.generate(width=10, height=10)["input"]) for _ in range(k))
nr = sorted(frac(m.generate()["input"]) for _ in range(k))
print(f"31adaf00 canonical grey fraction {fxg}; native 10x10 (k={k}) min/median/max "
      f"{n10[0]:.2f}/{n10[k // 2]:.2f}/{n10[-1]:.2f}; native random canvas {nr[0]:.2f}/{nr[k // 2]:.2f}/{nr[-1]:.2f}; "
      f"10x10 draws with grey > 0.5: {sum(x > 0.5 for x in n10)}/{k}")

# edcc2ff0 ------------------------------------------------------------------
from tasks import task_edcc2ff0 as m  # noqa: E402

zero = 0
for _ in range(n):
    p = m.generate()
    bars = [sum(v != 0 for v in p["output"][2 * i + 1]) for i in range(3)]
    zero += 0 in bars
print(f"edcc2ff0 native draws with a zero-count legend colour: {zero}/{n}; "
      f"canonical bar lengths {[[sum(v != 0 for v in p['output'][2 * i + 1]) for i in range(3)] for p in pairs('edcc2ff0')]}")

# ff2825db ------------------------------------------------------------------
tot = clip = 0.0
for wide in range(2, 9):
    for tall in range(2, 8):
        for brow in range(0, 8 - wide + 1):
            for bcol in range(0, 7 - tall + 1):
                w = 1 / (7 * 6 * (8 - wide + 1) * (7 - tall + 1))
                tot += w
                clip += w * (brow + tall > 7 or bcol + wide > 8)
print(f"ff2825db probability that the line-64/65 clutter box is clipped by the 7x8 interior: {clip / tot:.3f}")
