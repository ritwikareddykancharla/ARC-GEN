def build_program(d4, palette):
    k = d4 % 4
    # unit vector of original +x (column) direction, tracked through the D4 transform
    dr, dc = 0, 1
    if d4 >= 4:
        dr, dc = dr, -dc
    for _ in range(k):
        dr, dc = dc, -dr
    if dr == 0:
        horizontal = True
        positive = dc > 0
    else:
        horizontal = False
        positive = dr > 0
    bg = int(palette[0])
    gray = int(palette[5])
    src = '''import numpy as np

BG = %d
GRAY = %d
HORIZONTAL = %r
POSITIVE = %r


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    if HORIZONTAL:
        L = W
        nlines = H
    else:
        L = H
        nlines = W
    mid = L // 2  # centre index measured from the seed-A end (original left end)
    for t in range(nlines):
        if HORIZONTAL:
            line = g[t, :]
        else:
            line = g[:, t]
        if POSITIVE:
            a_end, b_end = 0, L - 1
        else:
            a_end, b_end = L - 1, 0
        a = int(line[a_end])
        b = int(line[b_end])
        if a == BG or b == BG:
            continue
        for j in range(L):
            i = j if POSITIVE else L - 1 - j
            if i < mid:
                v = a
            elif i > mid:
                v = b
            else:
                v = GRAY
            if HORIZONTAL:
                out[t, j] = v
            else:
                out[j, t] = v
    return out.tolist()
''' % (bg, gray, horizontal, positive)
    return src
