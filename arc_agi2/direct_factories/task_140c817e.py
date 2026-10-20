def build_program(d4, palette):
    c1 = int(palette[1])
    c2 = int(palette[2])
    c3 = int(palette[3])
    src = '''import numpy as np
from collections import Counter

LINE = %d
CENTER = %d
DIAG = %d

def _background(g):
    return int(Counter(g.ravel().tolist()).most_common(1)[0][0])

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = _background(g)
    seeds = [(y, x) for y in range(H) for x in range(W) if g[y, x] != bg]
    out = g.copy()
    # each seed shoots a full row and a full column of the line colour
    for y, x in seeds:
        out[y, :] = LINE
        out[:, x] = LINE
    # four diagonal neighbours (clipped at the border) get the marker colour
    for y, x in seeds:
        for dy in (-1, 1):
            for dx in (-1, 1):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W:
                    out[yy, xx] = DIAG
    # seed cell itself becomes the centre colour
    for y, x in seeds:
        out[y, x] = CENTER
    return out.tolist()
''' % (c1, c2, c3)
    return src
