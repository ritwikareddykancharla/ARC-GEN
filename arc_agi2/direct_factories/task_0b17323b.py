def build_program(d4, palette):
    d4 = int(d4) % 8
    dy, dx = 1, 1
    if d4 >= 4:
        dx = -dx
    for _ in range(d4 % 4):
        dy, dx = dx, -dy
    bg = int(palette[0])
    seed = int(palette[1])
    ext = int(palette[2])
    src = '''import numpy as np

BG = %d
SEED = %d
EXT = %d
SY = %d
SX = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    cells = [(int(r), int(c)) for r, c in zip(*np.nonzero(g == SEED))]
    if len(cells) < 2:
        cells = [(int(r), int(c)) for r, c in zip(*np.nonzero(g != BG))]
    if len(cells) < 2:
        return out.tolist()
    # order seeds along the visible propagation direction
    cells.sort(key=lambda p: (SY * p[0] + SX * p[1], p[0], p[1]))
    ly, lx = cells[-1]
    py, px = cells[-2]
    sy, sx = ly - py, lx - px
    if sy == 0 and sx == 0:
        return out.tolist()
    y, x = ly + sy, lx + sx
    while 0 <= y < H and 0 <= x < W:
        out[y, x] = EXT
        y += sy
        x += sx
    return out.tolist()
''' % (bg, seed, ext, dy, dx)
    return src
