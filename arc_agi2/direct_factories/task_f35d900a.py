def build_program(d4, palette):
    bg = int(palette[0])
    gray = int(palette[5])
    template = '''import numpy as np

BG = __BG__
GRAY = __GRAY__


def _dot_gap(out, cells):
    n = len(cells)
    for i, (y, x) in enumerate(cells):
        if min(i, n - 1 - i) % 2 == 0:
            out[y, x] = GRAY


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    ys, xs = np.nonzero(g != BG)
    pts = [(int(y), int(x)) for y, x in zip(ys, xs)]
    if not pts:
        return out.tolist()
    cols = sorted(set(int(g[y, x]) for y, x in pts))
    if len(cols) == 2:
        other = {cols[0]: cols[1], cols[1]: cols[0]}
    else:
        other = {c: c for c in cols}
    # Step 1: 3x3 ring of the partner colour around each corner pixel (clipped)
    for y, x in pts:
        c = other[int(g[y, x])]
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if (dy or dx) and 0 <= y + dy < H and 0 <= x + dx < W:
                    out[y + dy, x + dx] = c
    # Step 2: alternating gray dots in the background gap between neighbouring rings
    rows = sorted(set(p[0] for p in pts))
    for y in rows:
        line = sorted(p[1] for p in pts if p[0] == y)
        for a, b in zip(line, line[1:]):
            _dot_gap(out, [(y, x) for x in range(a + 2, b - 1)])
    colsx = sorted(set(p[1] for p in pts))
    for x in colsx:
        line = sorted(p[0] for p in pts if p[1] == x)
        for a, b in zip(line, line[1:]):
            _dot_gap(out, [(y, x) for y in range(a + 2, b - 1)])
    return out.tolist()
'''
    return template.replace('__BG__', str(bg)).replace('__GRAY__', str(gray))
