TEMPLATE = '''import numpy as np
from collections import Counter, deque

AXIS_COLS = __AXIS__
FIRST_START = __FIRST__
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _perp(d):
    return (d[1], -d[0])


def _components(mask):
    h, w = mask.shape
    seen = np.zeros(mask.shape, dtype=bool)
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
                    for ddy in (-1, 0, 1):
                        for ddx in (-1, 0, 1):
                            ny, nx = cy + ddy, cx + ddx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _first_panel(g):
    H, W = g.shape
    bg = Counter(g.ravel().tolist()).most_common(1)[0][0]
    if AXIS_COLS:
        cuts = [x for x in range(W) if g[0, x] != bg and np.all(g[:, x] == g[0, x])]
        n = W
    else:
        cuts = [y for y in range(H) if g[y, 0] != bg and np.all(g[y, :] == g[y, 0])]
        n = H
    edges = [-1] + cuts + [n]
    spans = [(a + 1, b - 1) for a, b in zip(edges, edges[1:]) if b - a > 1]
    if not spans:
        spans = [(0, n - 1)]
    a, b = spans[0] if FIRST_START else spans[-1]
    if AXIS_COLS:
        return g[:, a:b + 1].copy()
    return g[a:b + 1, :].copy()


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    P = _first_panel(g)
    H, W = P.shape
    bg = int(Counter(P.ravel().tolist()).most_common(1)[0][0])
    comps = _components(P != bg)
    if not comps:
        return P.tolist()
    shape = max(comps, key=len)
    col = int(P[shape[0][0], shape[0][1]])
    sset = set(shape)
    dots = set(c for comp in comps if comp is not shape for c in comp)
    tip, d = None, None
    for dy, dx in DIRS:
        vals = [y * dy + x * dx for y, x in shape]
        m = max(vals)
        ext = [c for c in shape if c[0] * dy + c[1] * dx == m]
        if len(ext) != 1:
            continue
        t = ext[0]
        if dy != 0:
            refl = set((y, 2 * t[1] - x) for y, x in shape)
        else:
            refl = set((2 * t[0] - y, x) for y, x in shape)
        if refl == sset:
            tip, d = t, (dy, dx)
            break
    if tip is None:
        tip, d = shape[0], (-1, 0)
    p = _perp(d)
    local = [((y - tip[0]) * d[0] + (x - tip[1]) * d[1],
              (y - tip[0]) * p[0] + (x - tip[1]) * p[1]) for y, x in shape]

    def ahead(t, dd):
        y, x = t[0] + dd[0], t[1] + dd[1]
        while 0 <= y < H and 0 <= x < W:
            if (y, x) in dots:
                return (y, x)
            y += dd[0]
            x += dd[1]
        return None

    guard = len(dots) + 2
    while guard > 0:
        guard -= 1
        nxt = ahead(tip, d)
        nd = d
        if nxt is None:
            best = None
            pp = _perp(d)
            for cand in (pp, (-pp[0], -pp[1])):
                hit = ahead(tip, cand)
                if hit is not None:
                    dist = abs(hit[0] - tip[0]) + abs(hit[1] - tip[1])
                    if best is None or dist < best[0]:
                        best = (dist, hit, cand)
            if best is None:
                break
            nxt, nd = best[1], best[2]
        dots.discard(nxt)
        tip, d = nxt, nd
    out = np.full((H, W), bg, dtype=int)
    pp = _perp(d)
    for a, b in local:
        y = tip[0] + a * d[0] + b * pp[0]
        x = tip[1] + a * d[1] + b * pp[1]
        if 0 <= y < H and 0 <= x < W:
            out[y, x] = col
    return out.tolist()
'''


def build_program(d4, palette):
    # Track the original 'towards first panel' direction (left) through the D4 map.
    dy, dx = 0, -1
    if d4 >= 4:
        dx = -dx
    for _ in range(d4 % 4):
        dy, dx = dx, -dy
    if dy == 0:
        axis_cols = 1
        first_start = 1 if dx < 0 else 0
    else:
        axis_cols = 0
        first_start = 1 if dy < 0 else 0
    return TEMPLATE.replace('__AXIS__', str(axis_cols)).replace('__FIRST__', str(first_start))
