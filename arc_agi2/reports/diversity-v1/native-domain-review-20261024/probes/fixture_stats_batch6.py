"""Batch-6 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Usage: fixture_stats_batch6.py [N] [SEED]

Prints the measurements quoted in the batch-6 semantic reviews. Nothing is
written; constructors are only called, and certified programs are obtained
through the production lookups (certified_factory_source / certified_source,
d4 = 0, identity palette), which return None if a certificate is stale. Every
section reseeds from SEED plus a fixed offset, so output is byte-identical
between runs.

Sections
  A. finite domains, exact by enumerating each sampler's parameter space
     (be03b35f, e3f79277, e6de6e8f, 8597cfd7, 72207abc, ca8de6ea, ed74f2f2,
     ed98d772, b1fc8b8e) and distinct inputs reached in N native draws.
  B. canonical fixtures against native sampler guards: b4a43f3b (segments
     needed per pattern), 18447a8d (band count), d017b73f (segments, widths),
     42f83767 (stencil pixel counts), e87109e9 (block sizes, separation,
     trace flags), dd2401ed (native label of the extra=1 pair, blue parity),
     ba1aa698 (extra step), 9110e3c5 / a8610ef7 / bbb1b8b6 statistics, and
     ungated truth-table ambiguity for d19f7514 / e133d23d / e345f17b.
  C. program generalisation: certified programs on inputs the native
     constructors cannot produce, against an independent reference that
     first replays every canonical pair (or against the constructor's own
     explicit-parameter path where noted). A pass is evidence of program
     support, not a certificate. Draws keep the background colour modal
     (9b30e358, e3f79277, e87109e9), because the programs read it as the
     modal colour; scenes where the motif covers most of the canvas were
     seen to fail for that reason alone and are out of scope here.
"""
import ast
import collections
import itertools
import json
import random
import sys

sys.path.insert(0, '.')
import common  # noqa: E402,F401
from arc_agi2 import runtime  # noqa: E402
from arc_agi2.direct_certificates import (certified_factory_source,  # noqa: E402
                                          certified_source)

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
N = int(ARGS[0]) if ARGS else 400
SEED = int(ARGS[1]) if len(ARGS) > 1 else 0
ID = list(range(10))


def section(offset):
    random.seed(SEED * 1000 + offset)
    return random.Random(SEED * 1000 + offset + 500)


def pairs(tid):
    c = runtime.reference(tid)["canonical"]
    return c["train"] + c["test"]


def key(g):
    return tuple(map(tuple, g))


def mod(tid):
    return __import__(f"tasks.task_{tid}", fromlist=["generate"])


def validate_kwargs(tid):
    """Explicit keyword arguments of every generate() call in validate()."""
    tree = ast.parse(open(f"tasks/task_{tid}.py").read())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate")
    out = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "generate":
            out.append((node.lineno, {k.arg: ast.literal_eval(k.value) for k in node.keywords}))
    return sorted(out, key=lambda t: t[0])


def program(tid):
    src = certified_factory_source(tid, 0, ID)
    kind = "direct_factory"
    if src is None:
        src = certified_source(tid)
        kind = "direct_certificate"
    if src is None:
        return None, "none"
    ns = {}
    exec(src, ns)
    return (lambda g, demos=(): [list(map(int, r)) for r in ns["solve"](list(demos), g)]), kind


def native_inputs(tid, n):
    m = mod(tid)
    return [key(m.generate()["input"]) for _ in range(n)]


def report(name, ok, total, extra=""):
    print(f"  {name}: {ok}/{total}{(' ' + extra) if extra else ''}")


# ---------------------------------------------------------------- A. finite
print("== A. finite domains (exact enumeration) and native reach")
section(1)
m = mod("be03b35f")
dom = {key(m.generate(colors=list(c))["input"]) for c in itertools.product((0, 1), repeat=4)
       if 0 < sum(c) < 4}
reach = set(native_inputs("be03b35f", N))
print(f"be03b35f: {len(dom)} inputs; {len(reach)} reached in {N} draws; all reached in domain {reach <= dom}")

section(2)
m = mod("e3f79277")
dom = {key(m.generate(length=L, color=c, flip=f, flop=o)["input"])
       for L in range(2, 7) for c in range(1, 10) if c != 7 for f in (0, 1) for o in (0, 1)}
reach = set(native_inputs("e3f79277", N))
print(f"e3f79277: {len(dom)} inputs (5 lengths x 8 colours x 4 corners); {len(reach)} reached in {N}")

section(3)
m = mod("e6de6e8f")
dom = {key(m.generate(commands=list(c))["input"]) for c in itertools.product((-1, 0, 1), repeat=5)
       if c.count(0) == 2}
print(f"e6de6e8f: {len(dom)} inputs (C(5,2) x 2^3)")

