def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[4])
    src = '''import numpy as np
from collections import deque

BG = %d
FILL = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    reach = np.zeros((h, w), dtype=bool)
    q = deque()
    for y in range(h):
        for x in range(w):
            if (y == 0 or y == h - 1 or x == 0 or x == w - 1) and g[y, x] == BG and not reach[y, x]:
                reach[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not reach[ny, nx] and g[ny, nx] == BG:
                reach[ny, nx] = True
                q.append((ny, nx))
    out = g.copy()
    out[(g == BG) & ~reach] = FILL
    return out.tolist()
''' % (bg, fill)
    return src
