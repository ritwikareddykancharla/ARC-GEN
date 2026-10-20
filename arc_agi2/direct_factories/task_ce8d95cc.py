def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np

BG = %d

def _compress(g):
    H, W = g.shape
    line_rows = [y for y in range(H) if np.all(g[y, :] != BG)]
    line_cols = [x for x in range(W) if np.all(g[:, x] != BG)]
    bg_rows = [y for y in range(H) if y not in line_rows]
    bg_cols = [x for x in range(W) if x not in line_cols]
    if bg_rows:
        brow = bg_rows[0]
        rows = [brow]
        for r in line_rows:
            rows += [r, brow]
    else:
        rows = list(line_rows)
    if bg_cols:
        bcol = bg_cols[0]
        cols = [bcol]
        for c in line_cols:
            cols += [c, bcol]
    else:
        cols = list(line_cols)
    stage = g[rows, :]
    out = stage[:, cols]
    return out

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    out = _compress(g)
    return [[int(v) for v in row] for row in out.tolist()]
''' % bg
    return src