section(4)
m = mod("8597cfd7")
dom = set()
for h in (9, 11):
    t = h // 2
    for r in itertools.product(range(1, t + 1), repeat=2):
        for y in itertools.product(range(1, t + 1), repeat=2):
            p = m.generate(height=h, reds=list(r), yellows=list(y))
            if p["input"] is not None:
                dom.add(key(p["input"]))
print(f"8597cfd7: {len(dom)} inputs")

section(5)
m = mod("72207abc")
dom = set()
for w in (19, 29):
    for k in (2, 3):
        for cols in itertools.permutations(range(1, 10), k):
            dom.add(key(m.generate(width=w, colors=list(cols))["input"]))
print(f"72207abc: {len(dom)} inputs; orbits under palette x D4 = width x colour count = 4")

section(6)
print(f"ca8de6ea: 9P5 = {9 * 8 * 7 * 6 * 5} inputs, one geometry")

section(7)
masks = set()
for bits in range(512):
    px = [(r, c) for r in range(3) for c in range(3) if bits >> (3 * r + c) & 1]
    if not 4 <= len(px) <= 8:
        continue
    if {r for r, _ in px} != {0, 1, 2} or {c for _, c in px} != {0, 1, 2}:
        continue
    if common.diagonally_connected(sorted(px)):
        masks.add(bits)
m = mod("ed74f2f2")
reach = set(native_inputs("ed74f2f2", N))
print(f"ed74f2f2: {len(masks)} pattern masks (4..8 px, all rows/cols, 8-connected) x 3 key colours = "
      f"{3 * len(masks)} inputs; {len(reach)} reached in {N}")
can_px = [sum(v != 0 for r in p["output"] for v in r) for p in pairs("ed74f2f2")]
print(f"  canonical pattern pixel counts {can_px}")

section(8)
print(f"ed98d772: (2^9 - 2) x 9 = {(2 ** 9 - 2) * 9} inputs")

section(9)
m = mod("b1fc8b8e")
dom = set()
cells_l = [(0, 1), (1, 0), (1, 1)]
cells_s = [(0, 0), (0, 1), (1, 0), (1, 1)]
pos = [(r, c) for r in range(5) for c in range(5)]
for shape, cells in ((0, cells_l), (1, cells_s)):
    for combo in itertools.combinations(pos, 4):
        occ = set()
        good = True
        for r, c in combo:
            for dr, dc in cells:
                if (r + dr, c + dc) in occ:
                    good = False
                occ.add((r + dr, c + dc))
        if not good:
            continue
        if shape == 0 and not any((r, c) in occ for r, c in combo):
            continue
        dom.add((shape, frozenset(occ)))
print(f"b1fc8b8e: {len(dom)} inputs (L-tromino {sum(1 for s, _ in dom if s == 0)}, "
      f"2x2 {sum(1 for s, _ in dom if s == 1)})")
can_last = [all(v == 0 for v in p["input"][5]) for p in pairs("b1fc8b8e")]
can_conn = []
for p in pairs("b1fc8b8e"):
    cells = sorted((r, c) for r in range(6) for c in range(6) if p["input"][r][c])
    can_conn.append(common.connected(cells))
print(f"  canonical: bottom row blank {can_last}; 4-connected blob {can_conn}")
random.seed(SEED * 1000 + 9)
conn = 0
for _ in range(N):
    g = mod("b1fc8b8e").generate()["input"]
    cells = sorted((r, c) for r in range(6) for c in range(6) if g[r][c])
    conn += common.connected(cells)
report("native 4-connected blob", conn, N)

# ------------------------------------------------------- B. canonical guards
print("== B. canonical fixtures against native guards")
section(20)


def segments_needed(cells, n=6, limit=4):
    cells = set(cells)
    segs = []
    for r in range(n):
        for a in range(n):
            for b in range(a, n):
                s = frozenset((r, c) for c in range(a, b + 1))
                if s <= cells:
                    segs.append(s)
                t = frozenset((c, r) for c in range(a, b + 1))
                if t <= cells:
                    segs.append(t)
    segs = list(set(segs))
    for k in range(1, limit + 1):
        for combo in itertools.combinations(segs, k):
            if frozenset().union(*combo) == cells:
                return k
    return None


need = []
for p in pairs("b4a43f3b"):
    cells = [(r, c) for r in range(6) for c in range(6) if p["input"][7 + r][c]]
    need.append(segments_needed(cells))
print(f"b4a43f3b: axis segments needed per canonical pattern {need} (native draws exactly 3, line 35)")

section(21)
kw = validate_kwargs("18447a8d")
print(f"18447a8d: canonical band counts {[len(k['colors']) for _, k in kw]} (native randint(3, 4), line 52)")

