def build_program(d4, palette):
    d4 = int(d4) % 8
    bg = int(palette[0])

    def tf(v):
        dy, dx = v
        if d4 >= 4:
            dx = -dx
        for _ in range(d4 % 4):
            dy, dx = dx, -dy
        return dy, dx

    col_sign = 1
    row_sign = 1
    for v in [(0, 1), (1, 0)]:
        ty, tx = tf(v)
        if ty == 0:
            col_sign = 1 if tx > 0 else -1
        else:
            row_sign = 1 if ty > 0 else -1

    prog = '''import numpy as np

BG = %d
COL_SIGN = %d
ROW_SIGN = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    ys, xs = np.nonzero(g != BG)
    seeds = [(int(y), int(x), int(g[y, x])) for y, x in zip(ys, xs)]
    if not seeds:
        return out.tolist()
    tb = sum(1 for y, x, c in seeds if y == 0 or y == H - 1)
    lr = sum(1 for y, x, c in seeds if x == 0 or x == W - 1)
    vertical = tb >= lr
    if vertical:
        sign = COL_SIGN
        limit = W
        lines = [(x, c) for y, x, c in seeds]
    else:
        sign = ROW_SIGN
        limit = H
        lines = [(y, c) for y, x, c in seeds]
    lines.sort(key=lambda t: t[0] * sign)

    def draw(p, col):
        if vertical:
            out[:, p] = col
        else:
            out[p, :] = col

    for p, c in lines:
        draw(p, c)
    if len(lines) >= 2:
        p1, c1 = lines[0]
        p2, c2 = lines[1]
        step = p2 - p1
        cols = [c1, c2]
        k = 2
        p = p2 + step
        while step != 0 and 0 <= p < limit:
            draw(p, cols[k %% 2])
            k += 1
            p += step
    return out.tolist()
''' % (bg, col_sign, row_sign)
    return prog
