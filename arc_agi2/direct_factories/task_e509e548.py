def build_program(d4, palette):
    bg = int(palette[0])
    fg = int(palette[3])
    c_l = int(palette[1])
    c_h = int(palette[2])
    c_u = int(palette[6])
    src = '''import numpy as np
from collections import deque

BG = %d
FG = %d
C_L = %d
C_H = %d
C_U = %d

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
    out = g.copy()
    mask = (g == FG)
    if not mask.any():
        mask = (g != BG)
    for cells in _components(mask):
        cs = set(cells)
        branch = False
        corners = 0
        for (y, x) in cs:
            hn = ((y, x - 1) in cs) + ((y, x + 1) in cs)
            vn = ((y - 1, x) in cs) + ((y + 1, x) in cs)
            if hn + vn >= 3:
                branch = True
            if hn == 1 and vn == 1:
                corners += 1
        if branch:
            col = C_H
        elif corners >= 2:
            col = C_U
        else:
            col = C_L
        for (y, x) in cs:
            out[y, x] = col
    return out.tolist()
''' % (bg, fg, c_l, c_h, c_u)
    return src
