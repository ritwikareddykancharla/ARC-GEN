def build_program(d4, palette):
    k = d4 % 4
    refl = d4 >= 4
    transposed = (k % 2 == 1)
    from_end = ((k >= 2) != refl)
    bg = int(palette[0])
    src = '''import numpy as np
from collections import deque

BG = __BG__
TRANSPOSED = __TR__
FROM_END = __FE__


def _components(g):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y, x] == BG or seen[y, x]:
                continue
            col = int(g[y, x])
            seen[y, x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == col:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            comps.append((col, cells))
    return comps


def solve(demonstrations, grid):
    orig = np.array(grid, dtype=int)
    g = orig.copy()
    for col, cells in _components(orig):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        if not TRANSPOSED:
            # long axis horizontal: cut interior rows at odd offsets from the card's start edge
            if FROM_END:
                cut = list(range(x1 - 1, x0, -2))
            else:
                cut = list(range(x0 + 1, x1, 2))
            for y in range(y0 + 1, y1):
                for x in cut:
                    if orig[y, x] == col:
                        g[y, x] = BG
        else:
            # long axis vertical: cut interior columns at odd offsets from the card's start edge
            if FROM_END:
                cut = list(range(y1 - 1, y0, -2))
            else:
                cut = list(range(y0 + 1, y1, 2))
            for x in range(x0 + 1, x1):
                for y in cut:
                    if orig[y, x] == col:
                        g[y, x] = BG
    return g.tolist()
'''
    src = src.replace('__BG__', str(bg)).replace('__TR__', 'True' if transposed else 'False').replace('__FE__', 'True' if from_end else 'False')
    return src
