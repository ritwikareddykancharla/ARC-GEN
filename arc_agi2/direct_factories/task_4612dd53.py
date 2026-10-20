def build_program(d4, palette):
    BG = int(palette[0])
    LINE = int(palette[1])
    FILL = int(palette[2])
    src = '''import numpy as np

BG = %d
LINE = %d
FILL = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    ys, xs = np.nonzero(g == LINE)
    if len(ys) == 0:
        return out.tolist()
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())

    def fill_row(y):
        for x in range(x0, x1 + 1):
            if out[y, x] == BG:
                out[y, x] = FILL

    def fill_col(x):
        for y in range(y0, y1 + 1):
            if out[y, x] == BG:
                out[y, x] = FILL

    # outer frame = bounding box border lines
    fill_row(y0)
    fill_row(y1)
    fill_col(x0)
    fill_col(x1)

    # interior cut-line: at most one full inner row or column
    row_counts = {}
    for y in range(y0 + 1, y1):
        row_counts[y] = int(np.sum(g[y, x0 + 1:x1] == LINE))
    col_counts = {}
    for x in range(x0 + 1, x1):
        col_counts[x] = int(np.sum(g[y0 + 1:y1, x] == LINE))
    rmax = max(row_counts.values()) if row_counts else 0
    cmax = max(col_counts.values()) if col_counts else 0
    if rmax == 0 and cmax == 0:
        return out.tolist()
    if rmax >= cmax:
        for y, c in row_counts.items():
            if c == rmax:
                fill_row(y)
                break
    else:
        for x, c in col_counts.items():
            if c == cmax:
                fill_col(x)
                break
    return out.tolist()
''' % (BG, LINE, FILL)
    return src
