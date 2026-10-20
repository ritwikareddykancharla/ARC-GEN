def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np

BG = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = np.full((3 * h, 3 * w), BG, dtype=int)
    rows = [r for r in range(h) if len(set(g[r, :].tolist())) == 1]
    cols = [c for c in range(w) if len(set(g[:, c].tolist())) == 1]
    for R in range(3):
        for C in range(3):
            if R in rows or C in cols:
                if R < h and C < w:
                    out[R * h:(R + 1) * h, C * w:(C + 1) * w] = g
    return out.tolist()
''' % bg
    return src
