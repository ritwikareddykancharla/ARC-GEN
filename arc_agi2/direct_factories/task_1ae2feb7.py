_COMMON = '''
import numpy as np

BG = __BG__


def _runs_outward(cells):
    # cells listed from the divider outward; group maximal same-colour runs,
    # skipping background gaps (e.g. the optional one-cell offset).
    runs = []
    i = 0
    n = len(cells)
    while i < n:
        c = cells[i]
        if c == BG:
            i += 1
            continue
        j = i
        while j < n and cells[j] == c:
            j += 1
        runs.append((c, j - i))
        i = j
    return runs
'''

_VERT = '''

def solve(demonstrations, grid):
    # Divider is a full-height column; runs lie along rows; stamping is horizontal.
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    best = None
    for x in range(W):
        col = g[:, x]
        vals = col[col != BG]
        if vals.size == 0:
            continue
        n = int(np.bincount(vals, minlength=10).max())
        if best is None or n > best[0]:
            best = (n, x)
    if best is None:
        return out.tolist()
    dx = best[1]
    before = int((g[:, :dx] != BG).sum())
    after = int((g[:, dx + 1:] != BG).sum())
    step = 1 if before >= after else -1
    for y in range(H):
        cells = []
        x = dx - step
        while 0 <= x < W:
            cells.append(int(g[y, x]))
            x -= step
        runs = _runs_outward(cells)
        for c, n in reversed(runs):
            d = 1
            while 0 <= dx + step * d < W:
                out[y, dx + step * d] = c
                d += n
    return out.tolist()
'''

_HORIZ = '''

def solve(demonstrations, grid):
    # Divider is a full-width row; runs lie along columns; stamping is vertical.
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    best = None
    for y in range(H):
        row = g[y, :]
        vals = row[row != BG]
        if vals.size == 0:
            continue
        n = int(np.bincount(vals, minlength=10).max())
        if best is None or n > best[0]:
            best = (n, y)
    if best is None:
        return out.tolist()
    dy = best[1]
    before = int((g[:dy, :] != BG).sum())
    after = int((g[dy + 1:, :] != BG).sum())
    step = 1 if before >= after else -1
    for x in range(W):
        cells = []
        y = dy - step
        while 0 <= y < H:
            cells.append(int(g[y, x]))
            y -= step
        runs = _runs_outward(cells)
        for c, n in reversed(runs):
            d = 1
            while 0 <= dy + step * d < H:
                out[dy + step * d, x] = c
                d += n
    return out.tolist()
'''


def build_program(d4, palette):
    bg = int(palette[0])
    body = _HORIZ if (int(d4) % 4) in (1, 3) else _VERT
    return _COMMON.replace('__BG__', str(bg)) + body
