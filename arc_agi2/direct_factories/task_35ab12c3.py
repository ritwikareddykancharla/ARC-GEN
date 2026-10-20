TEMPLATE = '''import numpy as np

BG = __BG__
RANK = __RANK__


def _sign(v):
    return 1 if v > 0 else (-1 if v < 0 else 0)


def _tour(pts):
    pts = sorted(set(pts))
    n = len(pts)
    if n < 3:
        return pts
    dist = [[((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for b in pts] for a in pts]
    best = {(1, 0): (0.0, (0,))}
    for mask in range(1, 1 << n):
        if not mask & 1:
            continue
        for last in range(n):
            st = best.get((mask, last))
            if st is None:
                continue
            for nx in range(1, n):
                if (mask >> nx) & 1:
                    continue
                key = (mask | (1 << nx), nx)
                cand = (st[0] + dist[last][nx], st[1] + (nx,))
                old = best.get(key)
                if old is None or cand < old:
                    best[key] = cand
    full = (1 << n) - 1
    res = min((best[(full, l)][0] + dist[l][0], best[(full, l)][1]) for l in range(1, n))
    return [pts[i] for i in res[1]]


def _edge_cells(pts):
    h = _tour(pts)
    n = len(h)
    cells = []
    if n < 2:
        return cells
    if n == 2:
        pairs = [(h[0], h[1])]
    else:
        pairs = [(h[i], h[(i + 1) % n]) for i in range(n)]
    for a, b in pairs:
        dy = b[0] - a[0]
        dx = b[1] - a[1]
        if not (dy == 0 or dx == 0 or abs(dy) == abs(dx)):
            continue
        L = max(abs(dy), abs(dx))
        sy = _sign(dy)
        sx = _sign(dx)
        for k in range(L + 1):
            cells.append((a[0] + k * sy, a[1] + k * sx))
    return cells


def _rank(c):
    return RANK.get(c, 100 + c)


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in np.asarray(grid).tolist()]
    H = len(g)
    W = len(g[0]) if H else 0
    pos = {}
    for r in range(H):
        for c in range(W):
            v = g[r][c]
            if v != BG:
                pos.setdefault(v, []).append((r, c))
    out = [row[:] for row in g]
    shapes = {}
    for col, pts in pos.items():
        if len(pts) >= 2:
            shapes[col] = _edge_cells(pts)
    for col in sorted(shapes, key=_rank):
        for r, c in shapes[col]:
            out[r][c] = col
    comps = []
    for col, pts in pos.items():
        if len(pts) != 1:
            continue
        cy, cx = pts[0]
        found = None
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                y = cy + dy
                x = cx + dx
                if 0 <= y < H and 0 <= x < W:
                    v = g[y][x]
                    if v != BG and v != col and v in shapes:
                        found = (v, cy - y, cx - x)
        if found is not None:
            comps.append((col, found))
    comps.sort(key=lambda t: _rank(t[0]))
    for col, (v, oy, ox) in comps:
        for y, x in shapes[v]:
            ny = y + oy
            nx = x + ox
            if 0 <= ny < H and 0 <= nx < W and out[ny][nx] == BG:
                out[ny][nx] = col
    return out
'''


def build_program(d4, palette):
    pal = [int(palette[i]) for i in range(10)]
    bg = pal[0]
    rank = {}
    for c in range(10):
        rank[pal[c]] = c
    src = TEMPLATE.replace('__BG__', repr(bg)).replace('__RANK__', repr(rank))
    return src
