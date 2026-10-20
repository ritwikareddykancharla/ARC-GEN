def build_program(d4, palette):
    pal = [int(palette[i]) for i in range(10)]
    bg = pal[0]
    shape = pal[8]
    table = {1: pal[1], 2: pal[3], 3: pal[2], 4: pal[4]}
    template = '''import numpy as np
from collections import deque

# Visible-coordinate constants (palette already applied by the factory).
BG = __BG__
SHAPE = __SHAPE__
HOLE_TABLE = __TABLE__
PAL = __PAL__


def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
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
                out.append(cells)
    return out


def _count_holes(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    occ = np.zeros((y1 - y0 + 3, x1 - x0 + 3), dtype=bool)
    for y, x in cells:
        occ[y - y0 + 1, x - x0 + 1] = True
    H, W = occ.shape
    n = 0
    for comp in _components(~occ):
        if not any(y == 0 or y == H - 1 or x == 0 or x == W - 1 for y, x in comp):
            n += 1
    return n


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    out = g.copy()
    colours = sorted(set(int(v) for v in g.ravel().tolist()) - {BG})
    for col in colours:
        for cells in _components(g == col):
            n = _count_holes(cells)
            if n in HOLE_TABLE:
                new = HOLE_TABLE[n]
            elif 0 <= n <= 9:
                new = PAL[n]
            else:
                new = col
            for y, x in cells:
                out[y, x] = new
    return out.tolist()
'''
    prog = template.replace('__BG__', repr(bg))
    prog = prog.replace('__SHAPE__', repr(shape))
    prog = prog.replace('__TABLE__', repr(table))
    prog = prog.replace('__PAL__', repr(pal))
    return prog
