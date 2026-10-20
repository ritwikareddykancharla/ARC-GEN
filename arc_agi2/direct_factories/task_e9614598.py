def build_program(d4, palette):
    bg = int(palette[0])
    marker = int(palette[1])
    plus = int(palette[3])
    src = '''import numpy as np

BG = __BG__
MARKER = __MARKER__
PLUS = __PLUS__

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    pts = [(int(r), int(c)) for r, c in zip(*np.nonzero(g == MARKER))]
    if len(pts) != 2:
        pts = [(int(r), int(c)) for r, c in zip(*np.nonzero(g != BG))]
    if len(pts) < 2:
        return out.tolist()
    pts.sort()
    (r0, c0), (r1, c1) = pts[0], pts[-1]
    # The two markers share a row or a column; the plus is centred midway.
    sr = r0 + r1
    sc = c0 + c1
    cr = sr // 2
    cc = sc // 2
    for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        r, c = cr + dr, cc + dc
        if 0 <= r < H and 0 <= c < W:
            out[r, c] = PLUS
    return out.tolist()
'''
    src = src.replace('__BG__', repr(bg)).replace('__MARKER__', repr(marker)).replace('__PLUS__', repr(plus))
    return src
