def build_program(d4, palette):
    bg = int(palette[0])
    fg = int(palette[1])
    fill = int(palette[3])
    src = '''import numpy as np
from collections import deque

BG = %d
FG = %d
FILL = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
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

def _encloses(objmask):
    # True if some non-object cell cannot reach the grid border through
    # non-object cells (4-connected). Only this object's own cells block.
    h, w = objmask.shape
    free = ~objmask
    reach = np.zeros((h, w), bool)
    q = deque()
    for y in range(h):
        for x in range(w):
            if (y == 0 or x == 0 or y == h - 1 or x == w - 1) and free[y, x]:
                reach[y, x] = True
                q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and free[ny, nx] and not reach[ny, nx]:
                reach[ny, nx] = True
                q.append((ny, nx))
    return bool(np.any(free & ~reach))

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    colours = sorted(set(int(v) for v in g.ravel()) - {BG})
    for col in colours:
        for cells in _components(g == col):
            m = np.zeros(g.shape, bool)
            for y, x in cells:
                m[y, x] = True
            if _encloses(m):
                for y, x in cells:
                    out[y, x] = FILL
    return out.tolist()
''' % (bg, fg, fill)
    return src
