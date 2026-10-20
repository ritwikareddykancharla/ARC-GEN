def build_program(d4, palette):
    bg = int(palette[0])
    gray = int(palette[5])
    template = '''import numpy as np

BG = __BG__
GRAY = __GRAY__


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    ys, xs = np.nonzero(g == GRAY)
    if ys.size == 0:
        return [[BG]]
    h = int(ys.max() - ys.min() + 1)
    w = int(xs.max() - xs.min() + 1)
    horiz_lines = []
    vert_lines = []
    for c in np.unique(g):
        c = int(c)
        if c == BG or c == GRAY:
            continue
        cy, cx = np.nonzero(g == c)
        span_r = int(cy.max() - cy.min() + 1)
        span_c = int(cx.max() - cx.min() + 1)
        if span_r == 1 and span_c > 1:
            horiz_lines.append((int(cy.min()), c))
        elif span_c == 1 and span_r > 1:
            vert_lines.append((int(cx.min()), c))
        elif span_c > span_r:
            horiz_lines.append((int(round(float(cy.mean()))), c))
        else:
            vert_lines.append((int(round(float(cx.mean()))), c))
    out = np.full((h, w), BG, dtype=int)
    if len(horiz_lines) >= len(vert_lines):
        horiz_lines.sort()
        for i, (pos, c) in enumerate(horiz_lines):
            if i < h:
                out[i, :] = c
    else:
        vert_lines.sort()
        for i, (pos, c) in enumerate(vert_lines):
            if i < w:
                out[:, i] = c
    return out.tolist()
'''
    return template.replace('__BG__', str(bg)).replace('__GRAY__', str(gray))
