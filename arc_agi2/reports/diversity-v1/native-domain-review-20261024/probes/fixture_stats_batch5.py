"""Batch-5 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Usage: fixture_stats_batch5.py [N_NATIVE] [SEED] [--timing]

Prints the canonical-fixture statistics and small native measurements quoted
in batch-5 reviews. Nothing is written; constructors are only called. Every
section reseeds from SEED plus a fixed per-section offset, so sections are
independent and the default output is byte-identical between runs. Timing is
only printed with --timing (wall-clock, not reproducible).

Sections
  * finite domains: exact counts by enumerating each sampler's parameter space
    (2072aba6, 3979b1a8, 5ad8a7c0, 66e6c45b, 833966f4, 8b28cd80, 6ea4a07e,
    8e2edd66, 59341089, 5b6cbef5) and the 8719f442 sprite-mask bound plus the
    masks reached in N draws; 4cd1b7b2 distinct inputs reached in N draws.
  * canonical vs native constraints: 6d1d5c90 distinct colours and filler
    share; 2072aba6 / 27f8ce4f / 48f8583b / 4cd1b7b2 / 87ab05b8 / 46c35fc7 /
    79cce52d / 626c0bcc / 68b67ca3 / 8ba14f53 fixture parameters checked
    against the native sampler guards; 337b420f collision displacement.
  * panel families without an evidence gate (3d31c5b3, 6a11f6da priority;
    506d28a5, 5d2a5c43 OR; 66f2d22f NOR): share of independent 3-demo +
    query episodes whose demonstrations leave the query answer ambiguous
    within the cell-wise truth-table / priority-order hypothesis class.
  * batch-D families (195ba7dc, 281123b4, 31d5ba1a, 34b99a2b): current input
    shapes in N draws and canonical vs native panel fill density.
  * 6ea4a07e: share of 3-demo episodes whose demos lack the query ink colour.
"""
import collections
import itertools
import random
import statistics
import sys
import time

sys.path.insert(0, '.')
import common  # noqa: E402
from arc_agi2 import runtime  # noqa: E402

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
N = int(ARGS[0]) if ARGS else 2000
SEED = int(ARGS[1]) if len(ARGS) > 1 else 0
TIMING = '--timing' in sys.argv


def section(offset):
    random.seed(SEED * 1000 + offset)


def pairs(tid):
    c = runtime.reference(tid)["canonical"]
    return c["train"] + c["test"]


def key(g):
    return tuple(map(tuple, g))


def mod(tid):
    return __import__(f"tasks.task_{tid}", fromlist=["generate"])


# ---------------------------------------------------------------- finite domains
print("== finite native domains (exact enumeration of sampler parameter space)")
fin = {
    "2072aba6": sum(1 for b in itertools.product((0, 1), repeat=9) if 3 <= sum(b) <= 6),
    "3979b1a8": len(list(itertools.permutations(range(1, 10), 3))),
    "5ad8a7c0": sum(1 for c in itertools.product(range(-1, 3), repeat=4) if max(c) != -1),
    "66e6c45b": len(list(itertools.permutations(range(1, 10), 4))),
    "833966f4": len(list(itertools.permutations(range(10), 5))),
    "8b28cd80": 9 * 9,
    "6ea4a07e": 3 * (2 ** 9 - 1),
    "8e2edd66": 9 * (2 ** 9 - 1),
    "59341089": 3 ** 9,
    "5b6cbef5": 4 * (2 ** 16 - 1),
}
for tid, n in fin.items():
    print(f"{tid}: {n} native inputs")
# verify the enumerations map to distinct inputs for the small ones
for tid, params in (("2072aba6", [dict(colors=list(b)) for b in itertools.product((0, 1), repeat=9)
                                   if 3 <= sum(b) <= 6]),
                    ("5ad8a7c0", [dict(cols=list(c)) for c in itertools.product(range(-1, 3), repeat=4)
                                   if max(c) != -1]),
                    ("3979b1a8", [dict(colors=list(p)) for p in itertools.permutations(range(1, 10), 3)])):
    m = mod(tid)
    ins = {key(m.generate(**kw)["input"]) for kw in params}
    print(f"{tid}: enumerated parameters give {len(ins)} distinct inputs")

