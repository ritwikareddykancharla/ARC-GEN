def build_program(d4, palette):
    bg = int(palette[0])
    big = int(palette[8])
    small = int(palette[7])
    src = '''import numpy as np
from collections import deque

BG = %d
BIG = %d
SMALL = %d

def _regions(g):
    h, w = g.shape
    seen = np.zeros((h, w), bool)
    regs = []
    for y in range(h):
        for x in range(w):
            if g[y, x] == BG and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and g[ny, nx] == BG and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                regs.append(cells)
    return regs

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    regs = _regions(g)
    if not regs:
        return out.tolist()
    regs = sorted(regs, key=len)
    for y, x in regs[-1]:
        out[y, x] = BIG
    for y, x in regs[0]:
        out[y, x] = SMALL
    return out.tolist()
''' % (bg, big, small)
    return src
