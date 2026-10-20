def build_program(d4, palette):
    red = int(palette[2])
    bg = int(palette[0])
    src = '''import numpy as np

RED = %d
BG = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    cells = [(y, x) for y in range(h) for x in range(w) if g[y, x] != BG]
    if not cells:
        return g.tolist()
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    y0, x0 = min(ys), min(xs)
    y1, x1 = max(ys), max(xs)
    others = [int(g[y, x]) for (y, x) in cells if g[y, x] != RED]
    C = others[0] if others else RED
    out = g.copy()
    reds = [(y, x) for (y, x) in cells if g[y, x] == RED]
    for (y, x) in reds:
        out[y, x] = C
    for (y, x) in reds:
        dy = -1 if y == y0 else 1
        dx = -1 if x == x0 else 1
        for sy, sx in ((y, x), (y, x + dx), (y + dy, x)):
            cy, cx = sy, sx
            while 0 <= cy < h and 0 <= cx < w:
                out[cy, cx] = C
                cy += dy
                cx += dx
    return out.tolist()
''' % (red, bg)
    return src