# 8719f442: masks that are diagonally connected and touch every row and column
masks = []
for bits in itertools.product((0, 1), repeat=9):
    px = [(i // 3, i % 3) for i in range(9) if bits[i]]
    if not px or {r for r, _ in px} != {0, 1, 2} or {c for _, c in px} != {0, 1, 2}:
        continue
    if common.diagonally_connected(px):
        masks.append(bits)
section(1)
m = mod("8719f442")
reached = collections.Counter(key(m.generate()["input"]) for _ in range(N * 5))
fx = [key(p["input"]) for p in pairs("8719f442")]
print(f"8719f442: {len(masks)} diagonally connected 3x3 masks cover all rows/cols; "
      f"{len(reached)} reached in {N * 5} native draws; fixture inputs reached: "
      f"{[f in reached for f in fx]}")
counts = sorted(collections.Counter(sum(v != 0 for r in k for v in r) for k in reached).items())
print(f"8719f442: pixel counts of reached masks {counts}")
# Structural: conway_sprite deletes at most tries=5 of 9 entries, so >= 4 (row, col)
# entries remain; 3 distinct pixels therefore need a duplicate pair, and
# diagonally_connected never marks a duplicate's second index, so it rejects.
print(f"8719f442: diagonally_connected with a duplicate pair -> "
      f"{common.diagonally_connected([(0, 0), (1, 1), (1, 1), (2, 2)])}; without -> "
      f"{common.diagonally_connected([(0, 0), (1, 1), (2, 2)])}; fixture pixel counts "
      f"{[sum(v != 0 for r in p['input'] for v in r) for p in pairs('8719f442')]}")

section(2)
m = mod("4cd1b7b2")
seen = set()
zeros = collections.Counter()
for _ in range(N):
    g = m.generate()["input"]
    seen.add(key(g))
    zeros[sum(v == 0 for r in g for v in r)] += 1
print(f"4cd1b7b2: {len(seen)} distinct inputs in {N} draws; blank counts {sorted(zeros.items())}; "
      f"fixture blank counts {[sum(v == 0 for r in p['input'] for v in r) for p in pairs('4cd1b7b2')]}")

# ---------------------------------------------------------- canonical vs native
print("== canonical fixtures vs native sampler guards")


def ncol(g):
    return len({v for r in g for v in r})


section(3)
m = mod("6d1d5c90")
nat = collections.Counter()
filler = []
for _ in range(N):
    g = m.generate()["input"]
    nat[ncol(g)] += 1
    filler.append(sum(v == 5 for r in g for v in r[1:]) / 36)
fxc = [ncol(p["input"]) for p in pairs("6d1d5c90")]
fxf = [round(sum(v == 5 for r in p["input"] for v in r[1:]) / 36, 3) for p in pairs("6d1d5c90")]
print(f"6d1d5c90: fixture distinct colours {fxc} (line 40 requires exactly 7); native {sorted(nat.items())}")
print(f"6d1d5c90: filler-5 share of the 6x6 picture: fixture {fxf}; native median "
      f"{statistics.median(filler):.3f} range {min(filler):.3f}-{max(filler):.3f}")
# how often the native bar loop would have produced 8 colours (the canonical count)
section(4)
eight = tries = 0
for _ in range(N):
    colors = [6, 5, 5, 5, 5, 5, 5] * 6
    for _ in range(10):
        length = random.randint(2, 4)
        row = random.randint(0, 6 - length)
        col = random.randint(0, 5)
        cdir = random.randint(0, 1)
        color = random.choice([1, 3, 4, 8, 9])
        for i in range(length):
            if cdir:
                colors[(row + i) * 7 + col + 1] = color
            else:
                colors[col * 7 + row + i + 1] = color
    colors[random.randint(0, 5) * 7] = 2
    tries += 1
    eight += len(set(colors)) == 8
print(f"6d1d5c90: unfiltered line-29..39 scenes with 8 colours (rejected by line 40): {eight}/{tries}")

print(f"2072aba6: fixture cell counts {[sum(v != 0 for r in p['input'] for v in r) for p in pairs('2072aba6')]} "
      f"(native 3..6)")


def counts_of(g):
    return sorted(collections.Counter(v for r in g for v in r).values())


print(f"27f8ce4f: fixture (colours, sorted counts) {[(ncol(p['input']), counts_of(p['input'])) for p in pairs('27f8ce4f')]} "
      f"(native 3..5 colours, unique max)")
print(f"48f8583b: fixture (colours, sorted counts) {[(ncol(p['input']), counts_of(p['input'])) for p in pairs('48f8583b')]} "
      f"(native 2..4 colours, unique min)")
print(f"87ab05b8: fixture non-6 non-2 cells {[sum(v not in (6, 2) for r in p['input'] for v in r) for p in pairs('87ab05b8')]} "
      f"(native at most 7)")


def comps(g, bg):
    h, w = len(g), len(g[0])
    seen, out = set(), []
    for y in range(h):
        for x in range(w):
            if g[y][x] == bg or (y, x) in seen:
                continue
            st, cells = [(y, x)], []
            seen.add((y, x))
            while st:
                cy, cx = st.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and (ny, nx) not in seen and g[ny][nx] != bg:
                        seen.add((ny, nx))
                        st.append((ny, nx))
            out.append(cells)
    return out


print(f"46c35fc7: fixture 3x3 box counts {[len(comps(p['input'], 7)) for p in pairs('46c35fc7')]} (native 1..2)")
print(f"79cce52d: fixture picture colour counts {[sorted(collections.Counter(v for r in p['input'][1:] for v in r[1:]).values()) for p in pairs('79cce52d')]} "
      f"(native: six colours, each >= 4 cells)")
# 626c0bcc: pieces = cells per hue / piece size; hue 1 is a 2x2 square
pc = []
for p in pairs("626c0bcc"):
    c = collections.Counter(v for r in p["output"] for v in r if v)
    pc.append({h: c[h] // (4 if h == 1 else 3) for h in sorted(c)})
print(f"626c0bcc: fixture pieces per hue {pc} (native 4..5 pieces, all four hues)")
print(f"68b67ca3: fixture lattice rows/cols all non-empty "
      f"{[all(any(p['output'][i][j] for j in range(3)) and any(p['output'][j][i] for j in range(3)) for i in range(3)) for p in pairs('68b67ca3')]}")
# 8ba14f53: holes per box (left to right) and total output rows used
hb = []
for p in pairs("8ba14f53"):
    o = p["output"]
    cs = []
    for r in o:
        for v in r:
            if v and v not in cs:
                cs.append(v)
    hb.append([sum(v == c for r in o for v in r) for c in cs])
print(f"8ba14f53: fixture holes per box, left box first {hb} (native interior up to 3x2 = 6)")

# 337b420f: canonical displaced pieces vs native disjoint union
m = mod("337b420f")
for i, p in enumerate(pairs("337b420f")):
    g, o = p["input"], p["output"]
    plain = [[8] * 5 for _ in range(5)]
    for left in (0, 6, 12):
        cs = comps([r[left:left + 5] for r in g], 8)
        cs = [c for c in cs if all(g[y][left + x] != 0 for y, x in c)]
        cs.sort(key=len, reverse=True)
        for y, x in cs[0]:
            plain[y][x] = g[y][left + x]
    if plain != o:
        print(f"337b420f: canonical pair {i} is not the plain overlay of largest pieces (collision case)")
section(5)
overlaps = 0
for _ in range(min(N, 500)):
    g = m.generate()["input"]
    occ = collections.Counter()
    for left in (0, 6, 12):
        cs = comps([r[left:left + 5] for r in g], 8)
        cs.sort(key=len, reverse=True)
        occ.update(cs[0])
    overlaps += any(v > 1 for v in occ.values())
print(f"337b420f: native draws whose largest pieces overlap: {overlaps}/{min(N, 500)}")

# ------------------------------------------------- ungated panel-family contexts
print("== panel families without an evidence gate: ambiguous 3-demo contexts")


def panels_rows(g, k, sep=False):
    """Split stacked panels (k equal bands along rows, optional 1-row separators)."""
    h = (len(g) - (k - 1 if sep else 0)) // k
    step = h + (1 if sep else 0)
    return [g[i * step:i * step + h] for i in range(k)]


def panels_cols(g, k, sep=False):
    w = (len(g[0]) - (k - 1 if sep else 0)) // k
    step = w + (1 if sep else 0)
    return [[r[i * step:i * step + w] for r in g] for i in range(k)]


def boolean_ambiguous(split, demos, query, bg=0):
    table = {}
    for d in demos:
        a, b = split(d["input"])
        for ra, rb, ro in zip(a, b, d["output"]):
            for x, y, v in zip(ra, rb, ro):
                table.setdefault((x != bg, y != bg), v)
    a, b = split(query["input"])
    return any((x != bg, y != bg) not in table for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def priority_ambiguous(split, colours, demos, query, bg=0):
    def predict(g, order):
        ps = split(g)
        rank = {c: i for i, c in enumerate(order)}
        out = []
        for y in range(len(ps[0])):
            row = []
            for x in range(len(ps[0][0])):
                cell = [p[y][x] for p in ps if p[y][x] != bg]
                row.append(min(cell, key=rank.__getitem__) if cell else bg)
            out.append(row)
        return out
    alive = [o for o in itertools.permutations(colours)
             if all(predict(d["input"], o) == d["output"] for d in demos)]
    return len({key(predict(query["input"], o)) for o in alive}) != 1


PANEL = {
    "3d31c5b3": ("priority", lambda g: panels_rows(g, 4), (5, 4, 8, 2)),
    "6a11f6da": ("priority", lambda g: panels_rows(g, 3), (6, 1, 8)),
    "506d28a5": ("boolean", lambda g: panels_rows(g, 2, sep=True), None),
    "5d2a5c43": ("boolean", lambda g: panels_cols(g, 2, sep=True), None),
    "66f2d22f": ("boolean", lambda g: panels_cols(g, 2), None),
}
for off, (tid, (kind, split, cols)) in enumerate(PANEL.items()):
    m = mod(tid)
    can = pairs(tid)
    section(10 + off)
    amb = 0
    for _ in range(N):
        four = [m.generate() for _ in range(4)]
        demos, query = four[:3], four[3]
        if kind == "priority":
            amb += priority_ambiguous(split, cols, demos, query)
        else:
            amb += boolean_ambiguous(split, demos, query)
    canon = [priority_ambiguous(split, cols, [p for j, p in enumerate(can) if j != i][:3], can[i])
             if kind == "priority" else
             boolean_ambiguous(split, [p for j, p in enumerate(can) if j != i][:3], can[i])
             for i in range(len(can))]
    print(f"{tid} ({kind}): ambiguous native episodes {amb}/{N}; canonical leave-one-out "
          f"(first 3 others as demos) ambiguous {sum(canon)}/{len(can)}")

# ------------------------------------------------------------- batch-D families
print("== batch-D families: current default domain")
BD = {
    "195ba7dc": lambda g: (panels_cols(g, 2, sep=True)),
    "34b99a2b": lambda g: (panels_cols(g, 2, sep=True)),
    "281123b4": lambda g: (panels_cols(g, 4, sep=True)),
    "31d5ba1a": lambda g: (panels_rows(g, 2)),
}
for off, (tid, split) in enumerate(BD.items()):
    m = mod(tid)
    section(20 + off)
    shapes, uniq, dens = collections.Counter(), set(), []
    for _ in range(N):
        g = m.generate()["input"]
        shapes[(len(g), len(g[0]))] += 1
        uniq.add(key(g))
        for p in split(g):
            dens.append(sum(v != 0 for r in p for v in r) / (len(p) * len(p[0])))
    fd = [round(sum(v != 0 for r in p for v in r) / (len(p) * len(p[0])), 2)
          for c in pairs(tid) for p in split(c["input"])]
    q = statistics.quantiles(dens, n=20)
    print(f"{tid}: {len(shapes)} input shapes, {len(uniq)} unique in {N}; max draws on one shape "
          f"{max(shapes.values())}; panel fill native 5-95% {q[0]:.2f}-{q[-1]:.2f}; "
          f"fixture panels {min(fd)}-{max(fd)}")

# ------------------------------------------------------------------- 6ea4a07e
section(30)
m = mod("6ea4a07e")
miss = 0
for _ in range(N):
    four = [m.generate() for _ in range(4)]
    ink = lambda g: {v for r in g for v in r} - {0}
    demo_inks = set().union(*(ink(d["input"]) for d in four[:3]))
    miss += not ink(four[3]["input"]) <= demo_inks
print(f"6ea4a07e: query ink absent from 3 demos in {miss}/{N} independent episodes "
      f"(colour_evidence resamples these)")

if TIMING:
    print("== timing (wall clock, not reproducible)")
    for tid in ("626c0bcc", "337b420f", "79cce52d", "6d1d5c90", "4cd1b7b2", "8ba14f53",
                "27f8ce4f", "48f8583b", "46c35fc7"):
        m = mod(tid)
        section(40)
        ts = []
        for _ in range(200):
            t = time.perf_counter()
            m.generate()
            ts.append(time.perf_counter() - t)
        print(f"{tid}: median {statistics.median(ts) * 1e3:.2f} ms, max {max(ts) * 1e3:.1f} ms over 200")
