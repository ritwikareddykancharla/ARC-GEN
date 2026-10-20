def build_program(d4, palette):
    # Image of the original unit vectors in visible coordinates.
    # R is the original row direction (down) and C is the original column direction (right).
    R = (1, 0)
    C = (0, 1)
    if d4 >= 4:
        C = (0, -1)
    for _ in range(d4 % 4):
        R = (R[1], -R[0])
        C = (C[1], -C[0])
    sy = R[0] + C[0]
    sx = R[1] + C[1]
    bg = int(palette[0])
    prog = '''import numpy as np
from collections import deque

BG = %d
SY = %d
SX = %d
KY = %d
KX = %d

def _components(g):
    h, w = g.shape
    seen = np.zeros((h, w), bool)
    objs = []
    for y in range(h):
        for x in range(w):
            if g[y, x] != BG and not seen[y, x]:
                col = g[y, x]
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == col:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                objs.append((int(col), cells))
    return objs

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    h, w = g.shape
    objs = _components(g)
    # order along the chaining axis (sequence direction)
    def key(o):
        cells = o[1]
        k = min(KY * y + KX * x for y, x in cells)
        return (k, min(y for y, x in cells), min(x for y, x in cells))
    objs.sort(key=key)
    out = np.full((h, w), BG, dtype=int)
    ay = 0 if SY > 0 else h - 1
    ax = 0 if SX > 0 else w - 1
    for col, cells in objs:
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        sy0 = y0 if SY > 0 else y1
        sx0 = x0 if SX > 0 else x1
        ey = y1 if SY > 0 else y0
        ex = x1 if SX > 0 else x0
        dy = ay - sy0
        dx = ax - sx0
        for y, x in cells:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                out[ny, nx] = col
        ay = ey + dy
        ax = ex + dx
    return out.tolist()
''' % (bg, sy, sx, C[0], C[1])
    return prog
