def build_program(d4, palette):
    gray = int(palette[5])
    zero = int(palette[0])
    src = '''import numpy as np

GRAY = %d
ZERO = %d

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    # The other colour C is the single non-gray colour in the query input.
    vals, counts = np.unique(g, return_counts=True)
    others = [(int(v), int(n)) for v, n in zip(vals, counts) if int(v) != GRAY]
    if others:
        # Constructor guarantees exactly one; if ever more, take the most frequent (lowest value on ties).
        others.sort(key=lambda t: (-t[1], t[0]))
        c = others[0][0]
    else:
        c = ZERO
    out = np.full(g.shape, ZERO, dtype=int)
    out[g == GRAY] = c
    return out.tolist()
''' % (gray, zero)
    return src
