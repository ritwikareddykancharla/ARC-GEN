def build_program(d4, palette):
    bg = int(palette[0])
    pivot = int(palette[5])
    src = '''import numpy as np

BG = %d
PIVOT = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    piv = np.argwhere(g == PIVOT)
    if len(piv) == 0:
        return out.tolist()
    py, px = int(piv[0][0]), int(piv[0][1])
    cells = [(int(y), int(x), int(g[y, x])) for y, x in np.argwhere((g != BG) & (g != PIVOT))]
    for y, x, c in cells:
        out[y, x] = BG
    for y, x, c in cells:
        ny, nx = 2 * py - y, 2 * px - x
        if 0 <= ny < H and 0 <= nx < W:
            out[ny, nx] = c
    out[py, px] = PIVOT
    return out.tolist()
''' % (bg, pivot)
    return src
