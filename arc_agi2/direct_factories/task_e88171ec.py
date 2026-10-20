def build_program(d4, palette):
    zero = int(palette[0])
    fill = int(palette[8])
    src = '''import numpy as np

ZERO = %d
FILL = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    z = (g == ZERO).astype(int)
    P = np.zeros((H + 1, W + 1), dtype=int)
    P[1:, 1:] = z.cumsum(0).cumsum(1)
    P = P.tolist()
    zl = z.tolist()
    best = None
    bestA = 0
    # The framed box is at least 2x2, so its zero ring is at least 4x4.
    for y0 in range(H):
        Py0 = P[y0]
        for y1 in range(y0 + 3, H):
            Py1 = P[y1 + 1]
            h = y1 - y0 + 1
            for x0 in range(W):
                if not zl[y0][x0]:
                    continue
                for x1 in range(x0 + 3, W):
                    a = h * (x1 - x0 + 1)
                    s = Py1[x1 + 1] - Py0[x1 + 1] - Py1[x0] + Py0[x0]
                    if s != a:
                        break
                    if a > bestA:
                        bestA = a
                        best = (y0, x0, y1, x1)
    out = g.copy()
    if best is not None:
        y0, x0, y1, x1 = best
        out[y0 + 1:y1, x0 + 1:x1] = FILL
    return out.tolist()
''' % (zero, fill)
    return src
