"""Direct-coordinate factory for e5062a87 (hypothesis agreement, no fallback).

The emitted program works on visible coordinates only. The template is the
palette[2] object, and the open cells are palette[0]. The program enumerates a
fixed, D4-closed family of visible stamping hypotheses. It keeps only the ones
that reproduce every demonstration exactly, and it answers only when all of
those survivors give the same full query output. Otherwise it raises (abstains).
d4 is deliberately unused: the family is closed under D4, so d4 never selects
among rival explanations.
"""

TEMPLATE = '''import numpy as np

ZERO = @Z@
TCOL = @T@

# Hypothesis family (all D4-closed, visible-coordinate):
#   hole  : 'none' | 'holes' (enclosed template holes must not land on ZERO)
#           | 'center' (odd box, empty centre must not land on ZERO)
#   thick : 1 -> thin template (no solid 2x2) may not partially fill an
#           all-ZERO 2x2 window
#   line  : 1 -> a 1-high (1-wide) template is copied only along its own row
#           (column)
#   res   : how overlapping candidates are resolved: 'union', 'minextra'
#           (strictly by fewest ZERO cells in the box, undefined on a tie
#           conflict) or one of 8 visible raster scans
HOLES = ('none', 'holes', 'center')
RESOLVE = ('union', 'minextra') + tuple(range(8))
HYPS = [(h, t, l, r) for h in HOLES for t in (0, 1) for l in (0, 1) for r in RESOLVE]


class Abstain(Exception):
    pass


def _template(g):
    ys, xs = np.nonzero(g == TCOL)
    if ys.size == 0:
        return None
    y0 = int(ys.min())
    x0 = int(xs.min())
    cells = sorted(set((int(y) - y0, int(x) - x0) for y, x in zip(ys.tolist(), xs.tolist())))
    h = max(c[0] for c in cells) + 1
    w = max(c[1] for c in cells) + 1
    return cells, y0, x0, h, w


def _enclosed(cells, h, w):
    s = set(cells)
    seen = set()
    stack = [(y, x) for y in range(h) for x in range(w)
             if (y in (0, h - 1) or x in (0, w - 1)) and (y, x) not in s]
    while stack:
        p = stack.pop()
        if p in seen:
            continue
        seen.add(p)
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (p[0] + a, p[1] + b)
            if 0 <= q[0] < h and 0 <= q[1] < w and q not in s and q not in seen:
                stack.append(q)
    return [(y, x) for y in range(h) for x in range(w) if (y, x) not in s and (y, x) not in seen]


def _analyse(g):
    tp = _template(g)
    if tp is None:
        return None
    cells, y0, x0, h, w = tp
    H, W = g.shape
    s = set(cells)
    holes = _enclosed(cells, h, w)
    centre = []
    if h % 2 == 1 and w % 2 == 1 and (h // 2, w // 2) not in s:
        centre = [(h // 2, w // 2)]
    solid = any(all((y + a, x + b) in s for a in (0, 1) for b in (0, 1))
                for y in range(h - 1) for x in range(w - 1))
    zero = (g == ZERO)
    cands = []
    for dy in range(H - h + 1):
        for dx in range(W - w + 1):
            if not all(zero[y + dy, x + dx] for y, x in cells):
                continue
            cs = frozenset((y + dy, x + dx) for y, x in cells)
            thick = False
            if not solid:
                for y, x in cs:
                    for wy in (y - 1, y):
                        for wx in (x - 1, x):
                            if wy < 0 or wx < 0 or wy + 1 >= H or wx + 1 >= W:
                                continue
                            win = ((wy, wx), (wy, wx + 1), (wy + 1, wx), (wy + 1, wx + 1))
                            k = sum(1 for q in win if q in cs)
                            if 2 <= k < 4 and all(zero[q] for q in win):
                                thick = True
            cands.append({
                'dy': dy, 'dx': dx, 'cells': cs,
                'holes': any(zero[y + dy, x + dx] for y, x in holes),
                'center': any(zero[y + dy, x + dx] for y, x in centre),
                'thick': thick,
                'line': (h == 1 and dy != y0) or (w == 1 and dx != x0),
                'extra': sum(1 for y in range(h) for x in range(w)
                             if (y, x) not in s and zero[y + dy, x + dx]),
            })
    return cands


def _predict(g, cands, hyp):
    hole, thick, line, res = hyp
    keep = []
    for c in cands:
        if hole != 'none' and c[hole]:
            continue
        if thick and c['thick']:
            continue
        if line and c['line']:
            continue
        keep.append(c)
    chosen = []
    used = set()
    if res == 'union':
        chosen = keep
    elif res == 'minextra':
        for level in sorted(set(c['extra'] for c in keep)):
            layer = [c for c in keep if c['extra'] == level and not (c['cells'] & used)]
            for i in range(len(layer)):
                for j in range(i + 1, len(layer)):
                    if layer[i]['cells'] & layer[j]['cells']:
                        return None
            for c in layer:
                chosen.append(c)
                used |= c['cells']
    else:
        swap = res >= 4
        sa = 1 if res & 1 else -1
        sb = 1 if res & 2 else -1
        if swap:
            order = sorted(keep, key=lambda c: (sa * c['dx'], sb * c['dy']))
        else:
            order = sorted(keep, key=lambda c: (sa * c['dy'], sb * c['dx']))
        for c in order:
            if c['cells'] & used:
                continue
            chosen.append(c)
            used |= c['cells']
    out = g.copy()
    for c in chosen:
        for p in c['cells']:
            out[p] = TCOL
    return out


def solve(demonstrations, grid):
    pairs = []
    for d in demonstrations:
        i = np.array(d['input'], dtype=int)
        o = np.array(d['output'], dtype=int)
        pairs.append((i, o, _analyse(i)))
    if not pairs:
        raise Abstain('no demonstrations')
    survivors = []
    for hyp in HYPS:
        ok = True
        for i, o, cands in pairs:
            if cands is None or i.shape != o.shape:
                ok = False
                break
            p = _predict(i, cands, hyp)
            if p is None or not np.array_equal(p, o):
                ok = False
                break
        if ok:
            survivors.append(hyp)
    if not survivors:
        raise Abstain('no hypothesis reproduces every demonstration')
    g = np.array(grid, dtype=int)
    cands = _analyse(g)
    if cands is None:
        raise Abstain('query has no template')
    answers = {}
    for hyp in survivors:
        p = _predict(g, cands, hyp)
        if p is None:
            raise Abstain('surviving hypothesis undefined on query')
        answers[p.tobytes()] = p
    if len(answers) != 1:
        raise Abstain('surviving hypotheses disagree on the query')
    out = list(answers.values())[0]
    return [[int(v) for v in row] for row in out.tolist()]
'''


def build_program(d4, palette):
    # d4 intentionally unused: every hypothesis is stated in visible
    # coordinates and the family is closed under D4.
    return TEMPLATE.replace('@Z@', str(int(palette[0]))).replace('@T@', str(int(palette[2])))
