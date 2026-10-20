def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np

BG = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    others = [int(v) for v in g.flatten() if int(v) != BG]
    out = np.full((h * h, w * w), BG, dtype=int)
    if not others:
        return out.tolist()
    c = others[0]
    mask = (g == BG)
    tile = np.where(mask, c, BG)
    for i in range(h):
        for j in range(w):
            if mask[i, j]:
                out[i * h:(i + 1) * h, j * w:(j + 1) * w] = tile
    return out.tolist()
''' % bg
    return src
