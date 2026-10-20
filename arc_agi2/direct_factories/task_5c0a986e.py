def build_program(d4, palette):
    def tf(dr, dc):
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc
    d1 = tf(-1, -1)
    d2 = tf(1, 1)
    bg = int(palette[0])
    c1 = int(palette[1])
    c2 = int(palette[2])
    src = '''import numpy as np

BG = %d
RAYS = [(%d, (%d, %d)), (%d, (%d, %d))]

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    orig = g.copy()
    for colour, (dr, dc) in RAYS:
        ys, xs = np.nonzero(orig == colour)
        if len(ys) == 0:
            continue
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        y = y1 if dr > 0 else y0
        x = x1 if dc > 0 else x0
        y += dr
        x += dc
        while 0 <= y < H and 0 <= x < W:
            if g[y, x] == BG:
                g[y, x] = colour
            y += dr
            x += dc
    return g.tolist()
''' % (bg, c1, d1[0], d1[1], c2, d2[0], d2[1])
    return src
