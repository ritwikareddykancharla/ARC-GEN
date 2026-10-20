def build_program(d4, palette):
    fill = int(palette[0])
    src = '''import numpy as np

FILL = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    vals, counts = np.unique(g, return_counts=True)
    best = int(counts.max())
    tied = set(int(v) for v, c in zip(vals, counts) if int(c) == best)
    key = None
    for r in range(h):
        for c in range(w):
            if int(g[r, c]) in tied:
                key = int(g[r, c])
                break
        if key is not None:
            break
    out = np.full((h * h, w * w), FILL, dtype=int)
    for i in range(h):
        for j in range(w):
            if int(g[i, j]) == key:
                out[i * h:(i + 1) * h, j * w:(j + 1) * w] = g
    return out.tolist()
''' % fill
    return src
