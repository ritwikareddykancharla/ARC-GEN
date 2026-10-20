def build_program(d4, palette):
    P = [int(palette[i]) for i in range(10)]
    header = (
        "import numpy as np\n"
        "BG = " + str(P[0]) + "\n"
        "Y = " + str(P[4]) + "\n"
        "G = " + str(P[3]) + "\n"
        "L = " + str(P[8]) + "\n"
        "R = " + str(P[2]) + "\n"
    )
    body = '''

def _lane(lane, line, low):
    # lane: writable 1-D view of one visible row or column crossing the divider.
    # low=True: shapes lie at indices < line, the wall side is > line.
    n = lane.shape[0]
    if low:
        near = lane[:line]
        idx = np.where(near == Y)[0]
        if idx.size == 0:
            return
        close = int(idx.max())
        far_cnt = int((lane[line + 1:] == R).sum())
        near[near == Y] = G
        lane[close + 1:line] = Y
        lane[line + 1:] = L
        if far_cnt:
            lane[n - far_cnt:] = R
    else:
        near = lane[line + 1:]
        idx = np.where(near == Y)[0]
        if idx.size == 0:
            return
        close = line + 1 + int(idx.min())
        far_cnt = int((lane[:line] == R).sum())
        near[near == Y] = G
        lane[line + 1:close] = Y
        lane[:line] = L
        if far_cnt:
            lane[:far_cnt] = R


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    if g.ndim != 2 or g.size == 0:
        return [list(r) for r in grid]
    H, W = g.shape
    full_rows = [y for y in range(H) if (g[y, :] == L).all()]
    full_cols = [x for x in range(W) if (g[:, x] == L).all()]
    ys, xs = np.where(g == Y)
    if ys.size == 0:
        return g.tolist()
    if full_rows and not (full_cols and len(full_rows) > 1):
        line = full_rows[0]
        low = bool(ys.mean() < line)
        for x in range(W):
            _lane(g[:, x], line, low)
    elif full_cols:
        line = full_cols[0]
        low = bool(xs.mean() < line)
        for y in range(H):
            _lane(g[y, :], line, low)
    return g.tolist()
'''
    return header + body
