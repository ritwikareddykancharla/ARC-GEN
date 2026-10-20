def build_program(d4, palette):
    line_c = int(palette[0])
    new_c = int(palette[2])
    src = '''import numpy as np

LINE = %d
NEW = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    # A row or column made entirely of the line colour becomes the new colour.
    # Rows and columns are handled the same way, so D4 only swaps which lines are rows.
    full_rows = [y for y in range(H) if np.all(g[y, :] == LINE)]
    full_cols = [x for x in range(W) if np.all(g[:, x] == LINE)]
    for y in full_rows:
        out[y, :] = NEW
    for x in full_cols:
        out[:, x] = NEW
    return out.tolist()
''' % (line_c, new_c)
    return src