section(22)
kw = validate_kwargs("d017b73f")
for ln, k in kw:
    h = k["hlengths"]
    mid, tail = (h[1:-1], h[-1]) if h[-1] == 1 else (h[1:], None)
    ok = 2 <= h[0] <= 3 and 3 <= len(mid) <= 4 and all(3 <= v <= 5 for v in mid)
    inw = sum(k["vlengths"]) + len(k["vlengths"]) - 1 + k["bump"]
    vok = 3 <= len(k["vlengths"]) <= 4 and all(2 <= v <= 3 for v in k["vlengths"])
    print(f"  d017b73f line {ln}: hlengths {h} native-reachable {ok}; vlengths {k['vlengths']} ok {vok}; "
          f"input width {inw}")
random.seed(SEED * 1000 + 22)
ws = collections.Counter(len(mod("d017b73f").generate()["input"][0]) for _ in range(N))
print(f"  native input widths in {N} draws: {dict(sorted(ws.items()))}")

section(23)
kw = validate_kwargs("42f83767")
for ln, k in kw:
    L = k["length"]
    px = [k["patterns"][i * L * L:(i + 1) * L * L].count("5") for i in range(len(k["subset"]))]
    print(f"  42f83767 line {ln}: L={L} stencil pixels {px}; native minimum L*L-L = {L * L - L}; "
          f"reachable {all(v >= L * L - L for v in px)}")

section(24)
m = mod("e87109e9")
kw = validate_kwargs("e87109e9")
for ln, k in kw:
    h = k["height"]
    blocks = [tuple(b) for b in k["blocks"]]
    sizes_ok = all(2 <= b[2] <= max(2, min(12, h - 4)) and 2 <= b[3] <= 14 for b in blocks)
    sq = k["square"]
    sq_rect = (sq[0], sq[1], sq[2], sq[2])
    apart = all(m._apart(b[:4], sq_rect, 1) for b in blocks) and all(
        m._apart(a[:4], b[:4], 1) for a, b in itertools.combinations(blocks, 2))
    body = m._build_body(h, k["bg"], tuple(sq), blocks)
    _, st = m._trace(body, k["bg"], tuple(sq), k["legend"])
    print(f"  e87109e9 line {ln}: blocks {len(blocks)} sizes within native {sizes_ok}; "
          f"1-cell separation {apart}; trace {st}")

section(25)
m = mod("dd2401ed")
kw = validate_kwargs("dd2401ed")
for (ln, k), p in zip(kw, pairs("dd2401ed")):
    blues = sum(v == 1 for r in p["input"] for v in r)
    if k.get("extra"):
        nat = m.generate(cursor=k["cursor"], extra=0, colors=k["colors"])["output"]
        diff = sum(a != b for ra, rb in zip(nat, p["output"]) for a, b in zip(ra, rb))
        print(f"  dd2401ed line {ln}: extra=1, blues {blues}; native (extra=0) label differs in {diff} cells")
    else:
        print(f"  dd2401ed line {ln}: extra=0, blues {blues}")
random.seed(SEED * 1000 + 25)
even_swept = 0
for _ in range(N):
    p = m.generate()
    g, o = p["input"], p["output"]
    blues = sum(v == 1 for r in g for v in r)
    swept = sum(1 for r in range(7) for c in range(15) if g[r][c] == 2 and o[r][c] == 1)
    even_swept += (blues % 2 == 0 and swept > 0)
report("native draws with even blue count and recoloured reds (parity reading disagrees)", even_swept, N)

section(26)
kw = validate_kwargs("ba1aa698")
print(f"ba1aa698: canonical extra per pair {[k.get('extra', 0) for _, k in kw]} (native extra=0, line 60)")

section(27)
dom_share = []
for p in pairs("9110e3c5"):
    cnt = collections.Counter(v for r in p["input"] for v in r if v)
    top = cnt.most_common(2)
    dom_share.append((top[0][0], top[0][1], top[1][1]))
print(f"9110e3c5: canonical (dominant colour, count, runner-up) {dom_share}")
random.seed(SEED * 1000 + 27)
gaps, ties = [], 0
for _ in range(N):
    g = mod("9110e3c5").generate()["input"]
    cnt = collections.Counter(v for r in g for v in r if v).most_common(2)
    gaps.append(cnt[0][1] - cnt[1][1])
    ties += cnt[0][1] == cnt[1][1]
gaps.sort()
print(f"  native dominant-minus-runner-up gap median {gaps[len(gaps) // 2]}, min {gaps[0]}; ties {ties}/{N}; "
      f"canonical gaps {[a - b for _, a, b in [(x, y, z) for x, y, z in dom_share]]}")

section(28)
dens = [round(sum(v == 8 for r in p["input"] for v in r) / 36, 2) for p in pairs("a8610ef7")]
print(f"a8610ef7: canonical 8-density {dens} (native fair coin, line 28)")

