def build_program(d4, palette):
    k = int(d4) % 4
    vertical = (k % 2 == 0)
    bg = int(palette[0])
    wall = int(palette[2])
    shape = int(palette[4])
    src = '''import numpy as np
from collections import deque

BG = %d
WALL = %d
SHAPE = %d
VERTICAL = %s


def _comps(mask, diag):
    h, w = mask.shape
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _span(c):
    # coordinate running along the wall
    return c[0] if VERTICAL else c[1]


def _perp(c):
    # coordinate across the wall
    return c[1] if VERTICAL else c[0]


def _mirror(c, axis):
    if VERTICAL:
        return (c[0], 2 * axis - c[1])
    return (2 * axis - c[0], c[1])


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    walls = _comps(g == WALL, False)
    if not walls:
        return out.tolist()
    info = []
    for w in walls:
        perps = sorted(_perp(c) for c in w)
        axis = perps[len(perps) // 2]
        span = set(_span(c) for c in w)
        info.append((axis, span, set(w)))
    owned = [[] for _ in walls]
    for comp in _comps(g == SHAPE, True):
        best = None
        for i, (axis, span, wset) in enumerate(info):
            cs = [c for c in comp if _span(c) in span]
            if not cs:
                continue
            adj = False
            for (y, x) in comp:
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (y + dy, x + dx) in wset:
                        adj = True
                        break
                if adj:
                    break
            d = min(abs(_perp(c) - axis) for c in cs)
            key = (0 if adj else 1, -len(cs) / float(len(comp)), d, i)
            if best is None or key < best[0]:
                best = (key, i)
        if best is not None:
            owned[best[1]].extend(comp)
    markers = [(y, x, int(g[y, x])) for y in range(H) for x in range(W)
               if int(g[y, x]) not in (BG, WALL, SHAPE)]
    assign = {}
    used = set()
    mirrored = []
    for i, (axis, span, wset) in enumerate(info):
        mset = set(_mirror(c, axis) for c in owned[i])
        mirrored.append(mset)
    # Primary: marker lies exactly on the mirror image of the wall's shape.
    for i in range(len(walls)):
        if not owned[i]:
            continue
        for mi, (my, mx, mc) in enumerate(markers):
            if mi in used:
                continue
            if (my, mx) in mirrored[i]:
                assign[i] = mi
                used.add(mi)
                break
    # Fallback: greedy nearest (Chebyshev) for any wall left without a marker.
    pairs = []
    for i, w in enumerate(walls):
        if i in assign or not owned[i]:
            continue
        for mi, (my, mx, mc) in enumerate(markers):
            if mi in used:
                continue
            d = min(max(abs(my - y), abs(mx - x)) for (y, x) in w)
            pairs.append((d, i, mi))
    pairs.sort()
    for d, i, mi in pairs:
        if i in assign or mi in used:
            continue
        assign[i] = mi
        used.add(mi)
    for i in range(len(walls)):
        if i not in assign:
            continue
        mc = markers[assign[i]][2]
        for (y, x) in mirrored[i]:
            if 0 <= y < H and 0 <= x < W and (out[y, x] == BG or out[y, x] == mc):
                out[y, x] = mc
    return out.tolist()
''' % (bg, wall, shape, 'True' if vertical else 'False')
    return src
