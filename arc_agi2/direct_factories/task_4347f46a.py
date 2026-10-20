def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np
from collections import deque

BG = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
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
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    src = g.copy()
    colours = sorted(set(src.ravel().tolist()) - {BG})
    for c in colours:
        for cells in _components(src == c):
            ys = [p[0] for p in cells]
            xs = [p[1] for p in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            if y1 - y0 >= 2 and x1 - x0 >= 2:
                g[y0 + 1:y1, x0 + 1:x1] = BG
    return g.tolist()
''' % bg
    return src
