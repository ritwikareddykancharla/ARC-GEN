def build_program(d4, palette):
    bg = int(palette[0])
    seed = int(palette[1])
    src = '''import numpy as np

BG = %d
SEED = %d

def solve(demonstrations, grid):
    inp = np.array(grid, dtype=int)
    out = inp.copy()
    H, W = inp.shape
    ys, xs = np.where(inp == SEED)
    for y, x in zip(ys.tolist(), xs.tolist()):
        y0 = max(0, y - 1)
        y1 = min(H - 1, y + 1)
        x0 = max(0, x - 1)
        x1 = min(W - 1, x + 1)
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                if out[yy, xx] == BG:
                    out[yy, xx] = SEED
    return out.tolist()
''' % (bg, seed)
    return src
