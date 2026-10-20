def build_program(d4, palette):
    k = d4 % 4
    dr, dc = 1, 0
    for _ in range(k):
        dr, dc = dc, -dr
    bg = int(palette[0])
    src = '''import numpy as np

DR = %d
DC = %d
BG = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    if DR != 0:
        n, m = W, H
    else:
        n, m = H, W

    def cell(depth, t):
        if DR == 1:
            return (H - 1 - depth, t)
        if DR == -1:
            return (depth, t)
        if DC == 1:
            return (t, W - 1 - depth)
        return (t, depth)

    if m < 2:
        return g.tolist()
    cap = [t for t in range(n) if g[cell(1, t)] != BG]
    if not cap:
        return g.tolist()
    t0, t1 = min(cap), max(cap)
    inner = int(g[cell(0, t0)])
    depth, t = 2, t0 - 1
    while depth < m and t >= 0:
        g[cell(depth, t)] = inner
        depth += 1
        t -= 1
    depth, t = 2, t1 + 1
    while depth < m and t < n:
        g[cell(depth, t)] = inner
        depth += 1
        t += 1
    return g.tolist()
''' % (dr, dc, bg)
    return src
