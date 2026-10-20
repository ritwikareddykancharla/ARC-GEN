def build_program(d4, palette):
    bg = int(palette[0])
    dot = int(palette[9])
    src = '''import numpy as np
from collections import deque

BG = %d
DOT = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
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
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    comps = _components(g != BG)
    best = None
    for cells in comps:
        n = sum(1 for (y, x) in cells if g[y, x] == DOT)
        if best is None or n < best[0]:
            best = (n, cells)
    if best is not None:
        ys = [c[0] for c in best[1]]
        xs = [c[1] for c in best[1]]
        out[min(ys):max(ys) + 1, min(xs):max(xs) + 1] = BG
    return out.tolist()
''' % (bg, dot)
    return src
