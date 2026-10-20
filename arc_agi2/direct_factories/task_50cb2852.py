def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[8])
    src = '''import numpy as np
from collections import deque

BG = %d
FILL = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    seen = np.zeros((h, w), dtype=bool)
    for y in range(h):
        for x in range(w):
            if seen[y, x] or g[y, x] == BG:
                continue
            col = g[y, x]
            q = deque([(y, x)])
            seen[y, x] = True
            y0 = y1 = y
            x0 = x1 = x
            while q:
                cy, cx = q.popleft()
                if cy < y0: y0 = cy
                if cy > y1: y1 = cy
                if cx < x0: x0 = cx
                if cx > x1: x1 = cx
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == col:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            if y1 - y0 >= 2 and x1 - x0 >= 2:
                out[y0 + 1:y1, x0 + 1:x1] = FILL
    return out.tolist()
''' % (bg, fill)
    return src
