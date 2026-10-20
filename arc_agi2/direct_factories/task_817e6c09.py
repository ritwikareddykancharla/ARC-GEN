def build_program(d4, palette):
    # Original mechanism: 2x2 squares of colour 2 on background 0, ordered by
    # their position along the original +x (east) axis. The square farthest
    # east gets colour 8, then every second square going west.
    # Find where original east points in visible coordinates.
    dy, dx = 0, 1
    if d4 >= 4:
        dx = -1  # reversing each row turns east into west
    for _ in range(d4 % 4):
        dy, dx = dx, -dy  # one clockwise turn: east->south->west->north
    sq = int(palette[2])
    hi = int(palette[8])
    template = '''import numpy as np
from collections import deque

DY = __DY__
DX = __DX__
SQ = __SQ__
HI = __HI__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y, x] == SQ and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == SQ:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                comps.append(cells)
    # Position of each square along the original sweep axis, measured at its
    # trailing edge. All squares are 2x2, so any consistent edge gives the
    # same order.
    def key(cells):
        lead = min(DY * cy + DX * cx for cy, cx in cells)
        return (lead, min(cells))
    order = sorted(comps, key=key, reverse=True)
    # The square farthest along the axis gets HI, then every second one after it.
    for i, cells in enumerate(order):
        if i % 2 == 0:
            for cy, cx in cells:
                out[cy, cx] = HI
    return out.tolist()
'''
    return (template.replace('__DY__', str(dy))
                    .replace('__DX__', str(dx))
                    .replace('__SQ__', str(sq))
                    .replace('__HI__', str(hi)))
