def build_program(d4, palette):
    bg = int(palette[0])
    seed = int(palette[5])
    fill = int(palette[1])
    src = '''import numpy as np

BG = %d
SEED = %d
FILL = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = np.full((H, W), BG, dtype=int)
    ys, xs = np.nonzero(g == SEED)
    for y, x in zip(ys.tolist(), xs.tolist()):
        out[max(0, y - 1):min(H, y + 2), max(0, x - 1):min(W, x + 2)] = FILL
    return out.tolist()
''' % (bg, seed, fill)
    return src
