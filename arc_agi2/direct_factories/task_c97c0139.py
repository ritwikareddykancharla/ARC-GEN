def build_program(d4, palette):
    bg = int(palette[0])
    line = int(palette[2])
    fill = int(palette[8])
    src = '''import numpy as np
from collections import deque

BG = %d
LINE = %d
FILL = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
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
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    for cells in _components(g == LINE):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        if y0 == y1:
            # horizontal segment: triangles above and below, shrinking by one cell at each end per row
            d = 1
            while x0 + d <= x1 - d:
                for y in (y0 - d, y0 + d):
                    if 0 <= y < H:
                        for x in range(x0 + d, x1 - d + 1):
                            if out[y, x] == BG:
                                out[y, x] = FILL
                d += 1
        else:
            # vertical segment: triangles left and right, shrinking by one cell at each end per column
            d = 1
            while y0 + d <= y1 - d:
                for x in (x0 - d, x0 + d):
                    if 0 <= x < W:
                        for y in range(y0 + d, y1 - d + 1):
                            if out[y, x] == BG:
                                out[y, x] = FILL
                d += 1
    return out.tolist()
''' % (bg, line, fill)
    return src
