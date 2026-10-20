def build_program(d4, palette):
    bg = int(palette[0])
    # A rotation commutes with a quarter turn. A reflection turns clockwise into counter-clockwise.
    turn_sign = -1 if d4 < 4 else 1  # numpy rot90 sign: -1 = clockwise, +1 = counter-clockwise
    src = '''import numpy as np
from collections import deque

BG = %d
TURN_SIGN = %d


def _clusters(mask, radius):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
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
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                out.append(cells)
    return out


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    m = g != BG
    if not m.any():
        return g.tolist()
    # Figure: largest cluster of diagonal components merged within Chebyshev distance 2.
    groups = _clusters(m, 2)
    struct = max(groups, key=len)
    sset = set(struct)
    ys = [p[0] for p in struct]
    xs = [p[1] for p in struct]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    rest = m.copy()
    for y, x in struct:
        rest[y, x] = False
    # Legend: each remaining 8-connected single-colour piece gives colour -> cell count.
    leg = {}
    for comp in _clusters(rest, 1):
        col = int(g[comp[0]])
        leg[col] = leg.get(col, 0) + len(comp)
    S = g[y0:y1 + 1, x0:x1 + 1].copy()
    out = np.full_like(S, BG)
    cols = sorted(int(c) for c in np.unique(S) if c != BG)
    # Unrotated layers are written first, then the rotated ones.
    for col in cols:
        if leg.get(col, 0) %% 4 == 0:
            out[S == col] = col
    for col in cols:
        k = leg.get(col, 0) %% 4
        if k == 0:
            continue
        mask = np.rot90(S == col, TURN_SIGN * k)
        if mask.shape == out.shape:
            out[mask] = col
        else:
            out[S == col] = col
    return out.tolist()
''' % (bg, turn_sign)
    return src
