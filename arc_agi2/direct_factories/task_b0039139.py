def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(palette[i]) for i in range(10)]

    def apply(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc

    rev_rows = False
    rev_cols = False
    for v in ((0, 1), (1, 0)):
        dr, dc = apply(v)
        if dr != 0:
            rev_rows = dr < 0
        else:
            rev_cols = dc < 0

    header = (
        'DIV = %d\n' % pal[1] +
        'BG = %d\n' % pal[0] +
        'BAR = %d\n' % pal[3] +
        'MOT = %d\n' % pal[4] +
        'REV_ROWS = %r\n' % rev_rows +
        'REV_COLS = %r\n' % rev_cols
    )

    body = '''
import numpy as np
from collections import deque

''' + header + '''

def _count_components(mask):
    mask = np.asarray(mask, bool)
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    n = 0
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                n += 1
                seen[y, x] = True
                q = deque([(y, x)])
                while q:
                    cy, cx = q.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
    return n


def _dominant(panel):
    vals = np.asarray(panel, int).ravel()
    return int(np.bincount(vals, minlength=10).argmax())


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    div_rows = [y for y in range(H) if np.all(g[y, :] == DIV)]
    if div_rows:
        stacked = True
        lines = div_rows
        L = H
        rev = REV_ROWS
    else:
        stacked = False
        lines = [x for x in range(W) if np.all(g[:, x] == DIV)]
        L = W
        rev = REV_COLS
    bounds = [-1] + lines + [L]
    segs = [(bounds[i] + 1, bounds[i + 1]) for i in range(len(bounds) - 1)
            if bounds[i + 1] - bounds[i] > 1]
    panels = [g[a:b, :] if stacked else g[:, a:b] for a, b in segs]
    if rev:
        panels = panels[::-1]
    # Sanity: the motif panel always has a background border; solid panels never do.
    if (not np.any(panels[0] == BG)) and np.any(panels[-1] == BG):
        panels = panels[::-1]
    p1 = panels[0]
    p2 = panels[1]
    p3 = panels[-2]
    p4 = panels[-1]
    A = _dominant(p3)
    B = _dominant(p4)
    m = (p1 == MOT)
    ys, xs = np.where(m)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    n = _count_components(p2 == BAR)
    tile = np.where(m, A, B)
    h, w = tile.shape
    if stacked:
        out = np.full((n * h + (n - 1), w), B, dtype=int)
        for i in range(n):
            out[i * (h + 1):i * (h + 1) + h, :] = tile
    else:
        out = np.full((h, n * w + (n - 1)), B, dtype=int)
        for i in range(n):
            out[:, i * (w + 1):i * (w + 1) + w] = tile
    return out.tolist()
'''
    return body
