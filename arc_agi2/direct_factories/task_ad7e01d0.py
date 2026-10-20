def build_program(d4, palette):
    marker = int(palette[5])
    fill = int(palette[0])
    src = '''import numpy as np

MARKER = %d
FILL = %d

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    h, w = g.shape
    out = np.full((h * h, w * w), FILL, dtype=int)
    for i in range(h):
        for j in range(w):
            if g[i, j] == MARKER:
                out[i * h:(i + 1) * h, j * w:(j + 1) * w] = g
    return out.tolist()
''' % (marker, fill)
    return src
