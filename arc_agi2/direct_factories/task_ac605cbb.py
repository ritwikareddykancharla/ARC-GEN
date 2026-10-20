def build_program(d4, palette):
    d4 = int(d4) % 8
    P = [int(p) for p in palette]

    def tf(v):
        dy, dx = v
        if d4 >= 4:
            dx = -dx
        for _ in range(d4 % 4):
            dy, dx = dx, -dy
        return (dy, dx)

    native = {1: ((0, 1), 2, (-1, 2)), 2: ((0, -1), 3, (0, -4)), 3: ((1, 0), 2, (3, 0)), 6: ((-1, 0), 5, (-6, 0))}
    stamps = {}
    for c, (d, L, o) in native.items():
        stamps[P[c]] = (tf(d), L, tf(o))
    diag = tf((1, -1))
    bg = P[0]
    grey = P[5]
    yellow = P[4]

    src = '''import numpy as np

STAMPS = %r
DIAG = %r
BG = %d
GREY = %d
CROSS = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    seeds = [(y, x, int(g[y, x])) for y in range(H) for x in range(W)
             if int(g[y, x]) != BG and int(g[y, x]) in STAMPS]
    cover = np.zeros((H, W), dtype=int)
    for y, x, c in seeds:
        (dy, dx), L, _ = STAMPS[c]
        for k in range(1, L + 1):
            yy, xx = y + dy * k, x + dx * k
            if 0 <= yy < H and 0 <= xx < W:
                cover[yy, xx] += 1
                if out[yy, xx] == BG:
                    out[yy, xx] = GREY
    for y, x, c in seeds:
        oy, ox = STAMPS[c][2]
        yy, xx = y + oy, x + ox
        if 0 <= yy < H and 0 <= xx < W:
            out[yy, xx] = c
    crossings = [(y, x) for y in range(H) for x in range(W) if cover[y, x] >= 2]
    ddy, ddx = DIAG
    for y, x in crossings:
        out[y, x] = CROSS
        yy, xx = y + ddy, x + ddx
        while 0 <= yy < H and 0 <= xx < W:
            if out[yy, xx] == BG:
                out[yy, xx] = CROSS
            yy += ddy
            xx += ddx
    return out.tolist()
''' % (stamps, diag, bg, grey, yellow)
    return src
