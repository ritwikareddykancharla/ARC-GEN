def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np
from collections import deque

BG = %d

def _components(g, colour):
    h, w = g.shape
    seen = np.zeros((h, w), bool)
    comps = []
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
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    best = None
    best_key = None
    for colour in sorted(set(g.ravel().tolist()) - {BG}):
        for cells in _components(g, colour):
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            hh = max(ys) - min(ys) + 1
            ww = max(xs) - min(xs) + 1
            area = hh * ww
            key = (area, area - len(cells), len(cells))
            if best_key is None or key > best_key:
                best_key = key
                best = colour
    if best is None:
        best = BG
    return [[int(best), int(best)], [int(best), int(best)]]
''' % bg
    return src
