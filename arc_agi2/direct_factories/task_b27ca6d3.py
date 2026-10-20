def build_program(d4, palette):
    bg = int(palette[0])
    red = int(palette[2])
    green = int(palette[3])
    src = '''import numpy as np
from collections import deque

BG = %d
RED = %d
GREEN = %d

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
    H, W = g.shape
    colours = sorted(set(int(v) for v in src.ravel()) - {BG})
    for col in colours:
        for cells in _components(src == col):
            if len(cells) != 2:
                continue
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            for y in range(y0 - 1, y1 + 2):
                for x in range(x0 - 1, x1 + 2):
                    if 0 <= y < H and 0 <= x < W and g[y, x] == BG:
                        g[y, x] = GREEN
    return g.tolist()
''' % (bg, red, green)
    return src
