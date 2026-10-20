def build_program(d4, palette):
    head = int(palette[2])
    shaft = int(palette[6])
    field = int(palette[7])
    src = '''import numpy as np

HEAD = %d
SHAFT = %d
FIELD = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    ys, xs = np.where(g == HEAD)
    if len(ys) == 0:
        return out.tolist()
    hy, hx = int(ys[0]), int(xs[0])
    # The arrow fires from the adjacent shaft cell toward the head.
    cands = []
    for ddy in (-1, 0, 1):
        for ddx in (-1, 0, 1):
            if ddy == 0 and ddx == 0:
                continue
            ny, nx = hy + ddy, hx + ddx
            if 0 <= ny < H and 0 <= nx < W and g[ny, nx] == SHAFT:
                cands.append((ddy, ddx))
    if not cands:
        return out.tolist()
    if len(cands) > 1:
        # Prefer the neighbour that continues a collinear shaft run.
        best = None
        for ddy, ddx in cands:
            n = 0
            y, x = hy + ddy, hx + ddx
            while 0 <= y < H and 0 <= x < W and g[y, x] == SHAFT:
                n += 1
                y += ddy
                x += ddx
            if best is None or n > best[0]:
                best = (n, ddy, ddx)
        ddy, ddx = best[1], best[2]
    else:
        ddy, ddx = cands[0]
    dy, dx = -ddy, -ddx
    y, x = hy + dy, hx + dx
    while 0 <= y < H and 0 <= x < W and g[y, x] == FIELD:
        y += dy
        x += dx
    if 0 <= y < H and 0 <= x < W:
        out[y, x] = FIELD
    return out.tolist()
''' % (head, shaft, field)
    return src
