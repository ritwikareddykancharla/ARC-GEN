def build_program(d4, palette):
    pal = [int(x) for x in palette]
    marker = pal[0]
    order = [pal[2], pal[5], pal[8], pal[9]]
    src = '''import numpy as np

MARKER = %d
CROSS_ORDER = %r
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    for col in CROSS_ORDER:
        ys, xs = np.nonzero(g == col)
        cells = set(zip(ys.tolist(), xs.tolist()))
        if not cells:
            continue
        centre = None
        for (y, x) in sorted(cells):
            if all((y + dy, x + dx) in cells for dy, dx in DIRS):
                centre = (y, x)
                break
        if centre is None:
            continue
        cy, cx = centre
        best, bestlen = None, -1
        for dy, dx in DIRS:
            n = 0
            while (cy + dy * (n + 1), cx + dx * (n + 1)) in cells:
                n += 1
            if n > bestlen:
                best, bestlen = (dy, dx), n
        dy, dx = best
        def edge(ey, ex):
            if ey == -1:
                return (0, cx)
            if ey == 1:
                return (H - 1, cx)
            if ex == -1:
                return (cy, 0)
            return (cy, W - 1)
        ly, lx = edge(dy, dx)
        oy, ox = edge(-dy, -dx)
        out[ly, lx] = MARKER
        out[oy, ox] = col
    return out.tolist()
''' % (marker, order)
    return src
