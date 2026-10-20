def build_program(d4, palette):
    grey = int(palette[5])
    bg = int(palette[0])
    src = '''import numpy as np
from collections import deque

GREY = %d
BG = %d

def _components(mask):
    h, w = mask.shape
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
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    for cells in _components(g == GREY):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        hh = (y1 - y0 + 1) // 2
        hw = (x1 - x0 + 1) // 2
        quads = [
            ((y0 - 1, x0 - 1), (y0, y0 + hh, x0, x0 + hw)),
            ((y0 - 1, x1 + 1), (y0, y0 + hh, x0 + hw, x1 + 1)),
            ((y1 + 1, x0 - 1), (y0 + hh, y1 + 1, x0, x0 + hw)),
            ((y1 + 1, x1 + 1), (y0 + hh, y1 + 1, x0 + hw, x1 + 1)),
        ]
        for (my, mx), (a, b, c, d) in quads:
            if 0 <= my < H and 0 <= mx < W:
                col = int(g[my, mx])
                out[a:b, c:d] = col
                out[my, mx] = BG
    return out.tolist()
''' % (grey, bg)
    return src
