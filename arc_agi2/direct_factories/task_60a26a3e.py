def build_program(d4, palette):
    bg = int(palette[0])
    plus = int(palette[2])
    line = int(palette[1])
    src = '''import numpy as np

BG = %d
PLUS = %d
LINE = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    centres = []
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if g[y, x] == BG and g[y - 1, x] == PLUS and g[y + 1, x] == PLUS and g[y, x - 1] == PLUS and g[y, x + 1] == PLUS:
                centres.append((y, x))
    rows = {}
    cols = {}
    for y, x in centres:
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)
    out = g.copy()
    for y in sorted(rows):
        xs = sorted(rows[y])
        for a, b in zip(xs, xs[1:]):
            for x in range(a + 2, b - 1):
                if g[y, x] == BG:
                    out[y, x] = LINE
    for x in sorted(cols):
        ys = sorted(cols[x])
        for a, b in zip(ys, ys[1:]):
            for y in range(a + 2, b - 1):
                if g[y, x] == BG:
                    out[y, x] = LINE
    return out.tolist()
''' % (bg, plus, line)
    return src
