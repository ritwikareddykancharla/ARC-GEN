def build_program(d4, palette):
    bg = int(palette[0])
    mk = int(palette[8])
    src = '''import numpy as np

BG = %d
MARK = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    pos = np.argwhere(g == MARK)
    if len(pos) == 0:
        return out.tolist()
    my, mx = int(pos[0][0]), int(pos[0][1])
    out[my, mx] = BG
    mask = (g != BG) & (g != MARK)
    pts = np.argwhere(mask)
    if len(pts) == 0:
        return out.tolist()
    y0, x0 = [int(v) for v in pts.min(axis=0)]
    y1, x1 = [int(v) for v in pts.max(axis=0)]
    fc = int(g[y0, x0])
    if y1 - y0 >= 2 and x1 - x0 >= 2:
        ic = int(g[y0 + 1, x0 + 1])
    else:
        ic = fc
    # stretch along the axis on which the marker lies outside the box range
    if mx < x0 or mx > x1:
        x0, x1 = min(x0, mx), max(x1, mx)
    if my < y0 or my > y1:
        y0, y1 = min(y0, my), max(y1, my)
    out[y0:y1 + 1, x0:x1 + 1] = fc
    if y1 - y0 >= 2 and x1 - x0 >= 2:
        out[y0 + 1:y1, x0 + 1:x1] = ic
    return out.tolist()
''' % (bg, mk)
    return src
