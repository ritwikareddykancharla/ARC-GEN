def build_program(d4, palette):
    fill = int(palette[0])
    src = '''import numpy as np
from collections import Counter

FILL = %d

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    h, w = g.shape
    counts = Counter(g.ravel().tolist())
    best = max(counts.values())
    # The generator guarantees a unique most frequent colour; break any tie by first occurrence in row-major order.
    dom = None
    for v in g.ravel().tolist():
        if counts[v] == best:
            dom = v
            break
    out = np.full((h * h, w * w), FILL, dtype=int)
    for y in range(h):
        for x in range(w):
            if g[y, x] == dom:
                out[y * h:(y + 1) * h, x * w:(x + 1) * w] = g
    return out.tolist()
''' % fill
    return src
