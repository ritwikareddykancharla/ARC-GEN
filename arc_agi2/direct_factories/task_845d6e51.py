def build_program(d4, palette):
    bg = int(palette[0])
    green = int(palette[3])
    wall = int(palette[5])
    src = '''import numpy as np
from collections import deque

BG = __BG__
GREEN = __GREEN__
WALL = __WALL__


def _comps(g, colour):
    h, w = g.shape
    seen = np.zeros((h, w), bool)
    out = []
    for y in range(h):
        for x in range(w):
            if g[y, x] == colour and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == colour:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _norm(cells):
    best = None
    for k in range(8):
        q = []
        for y, x in cells:
            if k & 4:
                y, x = x, y
            if k & 1:
                y = -y
            if k & 2:
                x = -x
            q.append((y, x))
        my = min(p[0] for p in q)
        mx = min(p[1] for p in q)
        t = tuple(sorted((a - my, b - mx) for a, b in q))
        if best is None or t < best:
            best = t
    return best


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    legend = {}
    sizes = {}
    for colour in sorted(set(g.ravel().tolist()) - {BG, GREEN, WALL}):
        for comp in _comps(g, colour):
            legend.setdefault(_norm(comp), colour)
            sizes.setdefault(len(comp), set()).add(colour)
    for comp in _comps(g, GREEN):
        col = legend.get(_norm(comp))
        if col is None:
            cands = sizes.get(len(comp), set())
            if len(cands) == 1:
                col = next(iter(cands))
        if col is None:
            continue
        for y, x in comp:
            out[y, x] = col
    return out.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__GREEN__', str(green)).replace('__WALL__', str(wall))
