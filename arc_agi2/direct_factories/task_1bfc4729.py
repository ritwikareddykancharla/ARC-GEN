def build_program(d4, palette):
    bg = int(palette[0])
    k = int(d4) % 4
    # Canonical split is by rows (pixels stacked vertically). A reflection of each row keeps
    # rows as rows; an odd number of clockwise quarter-turns turns rows into columns.
    axis = 1 if k in (1, 3) else 0
    src = '''import numpy as np

BG = %d
AXIS = %d  # 0: territories are row bands (top/bottom); 1: territories are column bands (left/right)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = np.full((H, W), BG, dtype=int)
    ys, xs = np.nonzero(g != BG)
    pts = [(int(y), int(x), int(g[y, x])) for y, x in zip(ys, xs)]
    if not pts:
        return out.tolist()
    n = H if AXIS == 0 else W
    half = n // 2
    key = (lambda p: p[0]) if AXIS == 0 else (lambda p: p[1])
    lo = min(pts, key=lambda p: (key(p), p[1] if AXIS == 0 else p[0]))
    hi = max(pts, key=lambda p: (key(p), p[1] if AXIS == 0 else p[0]))
    bands = [(lo, list(range(0, half)), 0), (hi, list(range(n - half, n)), n - 1)]
    for (py, px, col), lines, edge in bands:
        if AXIS == 0:
            for i in lines:
                out[i, 0] = col
                out[i, W - 1] = col
            out[edge, :] = col
            out[py, :] = col
        else:
            for j in lines:
                out[0, j] = col
                out[H - 1, j] = col
            out[:, edge] = col
            out[:, px] = col
    return out.tolist()
''' % (bg, axis)
    return src
