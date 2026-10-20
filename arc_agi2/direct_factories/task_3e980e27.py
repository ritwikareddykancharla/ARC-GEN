def build_program(d4, palette):
    bg = int(palette[0])
    flip_key = int(palette[2])
    # Original mechanism: copies keyed by red (2) are mirrored left-right (column offsets negated).
    # Under D4 the mirror is conjugated by the linear part of the transform. An odd number of
    # quarter turns swaps the axes, so the mirror becomes up-down (row offsets negated).
    # The optional row-reversal prefix commutes with a left-right mirror, so it changes nothing.
    rot = d4 % 4
    flip_rows = 1 if rot in (1, 3) else 0
    template = '''import numpy as np
from collections import deque

BG = __BG__
FLIP_KEY = __FK__
FLIP_ROWS = __FR__


def _components(g):
    H, W = g.shape
    seen = np.zeros((H, W), dtype=bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y, x] != BG and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < H and 0 <= nx < W and g[ny, nx] != BG and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                comps.append(sorted(cells))
    return comps


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    comps = _components(g)
    templates = []
    lone = []
    for cells in comps:
        if len(cells) == 1:
            lone.append(cells[0])
            continue
        counts = {}
        for (y, x) in cells:
            c = int(g[y, x])
            counts[c] = counts.get(c, 0) + 1
        singles = [c for c, n in counts.items() if n == 1]
        if len(singles) != 1 or len(counts) < 2:
            continue
        key = singles[0]
        ky, kx = [(y, x) for (y, x) in cells if int(g[y, x]) == key][0]
        offs = []
        for (y, x) in cells:
            c = int(g[y, x])
            if c == key:
                continue
            dy, dx = y - ky, x - kx
            if key == FLIP_KEY:
                if FLIP_ROWS:
                    dy = -dy
                else:
                    dx = -dx
            offs.append((dy, dx, c))
        templates.append((key, offs))
    out = g.copy()
    for key, offs in templates:
        for (ty, tx) in lone:
            if int(g[ty, tx]) != key:
                continue
            for dy, dx, c in offs:
                Y, X = ty + dy, tx + dx
                if 0 <= Y < H and 0 <= X < W and out[Y, X] == BG:
                    out[Y, X] = c
    return out.tolist()
'''
    return template.replace('__BG__', str(bg)).replace('__FK__', str(flip_key)).replace('__FR__', str(flip_rows))
