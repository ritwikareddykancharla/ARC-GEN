def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[8])
    template = '''import numpy as np

BG = __BG__
FILL = __FILL__


def _boxes(g):
    out = []
    for c in sorted(set(g.ravel().tolist())):
        if c == BG or c == FILL:
            continue
        ys, xs = np.nonzero(g == c)
        if len(ys) == 0:
            continue
        out.append((int(len(ys)), int(c), int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max())))
    out.sort(key=lambda b: (-b[0], b[1]))
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    boxes = _boxes(g)
    if len(boxes) < 2:
        return out.tolist()
    a = boxes[0][2:]
    b = boxes[1][2:]
    # a, b = (y0, x0, y1, x1)
    cols_disjoint = a[3] < b[1] or b[3] < a[1]
    rows_disjoint = a[2] < b[0] or b[2] < a[0]
    if cols_disjoint and not rows_disjoint:
        left, right = (a, b) if a[3] < b[1] else (b, a)
        x0, x1 = left[3] + 1, right[1] - 1
        y0, y1 = max(a[0], b[0]) + 1, min(a[2], b[2]) - 1
    elif rows_disjoint and not cols_disjoint:
        top, bot = (a, b) if a[2] < b[0] else (b, a)
        y0, y1 = top[2] + 1, bot[0] - 1
        x0, x1 = max(a[1], b[1]) + 1, min(a[3], b[3]) - 1
    else:
        return out.tolist()
    if y0 <= y1 and x0 <= x1:
        region = out[y0:y1 + 1, x0:x1 + 1]
        region[region == BG] = FILL
    return out.tolist()
'''
    return template.replace('__BG__', repr(bg)).replace('__FILL__', repr(fill))
