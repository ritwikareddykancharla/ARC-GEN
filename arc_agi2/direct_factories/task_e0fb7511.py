def build_program(d4, palette):
    z = int(palette[0])
    e = int(palette[8])
    src = '''import numpy as np
from collections import deque

ZERO = %d
MARK = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
    comps = []
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
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    comps = _components(g == ZERO)
    comps.sort(key=lambda c: -len(c))
    for c in comps:
        if len(c) < 2:
            continue
        for y, x in c:
            out[y, x] = MARK
    return out.tolist()
''' % (z, e)
    return src
