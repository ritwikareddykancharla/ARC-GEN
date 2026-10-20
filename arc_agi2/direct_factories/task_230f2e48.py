def build_program(d4, palette):
    k = int(d4) % 4
    flip = int(d4) >= 4

    def mapv(dr, dc):
        if flip:
            dc = -dc
        for _ in range(k):
            dr, dc = dc, -dr
        return dr, dc

    # Original generator tie (odd-size centre, never produced in practice):
    # a centred knee sends its new tail left (0,-1) or up (-1,0).
    # Map those original tie directions into visible coordinates.
    tie_row = 1
    tie_col = 1
    for v in ((0, -1), (-1, 0)):
        m = mapv(*v)
        if m[0] == 0:
            tie_col = m[1]
        else:
            tie_row = m[0]

    bg = int(palette[7])
    anchor = int(palette[5])
    body = int(palette[2])
    knee = int(palette[0])

    src = '''import numpy as np

BG = %d
ANCHOR = %d
BODY = %d
KNEE = %d
TIE_ROW = %d
TIE_COL = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    jobs = []
    ys, xs = np.where(g == KNEE)
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        tail = None
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            y, x = y0 + dy, x0 + dx
            n = 0
            while 0 <= y < H and 0 <= x < W and g[y, x] == BODY:
                n += 1
                y += dy
                x += dx
            anchored = 0 <= y < H and 0 <= x < W and g[y, x] == ANCHOR
            if anchored:
                continue
            if n > 0 and (tail is None or n > tail[2]):
                tail = (dy, dx, n)
        if tail is None:
            continue
        dy, dx, n = tail
        if dy != 0:
            # vertical line: tail swings horizontally toward the roomier side
            c2 = 2 * x0
            if c2 < W - 1:
                s = 1
            elif c2 > W - 1:
                s = -1
            else:
                s = TIE_COL
            nd = (0, s)
        else:
            # horizontal line: tail swings vertically toward the roomier side
            r2 = 2 * y0
            if r2 < H - 1:
                s = 1
            elif r2 > H - 1:
                s = -1
            else:
                s = TIE_ROW
            nd = (s, 0)
        jobs.append((y0, x0, dy, dx, n, nd))
    for y0, x0, dy, dx, n, nd in jobs:
        for t in range(1, n + 1):
            out[y0 + dy * t, x0 + dx * t] = BG
    for y0, x0, dy, dx, n, nd in jobs:
        for t in range(1, n + 1):
            yy, xx = y0 + nd[0] * t, x0 + nd[1] * t
            if 0 <= yy < H and 0 <= xx < W:
                out[yy, xx] = BODY
    return out.tolist()
''' % (bg, anchor, body, knee, tie_row, tie_col)
    return src
