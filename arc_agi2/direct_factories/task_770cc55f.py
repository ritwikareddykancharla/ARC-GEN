def build_program(d4, palette):
    k = int(d4) % 4
    # Bars originally live on the first/last ROW. A horizontal flip (d4>=4) keeps them on rows;
    # an odd number of clockwise quarter-turns moves them onto the first/last COLUMN.
    bars_on_columns = (k % 2 == 1)
    bg = int(palette[0])
    div = int(palette[2])
    fill = int(palette[4])
    src = '''import numpy as np

BG = __BG__
DIV = __DIV__
FILL = __FILL__
BARS_ON_COLUMNS = __AXIS__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    if not BARS_ON_COLUMNS:
        # Bars on the top and bottom rows, divider is a full row of DIV.
        divider = None
        for r in range(1, H - 1):
            if np.all(g[r, :] == DIV):
                divider = r
                break
        if divider is None:
            divider = H // 2
        first = g[0, :] != BG
        last = g[H - 1, :] != BG
        overlap = [c for c in range(W) if first[c] and last[c]]
        if int(first.sum()) >= int(last.sum()):
            span = range(1, divider)
        else:
            span = range(divider + 1, H - 1)
        for c in overlap:
            for r in span:
                out[r, c] = FILL
    else:
        # Bars on the left and right columns, divider is a full column of DIV.
        divider = None
        for c in range(1, W - 1):
            if np.all(g[:, c] == DIV):
                divider = c
                break
        if divider is None:
            divider = W // 2
        first = g[:, 0] != BG
        last = g[:, W - 1] != BG
        overlap = [r for r in range(H) if first[r] and last[r]]
        if int(first.sum()) >= int(last.sum()):
            span = range(1, divider)
        else:
            span = range(divider + 1, W - 1)
        for r in overlap:
            for c in span:
                out[r, c] = FILL
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg))
    src = src.replace('__DIV__', str(div))
    src = src.replace('__FILL__', str(fill))
    src = src.replace('__AXIS__', 'True' if bars_on_columns else 'False')
    return src
