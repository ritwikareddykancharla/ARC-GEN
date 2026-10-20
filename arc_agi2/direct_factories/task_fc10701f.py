def build_program(d4, palette):
    P = [int(palette[c]) for c in range(10)]
    BG = P[6]
    POST = P[0]
    GATE = P[2]
    MOVER = P[7]
    TARGET = P[9]
    src = '''import numpy as np

BG = %d
POST = %d
GATE = %d
MOVER = %d
TARGET = %d

def _bbox(mask):
    pts = np.argwhere(mask)
    if len(pts) == 0:
        return None
    return (int(pts[:, 0].min()), int(pts[:, 1].min()), int(pts[:, 0].max()), int(pts[:, 1].max()))

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    mm = (g == MOVER)
    tm = (g == TARGET)
    a = _bbox(mm)
    b = _bbox(tm)
    out[mm] = BG
    out[tm] = MOVER
    if a is None or b is None:
        return out.tolist()
    if a[1] == b[1] and a[3] == b[3]:
        # boxes share a column span: corridor runs along rows between them
        x0, x1 = a[1], a[3]
        if a[2] < b[0]:
            lo, hi = a[2], b[0]
        else:
            lo, hi = b[2], a[0]
        for y in range(lo + 1, hi):
            if x0 - 1 >= 0 and x1 + 1 < W and g[y, x0 - 1] == POST and g[y, x1 + 1] == POST:
                out[y, x0:x1 + 1] = GATE
    elif a[0] == b[0] and a[2] == b[2]:
        # boxes share a row span: corridor runs along columns between them
        y0, y1 = a[0], a[2]
        if a[3] < b[1]:
            lo, hi = a[3], b[1]
        else:
            lo, hi = b[3], a[1]
        for x in range(lo + 1, hi):
            if y0 - 1 >= 0 and y1 + 1 < H and g[y0 - 1, x] == POST and g[y1 + 1, x] == POST:
                out[y0:y1 + 1, x] = GATE
    return out.tolist()
''' % (BG, POST, GATE, MOVER, TARGET)
    return src
