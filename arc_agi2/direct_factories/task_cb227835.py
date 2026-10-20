def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[8])
    line = int(palette[3])
    src = '''import numpy as np

BG = %d
MARK = %d
LINE = %d


def _sign(v):
    return (v > 0) - (v < 0)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    h, w = g.shape
    pts = [(int(p[0]), int(p[1])) for p in np.argwhere(g == MARK)]
    if len(pts) != 2:
        pts = [(int(p[0]), int(p[1])) for p in np.argwhere(g != BG)]
    if len(pts) < 2:
        return g.tolist()
    pts.sort()
    (ay, ax), (by, bx) = pts[0], pts[-1]
    dy, dx = by - ay, bx - ax
    sy, sx = _sign(dy), _sign(dx)
    nd = min(abs(dy), abs(dx))
    ns = max(abs(dy), abs(dx)) - nd
    # The straight leg runs along whichever visible axis has the larger separation.
    if abs(dy) > abs(dx):
        st = (sy, 0)
    elif abs(dx) > abs(dy):
        st = (0, sx)
    else:
        st = (0, 0)
        ns = 0
    dg = (sy, sx)

    def draw(order):
        y, x = ay, ax
        for (vy, vx), n in order:
            for _ in range(n):
                y += vy
                x += vx
                if 0 <= y < h and 0 <= x < w and g[y, x] == BG:
                    g[y, x] = LINE

    # Route 1: straight first, then diagonal.
    draw([(st, ns), (dg, nd)])
    # Route 2: diagonal first, then straight. Together they close the parallelogram.
    draw([(dg, nd), (st, ns)])
    return g.tolist()
''' % (bg, mark, line)
    return src
