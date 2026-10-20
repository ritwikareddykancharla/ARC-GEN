def build_program(d4, palette):
    bg = int(palette[0])
    border = int(palette[1])
    ring_a = int(palette[2])
    ring_b = int(palette[3])
    src = '''import numpy as np
from collections import deque

BG = %d
BORDER = %d
RING_ODD = %d
RING_EVEN = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps = []
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
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    for comp in _components(g != BG):
        ys = [c[0] for c in comp]
        xs = [c[1] for c in comp]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        for y, x in comp:
            d = min(y - y0, y1 - y, x - x0, x1 - x)
            if d == 0:
                c = BORDER
            elif d %% 2 == 1:
                c = RING_ODD
            else:
                c = RING_EVEN
            out[y, x] = c
    return out.tolist()
''' % (bg, border, ring_a, ring_b)
    return src
