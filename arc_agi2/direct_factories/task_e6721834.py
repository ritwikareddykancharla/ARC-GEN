_PROGRAM = r'''import numpy as np
from collections import Counter, deque

# Episode specialisation. The mechanism is pure translation and is orientation-
# and colour-free, so the split axis, marker half and colour roles are inferred
# directly from the visible pixels in visible coordinates.
D4 = __D4__
PALETTE = __PALETTE__


def _mode(a):
    cnt = Counter(int(v) for v in a.ravel())
    best = None
    for c, n in cnt.items():
        if best is None or n > best[1] or (n == best[1] and c < best[0]):
            best = (c, n)
    return best[0]


def _colours(a):
    return set(int(v) for v in a.ravel())


def _comps(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _split(g):
    h, w = g.shape
    cands = []
    if w % 2 == 0 and w >= 2:
        cands.append((g[:, :w // 2], g[:, w // 2:]))
    if h % 2 == 0 and h >= 2:
        cands.append((g[:h // 2], g[h // 2:]))
    for A, B in cands:
        pa, pb = _mode(A), _mode(B)
        if pa != pb and pa not in _colours(B) and pb not in _colours(A):
            return A, B
    if w >= 2 and _mode(g[:, :w // 2]) != _mode(g[:, w // 2:]):
        return g[:, :w // 2], g[:, w // 2:]
    if h >= 2:
        return g[:h // 2], g[h // 2:]
    return g[:, :max(1, w // 2)], g[:, max(1, w // 2):]


def _is_dot_half(X, Y):
    m = _mode(X)
    cy = _colours(Y)
    return all(c in cy for c in _colours(X) if c != m)


def _rect_ok(a, b):
    comps = _comps(a != b)
    for c in comps:
        ys = [p[0] for p in c]
        xs = [p[1] for p in c]
        if (max(ys) - min(ys) + 1) * (max(xs) - min(xs) + 1) != len(c):
            return False
    return len(comps) > 0


def _sep(a, b):
    return a[1] + 1 < b[0] or b[1] + 1 < a[0] or a[3] + 1 < b[2] or b[3] + 1 < a[2]


def _cands(shape, dots, mk, dbg, strict):
    comp, vals, markers = shape
    H, W = mk.shape
    y0, x0, c0 = markers[0]
    res = []
    for (dy, dx), dc in sorted(dots.items()):
        if dc != c0:
            continue
        oy, ox = dy - y0, dx - x0
        if not all(dots.get((y + oy, x + ox)) == c for y, x, c in markers):
            continue
        mset = frozenset((y + oy, x + ox) for y, x, c in markers)
        cells = [(y + oy, x + ox) for y, x in comp]
        if strict:
            if any(not (0 <= ny < H and 0 <= nx < W) for ny, nx in cells):
                continue
            if any((ny, nx) not in mset and int(mk[ny, nx]) != dbg for ny, nx in cells):
                continue
        ys = [p[0] for p in cells]
        xs = [p[1] for p in cells]
        res.append((oy, ox, mset, frozenset(cells), (min(ys), max(ys), min(xs), max(xs))))
    return res


def _search(shapes, dots, mk, dbg, strict):
    allc = [_cands(s, dots, mk, dbg, strict) for s in shapes]
    target = frozenset(dots)
    n = len(shapes)
    rem = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        rem[i] = rem[i + 1] + len(shapes[i][2])
    budget = [200000]

    def rec(i, used, cells, boxes, chosen):
        budget[0] -= 1
        if budget[0] < 0:
            return None
        if len(target) - len(used) > rem[i]:
            return None
        if i == n:
            return list(chosen) if used == target else None
        for cand in allc[i]:
            oy, ox, mset, cset, bb = cand
            if mset & used:
                continue
            if strict:
                if cset & cells:
                    continue
                if any(not _sep(bb, b2) for b2 in boxes):
                    continue
            chosen.append((i, cand))
            r = rec(i + 1, used | mset, (cells | cset) if strict else cells, boxes + [bb], chosen)
            chosen.pop()
            if r is not None:
                return r
        return rec(i + 1, used, cells, boxes, chosen)

    return rec(0, frozenset(), frozenset(), [], [])


def _greedy(shapes, dots):
    used = set()
    sol = []
    for i, (comp, vals, markers) in enumerate(shapes):
        y0, x0, c0 = markers[0]
        for (dy, dx), dc in sorted(dots.items()):
            if dc != c0:
                continue
            oy, ox = dy - y0, dx - x0
            tgt = [(y + oy, x + ox) for y, x, c in markers]
            if all(dots.get(p) == c and p not in used for p, (y, x, c) in zip(tgt, markers)):
                used |= set(tgt)
                sol.append((i, (oy, ox, None, None, None)))
                break
    return sol


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    A, B = _split(g)
    da, db = _is_dot_half(A, B), _is_dot_half(B, A)
    if da and not db:
        mk, sh = A, B
    elif db and not da:
        mk, sh = B, A
    else:
        na = int(np.sum(A != _mode(A)))
        nb = int(np.sum(B != _mode(B)))
        mk, sh = (A, B) if na <= nb else (B, A)
    dbg = _mode(mk)
    mcols = _colours(mk)
    scols = _colours(sh)
    counts = Counter(int(v) for v in sh.ravel())
    cands = sorted(c for c in scols if c not in mcols)
    good = [c for c in cands if _rect_ok(sh, c)]
    pool = good or cands or sorted(scols)
    sbg = max(pool, key=lambda c: (counts[c], -c))
    comps = _comps(sh != sbg)
    fpool = [c for c in cands if c != sbg]
    fc = None
    if fpool:
        def score(c):
            k = sum(1 for comp in comps if any(int(sh[y, x]) == c for y, x in comp))
            return (k, counts[c], -c)
        fc = max(fpool, key=score)
    shapes = []
    for comp in comps:
        vals = [int(sh[y, x]) for y, x in comp]
        if fc is not None and fc in vals:
            body = fc
        else:
            body = max(sorted(set(vals)), key=vals.count)
        markers = [(y, x, v) for (y, x), v in zip(comp, vals) if v != body]
        if markers:
            shapes.append((comp, vals, markers))
    shapes.sort(key=lambda s: -len(s[2]))
    H, W = mk.shape
    dots = {}
    for y in range(H):
        for x in range(W):
            v = int(mk[y, x])
            if v != dbg:
                dots[(y, x)] = v
    sol = _search(shapes, dots, mk, dbg, True)
    if sol is None:
        sol = _search(shapes, dots, mk, dbg, False)
    if sol is None:
        sol = _greedy(shapes, dots)
    out = np.full((H, W), dbg, dtype=int)
    for i, cand in sol:
        oy, ox = cand[0], cand[1]
        comp, vals = shapes[i][0], shapes[i][1]
        for (y, x), v in zip(comp, vals):
            ny, nx = y + oy, x + ox
            if 0 <= ny < H and 0 <= nx < W:
                out[ny, nx] = v
    return out.tolist()
'''


def build_program(d4, palette):
    pal = [int(c) for c in palette]
    return _PROGRAM.replace('__D4__', str(int(d4))).replace('__PALETTE__', repr(pal))
