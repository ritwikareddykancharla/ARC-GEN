"""Independent identifiability gate for e5062a87 (pure Python, no numpy).

Re-implements the hypothesis family used by factory.py in a different style.
The gate sees only demonstration pairs and the query INPUT; it never sees a
query answer. It returns ('identified', answer), ('ambiguous', answers) or
('unexplained', None).
"""
from itertools import product


def _cells_of(g, colour):
    return [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == colour]


def _box_holes(rel, h, w):
    # A box cell outside the shape is a hole if no 4-path through non-shape
    # cells reaches the outside of the box (BFS from each cell separately).
    shape = set(rel)
    holes = []
    for y in range(h):
        for x in range(w):
            if (y, x) in shape:
                continue
            frontier, seen, escaped = [(y, x)], {(y, x)}, False
            while frontier and not escaped:
                cy, cx = frontier.pop()
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if not (0 <= ny < h and 0 <= nx < w):
                        escaped = True
                        break
                    if (ny, nx) not in shape and (ny, nx) not in seen:
                        seen.add((ny, nx))
                        frontier.append((ny, nx))
            if not escaped:
                holes.append((y, x))
    return holes


def stamp_options(g, zero, tcol):
    """Return the candidate stamps with every visible attribute, or None."""
    t = _cells_of(g, tcol)
    if not t:
        return None
    oy = min(r for r, _ in t)
    ox = min(c for _, c in t)
    rel = sorted({(r - oy, c - ox) for r, c in t})
    h = 1 + max(r for r, _ in rel)
    w = 1 + max(c for _, c in rel)
    H, W = len(g), len(g[0])
    shape = set(rel)
    holes = _box_holes(rel, h, w)
    centre = [(h // 2, w // 2)] if (h & 1 and w & 1 and (h // 2, w // 2) not in shape) else []
    has_block = any({(y, x), (y + 1, x), (y, x + 1), (y + 1, x + 1)} <= shape
                    for y in range(h - 1) for x in range(w - 1))
    open_windows = [frozenset({(y, x), (y + 1, x), (y, x + 1), (y + 1, x + 1)})
                    for y in range(H - 1) for x in range(W - 1)
                    if g[y][x] == zero and g[y + 1][x] == zero and g[y][x + 1] == zero and g[y + 1][x + 1] == zero]
    out = []
    for oy2, ox2 in product(range(H - h + 1), range(W - w + 1)):
        cells = frozenset((oy2 + y, ox2 + x) for y, x in rel)
        if any(g[r][c] != zero for r, c in cells):
            continue
        out.append(dict(
            off=(oy2, ox2), cells=cells,
            holes=any(g[oy2 + y][ox2 + x] == zero for y, x in holes),
            center=any(g[oy2 + y][ox2 + x] == zero for y, x in centre),
            thick=(not has_block) and any(1 < len(win & cells) < 4 for win in open_windows),
            line=(h == 1 and oy2 != oy) or (w == 1 and ox2 != ox),
            extra=sum(1 for y in range(h) for x in range(w) if (y, x) not in shape and g[oy2 + y][ox2 + x] == zero),
        ))
    return out


HYPOTHESES = list(product(('none', 'holes', 'center'), (False, True), (False, True),
                          ['union', 'minextra'] + ['scan%d' % k for k in range(8)]))


def _scan_key(k):
    # 8 visible raster scans: choose primary axis and both directions.
    def key(s):
        y, x = s['off']
        a, b = (x, y) if k & 4 else (y, x)
        return ((a if k & 1 else -a), (b if k & 2 else -b))
    return key


def paint(g, opts, hyp, tcol):
    hole, thick, line, res = hyp
    live = [s for s in opts
            if not (hole != 'none' and s[hole]) and not (thick and s['thick']) and not (line and s['line'])]
    taken = set()
    pick = []
    if res == 'union':
        pick = live
    elif res == 'minextra':
        for lv in sorted({s['extra'] for s in live}):
            tier = [s for s in live if s['extra'] == lv and not (s['cells'] & taken)]
            for a in range(len(tier)):
                for b in range(a + 1, len(tier)):
                    if tier[a]['cells'] & tier[b]['cells']:
                        return None
            for s in tier:
                pick.append(s)
                taken |= s['cells']
    else:
        for s in sorted(live, key=_scan_key(int(res[4:]))):
            if not (s['cells'] & taken):
                pick.append(s)
                taken |= s['cells']
    res_grid = [list(row) for row in g]
    for s in pick:
        for r, c in s['cells']:
            res_grid[r][c] = tcol
    return res_grid


def gate(demos, query_input, zero, tcol):
    """demos: list of (input, output) lists; query_input: grid. Answers never seen."""
    alive = []
    prepared = [(i, o, stamp_options(i, zero, tcol)) for i, o in demos]
    for hyp in HYPOTHESES:
        if all(opts is not None and paint(i, opts, hyp, tcol) == [list(r) for r in o]
               for i, o, opts in prepared):
            alive.append(hyp)
    if not alive:
        return ('unexplained', None, alive)
    qopts = stamp_options(query_input, zero, tcol)
    if qopts is None:
        return ('unexplained', None, alive)
    answers = {}
    for hyp in alive:
        p = paint(query_input, qopts, hyp, tcol)
        answers.setdefault(None if p is None else str(p), []).append(hyp)
    if len(answers) == 1 and None not in answers:
        key = next(iter(answers))
        return ('identified', eval_grid(key), alive)
    return ('ambiguous', answers, alive)


def eval_grid(s):
    import json
    return json.loads(s)
