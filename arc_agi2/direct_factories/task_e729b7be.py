def build_program(d4, palette):
    # Colour roles in the visible palette.
    bg = int(palette[7])
    mark = int(palette[8])
    line = int(palette[4])
    # Original shape side is LEFT of the line. Sides are listed in clockwise
    # order: 0=left, 1=top, 2=right, 3=bottom. A row reversal (d4>=4) turns
    # left into right. Each clockwise quarter turn moves left->top->right->bottom.
    base = 2 if d4 >= 4 else 0
    side = (base + (d4 % 4)) % 4
    src = '''import numpy as np

BG = %d
MARK = %d
LINE = %d
SIDE = %d  # 0: shape left of centre column, 1: above centre row, 2: right of centre column, 3: below centre row


def _on_shape_side(y, x, cy, cx):
    if SIDE == 0:
        return x < cx
    if SIDE == 2:
        return x > cx
    if SIDE == 1:
        return y < cy
    return y > cy


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    # The centre is the marker that does not touch any grid edge.
    centre = None
    ys, xs = np.where(g == MARK)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if 0 < y < H - 1 and 0 < x < W - 1:
            centre = (y, x)
            break
    if centre is None:
        return out.tolist()
    cy, cx = centre
    # Point-reflect every shape cell on the shape side about the centre marker,
    # painting only onto background cells and skipping cells that leave the grid.
    for y in range(H):
        for x in range(W):
            v = int(g[y, x])
            if v == BG or v == LINE or v == MARK:
                continue
            if not _on_shape_side(y, x, cy, cx):
                continue
            ny, nx = 2 * cy - y, 2 * cx - x
            if 0 <= ny < H and 0 <= nx < W and out[ny, nx] == BG:
                out[ny, nx] = v
    return out.tolist()
''' % (bg, mark, line, side)
    return src
