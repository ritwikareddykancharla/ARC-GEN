def build_program(d4, palette):
    bg = int(palette[7])
    mark = int(palette[8])
    src = '''import numpy as np

BG = %d
MARK = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    moves = []
    colours = sorted(set(int(v) for v in g.ravel().tolist()))
    for c in colours:
        if c == BG or c == MARK:
            continue
        ys, xs = np.where(g == c)
        if len(ys) == 0:
            continue
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        dy = 0
        dx = 0
        for cy, cx in ((y0, x0), (y0, x1), (y1, x0), (y1, x1)):
            if g[cy, cx] == MARK:
                dy = -1 if cy == y0 else 1
                dx = -1 if cx == x0 else 1
                break
        moves.append((c, y0, x0, y1, x1, dy, dx))
    # stage 1: erase every object and every marker
    out = np.full((H, W), BG, dtype=int)
    # stage 2: paint each rectangle solid, shifted one cell diagonally toward its marked corner
    for c, y0, x0, y1, x1, dy, dx in moves:
        for y in range(y0 + dy, y1 + dy + 1):
            if y < 0 or y >= H:
                continue
            for x in range(x0 + dx, x1 + dx + 1):
                if 0 <= x < W:
                    out[y, x] = c
    return out.tolist()
''' % (bg, mark)
    return src
