def build_program(d4, palette):
    bg = int(palette[0])
    block = int(palette[3])
    src = '''import numpy as np

BG = %d
BLOCK = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    ys, xs = np.where(g == BLOCK)
    if ys.size == 0:
        return g.tolist()
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    rays = []
    for y in range(y0, y1 + 1):
        rays.append((y, x0, 0, -1))
        rays.append((y, x1, 0, 1))
    for x in range(x0, x1 + 1):
        rays.append((y0, x, -1, 0))
        rays.append((y1, x, 1, 0))
    src_grid = g.copy()
    for sy, sx, dy, dx in rays:
        path = []
        y, x = sy + dy, sx + dx
        while 0 <= y < H and 0 <= x < W and src_grid[y, x] == BG:
            path.append((y, x))
            y += dy
            x += dx
        if 0 <= y < H and 0 <= x < W and src_grid[y, x] != BLOCK and src_grid[y, x] != BG:
            c = int(src_grid[y, x])
            for py, px in path:
                g[py, px] = c
    return g.tolist()
''' % (bg, block)
    return src
