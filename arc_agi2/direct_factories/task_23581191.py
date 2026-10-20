def build_program(d4, palette):
    bg = int(palette[0])
    cross_col = int(palette[2])
    src = '''import numpy as np

BG = %d
CROSS = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    seeds = [(y, x, int(g[y, x])) for y in range(H) for x in range(W) if g[y, x] != BG]
    count = np.zeros((H, W), dtype=int)
    for y, x, c in seeds:
        out[y, :] = c
        out[:, x] = c
        reach = np.zeros((H, W), dtype=bool)
        reach[y, :] = True
        reach[:, x] = True
        count += reach.astype(int)
    out[count >= 2] = CROSS
    return out.tolist()
''' % (bg, cross_col)
    return src
