def build_program(d4, palette):
    bg = int(palette[0])
    # Image of the original +column (growth) direction under the D4 transform.
    dr, dc = 0, 1
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        # clockwise rotation maps direction (dr, dc) -> (dc, -dr)
        dr, dc = dc, -dr
    gr, gc = dr, dc
    src = '''import numpy as np

BG = %d
GROW_R = %d
GROW_C = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    ys, xs = np.nonzero(g != BG)
    if ys.size == 0:
        return out.tolist()
    y0 = int(ys.min())
    x0 = int(xs.min())
    block = g[y0:y0 + 2, x0:x0 + 2].copy()
    if block.shape != (2, 2):
        return out.tolist()
    horizontal = GROW_C != 0
    positive = (GROW_R + GROW_C) > 0
    if horizontal:
        L = W
        a0 = x0
        b0 = y0
    else:
        L = H
        a0 = y0
        b0 = x0
    s = 2
    while True:
        if positive:
            start = a0 + 2 * (s - 1)
            if start >= L:
                break
        else:
            end = a0 + 1 - 2 * (s - 1)
            if end < 0:
                break
            start = end - 2 * s + 1
        cross = b0 - s + 1
        big = np.kron(block, np.ones((s, s), dtype=int))
        if horizontal:
            top, left = cross, start
        else:
            top, left = start, cross
        r0 = max(top, 0)
        r1 = min(top + 2 * s, H)
        c0 = max(left, 0)
        c1 = min(left + 2 * s, W)
        if r0 < r1 and c0 < c1:
            out[r0:r1, c0:c1] = big[r0 - top:r1 - top, c0 - left:c1 - left]
        s *= 2
    return out.tolist()
''' % (bg, gr, gc)
    return src