section(29)
can = []
for p in pairs("bbb1b8b6"):
    g = p["input"]
    holes = sum(g[r][c] == 0 for r in range(4) for c in range(4))
    other = sum(g[r][c + 5] != 0 for r in range(4) for c in range(4))
    exact = all((g[r][c] == 0) != (g[r][c + 5] == 0) for r in range(4) for c in range(4))
    can.append((exact, holes, other))
print(f"bbb1b8b6: canonical (exact, holes, other cells) {can}")
random.seed(SEED * 1000 + 29)
nonexact = same = 0
for _ in range(N):
    g = mod("bbb1b8b6").generate()["input"]
    exact = all((g[r][c] == 0) != (g[r][c + 5] == 0) for r in range(4) for c in range(4))
    if not exact:
        nonexact += 1
        holes = sum(g[r][c] == 0 for r in range(4) for c in range(4))
        other = sum(g[r][c + 5] != 0 for r in range(4) for c in range(4))
        same += holes == other
print(f"  native non-exact draws {nonexact}/{N}; of those with other-cell count == hole count {same}")

# Ungated panel truth tables: share of independent native 3-demo + query episodes whose
# demonstrations leave the query output undetermined within the 16 cell-wise truth tables.
PANELS = {"d19f7514": lambda g: (g[:len(g) // 2], g[len(g) // 2:]),
          "e133d23d": lambda g: ([r[:len(r) // 2] for r in g], [r[len(r) // 2 + 1:] for r in g]),
          "e345f17b": lambda g: ([r[:len(r) // 2] for r in g], [r[len(r) // 2:] for r in g])}
for i, tid in enumerate(sorted(PANELS)):
    random.seed(SEED * 1000 + 40 + i)
    m = mod(tid)
    split = PANELS[tid]
    amb = 0
    for _ in range(N):
        eps = [m.generate() for _ in range(4)]
        seen = set()
        for p in eps[:3]:
            a, b = split(p["input"])
            seen |= {(x != 0, y != 0) for ra, rb in zip(a, b) for x, y in zip(ra, rb)}
        a, b = split(eps[3]["input"])
        need = {(x != 0, y != 0) for ra, rb in zip(a, b) for x, y in zip(ra, rb)}
        amb += not need <= seen
    report(f"{tid} episodes whose query uses an occupancy combination absent from the demos", amb, N)

# ------------------------------------------------------- C. generalisation
print("== C. certified programs on inputs outside the native domain")


def rot_cw(g):
    return [list(r) for r in zip(*g[::-1])]


def rot_ccw(g):
    return [list(r) for r in zip(*g)][::-1]


def flip_rows(g):
    return [list(r) for r in g[::-1]]


def flip_cols(g):
    return [list(r)[::-1] for r in g]


def hcat(*gs):
    return [sum((list(g[i]) for g in gs), []) for i in range(len(gs[0]))]


def vcat(*gs):
    return [list(r) for g in gs for r in g]


def tile_k(g, k):
    return vcat(*[hcat(*[g] * k)] * k)


def ref_a59b95c0(g):
    return tile_k(g, len({v for r in g for v in r}))


def ref_d4b1c2b1(g):
    k = len({v for r in g for v in r})
    return [[v for v in r for _ in range(k)] for r in g for _ in range(k)]


def ref_c48954c1(g):
    rows = []
    for i in range(3):
        blocks = []
        for j in range(3):
            t = flip_rows(g) if i % 2 == 0 else [list(r) for r in g]
            blocks.append(flip_cols(t) if j % 2 == 0 else t)
        rows.append(hcat(*blocks))
    return vcat(*rows)


def ref_e633a9e5(g):
    ri = [0] + list(range(len(g))) + [len(g) - 1]
    ci = [0] + list(range(len(g[0]))) + [len(g[0]) - 1]
    return [[g[r][c] for c in ci] for r in ri]


def ref_a8610ef7(g):
    h = len(g)
    return [[(2 if g[h - 1 - r][c] == 8 else 5) if v == 8 else v for c, v in enumerate(row)]
            for r, row in enumerate(g)]


def ref_bc4146bd(g):
    m_ = flip_cols(g)
    return hcat(g, m_, g, m_, g)


def ref_cf5fd0ad(g):
    r180 = rot_cw(rot_cw(g))
    return vcat(hcat(tile2(r180), tile2(rot_cw(g))), hcat(tile2(rot_ccw(g)), tile2(g)))


def tile2(g):
    return vcat(hcat(g, g), hcat(g, g))


def ref_ed98d772(g):
    return vcat(hcat(g, rot_ccw(g)), hcat(rot_ccw(rot_ccw(g)), rot_ccw(rot_ccw(rot_ccw(g)))))


def ref_be03b35f(g, k):
    a = [row[:k] for row in g[:k]]
    return rot_cw(rot_cw(rot_cw(a)))


def ref_72207abc(g):
    row = max(range(len(g)), key=lambda r: sum(v != 0 for v in g[r]))
    cols = [v for v in g[row] if v]
    out = [list(r) for r in g]
    t = 0
    while t * (t + 1) // 2 < len(g[0]):
        out[row][t * (t + 1) // 2] = cols[t % len(cols)]
        t += 1
    return out


def ref_8597cfd7(g):
    h = len(g)
    d = h // 2
    def cnt(c, rows):
        return sum(v == c for r in rows for v in g[r])
    gr = cnt(2, range(d + 1, h)) - cnt(2, range(d))
    gy = cnt(4, range(d + 1, h)) - cnt(4, range(d))
    w = 2 if gr > gy else 4
    return [[w, w], [w, w]]


def ref_bbb1b8b6(g):
    w = (len(g[0]) - 1) // 2
    a = [r[:w] for r in g]
    b = [r[w + 1:] for r in g]
    exact = all((x == 0) != (y == 0) for ra, rb in zip(a, b) for x, y in zip(ra, rb))
    return [[x + (y if exact else 0) for x, y in zip(ra, rb)] for ra, rb in zip(a, b)]


def ref_9b30e358(g):
    h, bg = len(g), g[0][0]
    top = next(r for r in range(h) if any(v != bg for v in g[r]))
    line = h - top
    return [list(g[h - 1 - ((h - 1 - r) % line)]) for r in range(h)]


REFS = {"a59b95c0": ref_a59b95c0, "d4b1c2b1": ref_d4b1c2b1, "c48954c1": ref_c48954c1,
        "e633a9e5": ref_e633a9e5, "a8610ef7": ref_a8610ef7, "bc4146bd": ref_bc4146bd,
        "cf5fd0ad": ref_cf5fd0ad, "ed98d772": ref_ed98d772, "72207abc": ref_72207abc,
        "8597cfd7": ref_8597cfd7, "bbb1b8b6": ref_bbb1b8b6, "9b30e358": ref_9b30e358}


def draw_input(tid, rng):
    if tid in ("a59b95c0", "d4b1c2b1"):
        while True:
            h, w = rng.randint(1, 6), rng.randint(1, 6)
            if h * w == 9 and h == w:
                continue  # native 3x3
            k = rng.randint(1, min(h * w, 30 // max(h, w), 9))
            cols = rng.sample(range(1, 10), k)
            g = [[rng.choice(cols) for _ in range(w)] for _ in range(h)]
            if len({v for r in g for v in r}) == k:
                return g
    if tid == "c48954c1":
        h, w = rng.choice([(a, b) for a in range(1, 11) for b in range(1, 11) if (a, b) != (3, 3)])
        cols = rng.sample(range(1, 10), rng.randint(2, 5))
        return [[rng.choice(cols) for _ in range(w)] for _ in range(h)]
    if tid == "e633a9e5":
        h, w = rng.choice([(a, b) for a in range(1, 29) for b in range(1, 29) if (a, b) != (3, 3)])
        return [[rng.randint(1, 9) for _ in range(w)] for _ in range(h)]
    if tid == "a8610ef7":
        h, w = rng.choice([(a, b) for a in range(1, 31) for b in range(1, 31) if (a, b) != (6, 6)])
        return [[8 * rng.randint(0, 1) for _ in range(w)] for _ in range(h)]
    if tid == "bc4146bd":
        h, w = rng.choice([(a, b) for a in range(1, 31) for b in range(1, 7) if (a, b) != (4, 4)])
        cols = rng.sample(range(1, 10), rng.randint(2, 4))
        return [[rng.choice(cols) for _ in range(w)] for _ in range(h)]
    if tid in ("cf5fd0ad", "ed98d772"):
        n = rng.choice([v for v in range(1, (8 if tid == "cf5fd0ad" else 16)) if v != 3])
        if tid == "cf5fd0ad":
            sub = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], rng.randint(1, 3))
            return [[8 if rng.randint(0, 2) else rng.choice(sub) for _ in range(n)] for _ in range(n)]
        hue = rng.randint(1, 9)
        return [[hue * rng.randint(0, 1) for _ in range(n)] for _ in range(n)]
    if tid == "72207abc":
        while True:
            h, w = rng.randint(1, 30), rng.randint(4, 30)
            if h == 3 and w in (19, 29):
                continue
            k = rng.randint(2, 4)
            seeds = [0, 1, 3, 6][:k]
            if seeds[-1] >= w:
                continue
            cols = rng.sample(range(1, 10), k)
            g = [[0] * w for _ in range(h)]
            r = rng.randrange(h)
            for s, c in zip(seeds, cols):
                g[r][s] = c
            return g
    if tid == "8597cfd7":
        while True:
            h = rng.choice(range(5, 30, 2))
            w = rng.randint(3, 30)
            if (h, w) in ((9, 9), (11, 9)):
                continue
            cr, cy = rng.sample(range(w), 2)
            t = h // 2
            reds = sorted(rng.sample(range(1, t + 1), 2)) if t >= 2 else None
            yel = sorted(rng.sample(range(1, t + 1), 2)) if t >= 2 else None
            if not reds or reds[1] - reds[0] == yel[1] - yel[0]:
                continue
            g = [[0] * w for _ in range(h)]
            g[t] = [5] * w
            for i in range(2):
                for r in range(reds[i]):
                    g[i * (t + 1) + r][cr] = 2
                for r in range(yel[i]):
                    g[i * (t + 1) + r][cy] = 4
            return g
    if tid == "bbb1b8b6":
        while True:
            h, w = rng.randint(2, 30), rng.randint(2, 14)
            if (h, w) == (4, 4):
                continue
            base = [[rng.randint(0, 1) for _ in range(w)] for _ in range(h)]
            if all(v for r in base for v in r) or not any(v for r in base for v in r):
                continue
            col = rng.choice([2, 3, 4, 6, 7, 8, 9])
            mode = rng.randint(0, 2)
            other = [[1 - v for v in r] for r in base]
            if mode == 1:  # random
                other = [[rng.randint(0, 1) for _ in range(w)] for _ in range(h)]
            if mode == 2:  # near miss: complement with one cell toggled
                rr, cc = rng.randrange(h), rng.randrange(w)
                other[rr][cc] = 1 - other[rr][cc]
            return [[base[r][c] for c in range(w)] + [5] + [col * other[r][c] for c in range(w)]
                    for r in range(h)]
    if tid == "9b30e358":
        while True:
            h, w = rng.randint(6, 30), rng.randint(3, 30)
            if h == 10 and 5 <= w <= 7:
                continue
            bg = rng.randint(1, 9)
            sub = rng.sample([c for c in range(1, 10) if c != bg], 2)
            line = rng.randint(1, (h - 1) // 2)  # keeps the background modal; see note below
            g = [[bg] * w for _ in range(h)]
            for r in range(line):
                for c in rng.sample(range(w), rng.randint(1, w)):
                    g[h - 1 - r][c] = rng.choice(sub)
            return g


for i, tid in enumerate(sorted(REFS)):
    rng = section(100 + i)
    solve, kind = program(tid)
    ref = REFS[tid]
    can = all(ref(p["input"]) == p["output"] for p in pairs(tid))
    agree = 0
    shapes = set()
    for _ in range(N):
        g = draw_input(tid, rng)
        shapes.add((len(g), len(g[0])))
        try:
            agree += solve(g) == ref(g)
        except Exception:
            pass
    print(f"{tid} ({kind}): reference reproduces canonical {can}; program == reference "
          f"{agree}/{N} over {len(shapes)} input shapes")

# be03b35f: k x k quadrants with a gap, k 2..9
rng = section(150)
solve, kind = program("be03b35f")
can = all(ref_be03b35f(p["input"], 2) == p["output"] for p in pairs("be03b35f"))
agree = total = 0
for _ in range(N):
    k, gap = rng.randint(2, 9), rng.randint(1, 3)
    if (k, gap) == (2, 1):
        continue
    while True:
        a = [[rng.randint(0, 1) for _ in range(k)] for _ in range(k)]
        if 0 < sum(map(sum, a)) < k * k:
            break
    n = 2 * k + gap
    g = [[0] * n for _ in range(n)]
    tr = rot_cw(a)
    bl = rot_cw(tr)
    for r in range(k):
        for c in range(k):
            g[r][c] = a[r][c]
            g[r][k + gap + c] = tr[r][c]
            g[k + gap + r][c] = bl[r][c]
            g[k + gap + r][k + gap + c] = 2
    total += 1
    try:
        agree += solve(g) == ref_be03b35f(g, k)
    except Exception:
        pass
print(f"be03b35f ({kind}): reference reproduces canonical {can}; k x k quadrants (k 2..9, gap 1..3) "
      f"{agree}/{total}")

# e3f79277: input canvas H x W (>= L) and L up to 8, against an independent drawing
rng = section(151)
solve, kind = program("e3f79277")


def ref_e3f79277(L, col, flip, flop):
    out = [[7] * 16 for _ in range(16)]
    for i in range(2 * L):
        out[0][i] = out[i][0] = out[i][2 * L - 1 - i] = col
    if flip:
        out = out[::-1]
    if flop:
        out = [r[::-1] for r in out]
    return out


can = all(ref_e3f79277(k["length"], k["color"], k["flip"], k["flop"]) == p["output"]
          for (_, k), p in zip(validate_kwargs("e3f79277"), pairs("e3f79277")))
agree = total = 0
for _ in range(N):
    L = rng.randint(2, 8)
    h, w = rng.randint(L, 30), rng.randint(L, 30)
    if (h, w) == (6, 6) and L <= 6:
        continue
    if h * w <= 2 * (2 * L - 1):
        continue  # the background (7) must stay modal; the teacher reads it as the modal colour
    col = rng.choice([1, 2, 3, 4, 5, 6, 8, 9])
    flip, flop = rng.randint(0, 1), rng.randint(0, 1)
    g = [[7] * w for _ in range(h)]
    for i in range(L):
        g[0][i] = g[i][0] = col
    if flip:
        g = g[::-1]
    if flop:
        g = [r[::-1] for r in g]
    total += 1
    try:
        agree += solve(g) == ref_e3f79277(L, col, flip, flop)
    except Exception:
        pass
print(f"e3f79277 ({kind}): reference reproduces canonical {can}; canvas L..30 x L..30, L 2..8 {agree}/{total}")

# Families whose own explicit-parameter path is the reference (outside native ranges)
rng = section(152)
solve, kind = program("18447a8d")
m = mod("18447a8d")
agree = total = 0
counts = collections.Counter()
while total < N:
    n = rng.choice([2, 5, 6, 7])
    colors = rng.sample([1, 2, 3, 4, 5, 6, 9], n)
    lefts, rights = [], []
    for _ in colors:
        left = [rng.randint(1, 4) for _ in range(3)]
        lefts.append(left)
        rights.append([5 - v for v in left])
    rng.shuffle(rights)
    p = m.generate(lefts=sum(lefts, []), rights=sum(rights, []), colors=colors)
    if p["input"] is None:
        continue
    total += 1
    counts[n] += 1
    agree += solve(p["input"]) == p["output"]
print(f"18447a8d ({kind}): band counts {dict(sorted(counts.items()))} via the constructor's explicit path "
      f"{agree}/{total}")

rng = section(153)
solve, kind = program("d017b73f")
m = mod("d017b73f")
agree = total = 0
nseg = collections.Counter()
tries = 0
while total < N and tries < 200000:
    tries += 1
    k = rng.randint(2, 6)
    hl = [rng.randint(1, 5) for _ in range(k)]
    hl[0] = max(hl[0], 2)
    hrows = [1]
    for _ in hl[1:]:
        hrows.append(rng.choice([r for r in range(3) if r != hrows[-1]]))
    outw = sum(hl) - len(hl) + 1
    nv = rng.randint(2, 5)
    vl = [rng.randint(1, 4) for _ in range(nv)]
    if sum(vl) != outw:
        continue
    vo = [0] + [rng.randint(-2, 2) for _ in vl[1:]]
    vc = [rng.randint(1, 9) for _ in vl]
    if any(a == b for a, b in zip(vc, vc[1:])) or len(set(vo)) == 1:
        continue
    native = (2 <= hl[0] <= 3 and 4 <= len(hl) <= 6 and 3 <= nv <= 4 and all(2 <= v <= 3 for v in vl))
    if native:
        continue
    p = m.generate(hlengths=hl, hrows=hrows, vlengths=vl, vcolors=vc, voffsets=vo, bump=rng.randint(0, 1))
    if p["input"] is None or len(p["input"][0]) > 30:
        continue
    total += 1
    nseg[len(hl)] += 1
    agree += solve(p["input"]) == p["output"]
print(f"d017b73f ({kind}): non-native segment/piece parameters, segments {dict(sorted(nseg.items()))}, "
      f"via the constructor's explicit path {agree}/{total}")

# Canonical-compatible relaxation: first segment 2..3, 1..4 middle segments of 3..5, optional last
# segment 1..5 (canonical lines 105-108 need 2..3 middle segments and a last segment of 2), pieces 2..3
# wide, 2..5 pieces. Native draws are excluded.
rng = section(156)
agree = total = 0
nseg = collections.Counter()
tries = 0
while total < N and tries < 400000:
    tries += 1
    hl = [rng.randint(2, 3)] + [rng.randint(3, 5) for _ in range(rng.randint(1, 4))]
    if rng.randint(0, 1):
        hl.append(rng.randint(1, 5))
    hrows = [1]
    for _ in hl[1:]:
        hrows.append(rng.choice([r for r in range(3) if r != hrows[-1]]))
    outw = sum(hl) - len(hl) + 1
    vl = [rng.randint(2, 3) for _ in range(rng.randint(2, 5))]
    if sum(vl) != outw:
        continue
    vo = [0] + [rng.randint(-2, 2) for _ in vl[1:]]
    vc = [rng.randint(1, 9) for _ in vl]
    if any(a == b for a, b in zip(vc, vc[1:])) or len(set(vo)) == 1:
        continue
    mid, tail = (hl[1:-1], hl[-1]) if hl[-1] == 1 else (hl[1:], None)
    native = 3 <= len(mid) <= 4 and all(3 <= v <= 5 for v in mid) and 3 <= len(vl) <= 4
    if native:
        continue
    p = m.generate(hlengths=hl, hrows=hrows, vlengths=vl, vcolors=vc, voffsets=vo, bump=rng.randint(0, 1))
    if p["input"] is None or len(p["input"][0]) > 30:
        continue
    total += 1
    nseg[len(hl)] += 1
    agree += solve(p["input"]) == p["output"]
print(f"d017b73f ({kind}): canonical-compatible relaxation (segments {dict(sorted(nseg.items()))}) "
      f"{agree}/{total}")

rng = section(154)
solve, kind = program("42f83767")
m = mod("42f83767")
agree = total = 0
while total < N:
    L, size = rng.randint(3, 6), rng.randint(4, 7)
    brow, bcol = rng.randint(L + 1, 15 - size), rng.randint(1, 5)
    subset = rng.sample([1, 2, 3, 4, 8], rng.randint(2, 4))
    if (3 + L + 1) * len(subset) - 1 > 30 or L * size > 30:
        continue
    colors = [rng.choice(subset) for _ in range(size * size)]
    if len(set(colors)) != len(subset):
        continue
    pats = []
    for _ in subset:
        while True:
            mask = [rng.random() < rng.uniform(0.3, 0.7) for _ in range(L * L)]
            rows = {i // L for i, v in enumerate(mask) if v}
            cols_ = {i % L for i, v in enumerate(mask) if v}
            if len(rows) == L and len(cols_) == L and sum(mask) < L * L - L:
                break
        pats.append("".join("5" if v else "0" for v in mask))
    p = m.generate(length=L, size=size, brow=brow, bcol=bcol, subset=subset,
                   colors="".join(map(str, colors)), patterns="".join(pats))
    total += 1
    agree += solve(p["input"]) == p["output"]
print(f"42f83767 ({kind}): stencils sparser than conway_sprite (< L*L-L px) via the constructor's "
      f"explicit path {agree}/{total}")

rng = section(155)
solve, kind = program("e87109e9")
m = mod("e87109e9")
agree = total = flagged = 0
while total < N:
    h = rng.randint(14, 24)
    bg = rng.choice(m.PALETTE)
    cols = [c for c in m.PALETTE if c != bg]
    legend_cols = rng.sample(cols, 4)
    legend = [(c, rng.choice(["L", "R"])) for c in legend_cols]
    s = rng.choice([2, 3])
    r, c = rng.randint(2, h - s - 2), rng.randint(2, 24 - s - 2)
    blocks = []
    for colour in rng.sample(legend_cols, rng.randint(3, 4)):
        for _ in range(60):
            bh, bw = rng.randint(2, h - 1), rng.randint(2, 23)
            top, left = rng.randint(0, h - bh), rng.randint(0, 24 - bw)
            if not m._apart((top, left, bh, bw), (r, c, s, s), 1):
                continue
            if all(m._apart((top, left, bh, bw), b[:4], 0) for b in blocks):
                blocks.append((top, left, bh, bw, colour))
                break
    if len(blocks) < 3:
        continue
    if not any(b[2] > min(12, h - 4) or b[3] > 14 or any(not m._apart(b[:4], o[:4], 1) for o in blocks if o is not b)
               for b in blocks):
        continue  # keep only scenes outside the native block ranges / separation
    if (sum(b[2] * b[3] for b in blocks) + s * s) * 2 >= h * 24:
        continue  # keep the constructor's area guard (line 182): background stays modal
    body = m._build_body(h, bg, (r, c, s), blocks)
    out, st = m._trace(body, bg, (r, c, s), legend)
    if st["mixed"] or st["loop"] or st["stopped"]:
        flagged += 1
        continue
    total += 1
    agree += solve(m._header(legend) + body) == out
print(f"e87109e9 ({kind}): touching or oversized blocks (native excludes) via the constructor's trace "
      f"{agree}/{total}; scenes skipped for mixed/loop/stop flags {flagged}")

# Configured-size path of the parameterised panel families
for i, tid in enumerate(("d19f7514", "e133d23d", "e345f17b")):
    rng = section(160 + i)
    solve, kind = program(tid)
    m = mod(tid)
    agree = total = 0
    shapes = set()
    for _ in range(N):
        w, h = rng.randint(1, 14), rng.randint(1, 15 if tid == "d19f7514" else 30)
        p = m.generate(width=w, height=h, top=[rng.randint(0, 1) for _ in range(w * h)],
                       bottom=[rng.randint(0, 1) for _ in range(w * h)])
        if len(p["input"]) > 30 or len(p["input"][0]) > 30:
            continue
        total += 1
        shapes.add((len(p["input"]), len(p["input"][0])))
        agree += solve(p["input"]) == p["output"]
    print(f"{tid} ({kind}): explicit width/height path {agree}/{total} over {len(shapes)} input shapes")
