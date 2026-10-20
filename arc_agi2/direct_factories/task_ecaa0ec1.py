def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[4])
    src = '''import numpy as np

BG = __BG__
MARK = __MARK__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    marks = [(int(p[0]), int(p[1])) for p in np.argwhere(g == MARK)]
    blk = np.argwhere((g != BG) & (g != MARK))
    if len(blk) == 0 or len(marks) == 0:
        return g.tolist()
    y0, x0 = (int(v) for v in blk.min(0))
    y1, x1 = (int(v) for v in blk.max(0))
    cy = (y0 + y1) / 2.0
    cx = (x0 + x1) / 2.0

    def corner(p):
        up = p[0] < cy
        left = p[1] < cx
        # counter-clockwise order in visible coordinates: TL, BL, BR, TR
        return {(True, True): 0, (False, True): 1,
                (False, False): 2, (True, False): 3}[(up, left)]

    def shares_row(p):
        return any(q != p and q[0] == p[0] for q in marks)

    def shares_col(p):
        return any(q != p and q[1] == p[1] for q in marks)

    lcorner = None
    for p in marks:
        if shares_row(p) and shares_col(p):
            lcorner = p
            break
    lone = None
    for p in marks:
        if p != lcorner and not shares_row(p) and not shares_col(p):
            lone = p
            break
    if lone is None:
        hy = (y1 - y0) / 2.0 + 1
        hx = (x1 - x0) / 2.0 + 1
        for p in marks:
            if p != lcorner and abs(p[0] - cy) == hy and abs(p[1] - cx) == hx:
                lone = p
                break
    if lcorner is None or lone is None:
        return g.tolist()

    s = corner(lone)
    t = corner(lcorner)
    k = (t - s) % 4

    out = g.copy()
    for p in marks:
        out[p] = BG
    block = g[y0:y1 + 1, x0:x1 + 1].copy()
    rb = np.rot90(block, k)
    if rb.shape == block.shape:
        out[y0:y1 + 1, x0:x1 + 1] = rb
    pos = {0: (y0 - 1, x0 - 1), 1: (y1 + 1, x0 - 1),
           2: (y1 + 1, x1 + 1), 3: (y0 - 1, x1 + 1)}[t]
    if 0 <= pos[0] < H and 0 <= pos[1] < W:
        out[pos] = MARK
    return out.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__MARK__', str(mark))
