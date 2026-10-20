def build_program(d4, palette):
    p5 = int(palette[5])
    p9 = int(palette[9])
    p6 = int(palette[6])
    src = '''import numpy as np

BLOCK = %d
MARK = %d
BEACON = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    # The block is the 3x3 patch of BLOCK colour with MARK at its centre.
    ys, xs = np.where((g == BLOCK) | (g == MARK))
    bys, bxs = np.where(g == BLOCK)
    if len(bys) == 0:
        return g.tolist()
    r0, r1 = int(bys.min()), int(bys.max())
    c0, c1 = int(bxs.min()), int(bxs.max())
    # Find the MARK cell inside the block.
    my, mx = None, None
    ms = np.argwhere(g == MARK)
    for (y, x) in ms:
        if r0 <= y <= r1 and c0 <= x <= c1:
            my, mx = int(y), int(x)
            break
    if my is None:
        my, mx = (r0 + r1) // 2, (c0 + c1) // 2
    bs = np.argwhere(g == BEACON)
    if len(bs) == 0:
        return g.tolist()
    by, bx = int(bs[0][0]), int(bs[0][1])
    # Step component: -1 / 0 / +1 by whether beacon is before, within, after the block span.
    dy = -1 if by < r0 else (1 if by > r1 else 0)
    dx = -1 if bx < c0 else (1 if bx > c1 else 0)
    ty, tx = my + dy, mx + dx
    if (dy, dx) != (0, 0) and 0 <= ty < H and 0 <= tx < W:
        g[my, mx] = BLOCK
        g[ty, tx] = MARK
    g[by, bx] = MARK
    return g.tolist()
''' % (p5, p9, p6)
    return src
