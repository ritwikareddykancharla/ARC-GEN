def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np

BG = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    # Bands that span the whole grid: full lines containing no background cell.
    full_rows = [y for y in range(H) if np.all(g[y, :] != BG)]
    full_cols = [x for x in range(W) if np.all(g[:, x] != BG)]
    if not full_rows or not full_cols:
        return g.tolist()
    row_set = set(full_rows)
    col_set = set(full_cols)
    outside_cols = [x for x in range(W) if x not in col_set]
    outside_rows = [y for y in range(H) if y not in row_set]
    if not outside_cols or not outside_rows:
        return g.tolist()
    # Colour of the band made of full rows, read away from the crossing.
    row_band_colour = int(g[full_rows[0], outside_cols[0]])
    # Colour of the band made of full columns, read away from the crossing.
    col_band_colour = int(g[outside_rows[0], full_cols[0]])
    out = g.copy()
    for y in full_rows:
        for x in full_cols:
            # Swap which band is on top: paint the colour not currently shown.
            if int(g[y, x]) == col_band_colour:
                out[y, x] = row_band_colour
            else:
                out[y, x] = col_band_colour
    return out.tolist()
''' % bg
    return src
