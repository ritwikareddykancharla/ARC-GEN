def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[1])
    seed = int(palette[2])
    src = '''import numpy as np

BG = %d
FILL = %d
SEED = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    ys, xs = np.where(g == SEED)
    if len(ys) == 0:
        ys, xs = np.where(g != BG)
    if len(ys) == 0:
        return out.tolist()
    colour = int(g[ys[0], xs[0]])
    rows = sorted(int(y) for y in ys)
    cols = sorted(int(x) for x in xs)
    for y in rows:
        out[y, :] = colour
    for x in cols:
        out[:, x] = colour
    r0, r1 = rows[0] + 1, rows[-1]
    c0, c1 = cols[0] + 1, cols[-1]
    if r1 > r0 and c1 > c0:
        out[r0:r1, c0:c1] = FILL
    return out.tolist()
''' % (bg, fill, seed)
    return src
