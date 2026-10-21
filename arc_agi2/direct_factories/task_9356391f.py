TEMPLATE = '''import numpy as np

NR = __NR__
NC = __NC__
RR = __RR__
RC = __RC__
BG = __BG__
GRAY = __GRAY__


def _layout(H, W):
    if NR == -1:
        line = [(0, c) for c in range(W)]
        box = (2, H, 0, W)
    elif NR == 1:
        line = [(H - 1, c) for c in range(W)]
        box = (0, H - 2, 0, W)
    elif NC == -1:
        line = [(r, 0) for r in range(H)]
        box = (0, H, 2, W)
    else:
        line = [(r, W - 1) for r in range(H)]
        box = (0, H, 0, W - 2)
    if RR + RC < 0:
        line = line[::-1]
    return line, box


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    line, (r0, r1, c0, c1) = _layout(H, W)
    r1 = max(r1, r0)
    c1 = max(c1, c0)
    legend = [int(g[p]) for p in line]
    while legend and legend[-1] == BG:
        legend.pop()
    if not legend:
        raise ValueError("Missing legend")
    ys, xs = np.nonzero(g[r0:r1, c0:c1] != BG)
    if len(ys) != 1:
        raise ValueError("Expected exactly one seed")
    sy = int(ys[0]) + r0
    sx = int(xs[0]) + c0
    yy, xx = np.indices((H, W))
    dist = np.maximum(np.abs(yy - sy), np.abs(xx - sx))
    region = np.zeros((H, W), dtype=bool)
    region[r0:r1, c0:c1] = True
    for k in range(len(legend) - 1, 0, -1):
        out[region & (dist == k)] = legend[k]
    for k in range(len(legend)):
        if sy-k < r0 or sy+k >= r1 or sx-k < c0 or sx+k >= c1:
            out[line[k]] = GRAY
    return out.tolist()
'''


def build_program(d4, palette):
    nr, nc = -1, 0
    rr, rc = 0, 1
    if d4 >= 4:
        rc = -1
    for _ in range(d4 % 4):
        nr, nc = nc, -nr
        rr, rc = rc, -rr
    src = TEMPLATE
    for key, val in (('__NR__', nr), ('__NC__', nc), ('__RR__', rr), ('__RC__', rc), ('__BG__', int(palette[0])), ('__GRAY__', int(palette[5]))):
        src = src.replace(key, str(val))
    return src
