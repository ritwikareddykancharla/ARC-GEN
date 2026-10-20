def build_program(d4, palette):
    bg = int(palette[0])
    ring = int(palette[1])
    seed = int(palette[5])
    src = '''import numpy as np

BG = %d
RING = %d
SEED = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    ys, xs = np.nonzero(g != BG)
    for y, x in zip(ys.tolist(), xs.tolist()):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                yy = y + dy
                xx = x + dx
                if 0 <= yy < H and 0 <= xx < W and g[yy, xx] == BG:
                    out[yy, xx] = RING
    return out.tolist()
''' % (bg, ring, seed)
    return src
