def build_program(d4, palette):
    pal = [int(palette[i]) for i in range(10)]
    obj = pal[0]
    bg = pal[5]
    c3 = pal[1]
    c2 = pal[2]
    c1 = pal[3]
    src = '''import numpy as np
from collections import deque

OBJ = %d
BG = %d
SIZE_COLOUR = {3: %d, 2: %d, 1: %d}

def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
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
    comps = _components(g == OBJ)
    for cells in comps:
        s = len(cells)
        if s in SIZE_COLOUR:
            col = SIZE_COLOUR[s]
        else:
            col = SIZE_COLOUR[3]
        for y, x in cells:
            out[y, x] = col
    return out.tolist()
''' % (obj, bg, c3, c2, c1)
    return src
