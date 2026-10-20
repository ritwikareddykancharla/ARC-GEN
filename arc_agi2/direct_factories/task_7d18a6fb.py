def build_program(d4, palette):
    d4 = int(d4) % 8
    top, left = True, True
    if d4 >= 4:
        left = not left
    for _ in range(d4 % 4):
        top, left = left, (not top)
    bg = int(palette[0])
    board = int(palette[1])
    src = '''import numpy as np

BG = %d
BOARD = %d
ANCHOR_TOP = %s
ANCHOR_LEFT = %s

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    ys, xs = np.where(g == BOARD)
    if ys.size == 0:
        return [[BG]]
    y0, x0 = int(ys.min()), int(xs.min())
    h, w = int(ys.max()) - y0 + 1, int(xs.max()) - x0 + 1
    out = np.full((h, w), BG, dtype=int)
    inside = np.zeros(g.shape, bool)
    inside[y0:y0 + h, x0:x0 + w] = True
    for qy in (0, 4):
        for qx in (0, 4):
            my, mx = y0 + qy + 1, x0 + qx + 1
            if my >= g.shape[0] or mx >= g.shape[1]:
                continue
            c = int(g[my, mx])
            if c == BOARD or c == BG:
                continue
            mask = (g == c) & ~inside
            if not mask.any():
                continue
            cy, cx = np.where(mask)
            ymin, ymax = int(cy.min()), int(cy.max())
            xmin, xmax = int(cx.min()), int(cx.max())
            for yy, xx in zip(cy.tolist(), cx.tolist()):
                ty = qy + (yy - ymin) if ANCHOR_TOP else qy + 2 - (ymax - yy)
                tx = qx + (xx - xmin) if ANCHOR_LEFT else qx + 2 - (xmax - xx)
                if 0 <= ty < h and 0 <= tx < w:
                    out[ty, tx] = c
    return out.tolist()
''' % (bg, board, 'True' if top else 'False', 'True' if left else 'False')
    return src
