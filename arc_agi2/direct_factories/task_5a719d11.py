def build_program(d4, palette):
    div = int(palette[0])
    horiz = (int(d4) % 2 == 0)
    template = '''import numpy as np

DIV = __DIV__
HORIZONTAL_PAIRS = __HORIZ__


def _intervals(lines, size):
    res = []
    start = 0
    for line in list(lines) + [size]:
        if start < line:
            res.append((start, line - 1))
        start = line + 1
    return res


def _panel_info(g, y0, y1, x0, x1):
    p = g[y0:y1 + 1, x0:x1 + 1]
    vals, cnts = np.unique(p, return_counts=True)
    bg = int(vals[int(np.argmax(cnts))])
    return bg, (p != bg)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    dr = [y for y in range(H) if bool((g[y, :] == DIV).all())]
    dc = [x for x in range(W) if bool((g[:, x] == DIV).all())]
    yints = _intervals(dr, H)
    xints = _intervals(dc, W)
    if HORIZONTAL_PAIRS:
        # panels side by side within each band of rows exchange shapes
        groups = [[(y0, y1, x0, x1) for (x0, x1) in xints] for (y0, y1) in yints]
    else:
        # panels stacked within each band of columns exchange shapes
        groups = [[(y0, y1, x0, x1) for (y0, y1) in yints] for (x0, x1) in xints]
    for grp in groups:
        n = len(grp)
        if n < 2:
            continue
        info = []
        for b in grp:
            bg, mask = _panel_info(g, *b)
            info.append((b, bg, mask))
        for i in range(n):
            b, bg, _ = info[i]
            _, pbg, pmask = info[n - 1 - i]
            y0, y1, x0, x1 = b
            region = out[y0:y1 + 1, x0:x1 + 1]
            region[:, :] = bg
            h = min(y1 - y0 + 1, pmask.shape[0])
            w = min(x1 - x0 + 1, pmask.shape[1])
            sub = region[:h, :w]
            sub[pmask[:h, :w]] = pbg
    return out.tolist()
'''
    return template.replace('__DIV__', str(div)).replace('__HORIZ__', 'True' if horiz else 'False')
