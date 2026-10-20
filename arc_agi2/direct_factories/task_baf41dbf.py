def build_program(d4, palette):
    bg = int(palette[0])
    fc = int(palette[3])
    mc = int(palette[6])
    src = '''import numpy as np

BG = %d
FC = %d
MC = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    ys, xs = np.nonzero(g == FC)
    if len(ys) == 0:
        return out.tolist()
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    # internal dividers: full-span lines of frame colour strictly inside the box
    rows = [y for y in range(y0 + 1, y1) if bool(np.all(g[y, x0:x1 + 1] == FC))]
    cols = [x for x in range(x0 + 1, x1) if bool(np.all(g[y0:y1 + 1, x] == FC))]
    # markers: the marker colour (fallback: any non-background, non-frame pixel)
    mys, mxs = np.nonzero(g == MC)
    if len(mys) == 0:
        mys, mxs = np.nonzero((g != BG) & (g != FC))
    todo = [(int(a), int(b)) for a, b in zip(mys, mxs)]
    # erase old frame
    out[g == FC] = BG
    # assign markers to sides in repeated passes; a marker belongs to the side
    # whose span (rows for left/right, columns for top/bottom) contains it
    changed = True
    while changed and todo:
        changed = False
        for m in list(todo):
            my, mx = m
            if y0 <= my <= y1 and mx < x0:
                x0 = mx + 1
            elif y0 <= my <= y1 and mx > x1:
                x1 = mx - 1
            elif x0 <= mx <= x1 and my < y0:
                y0 = my + 1
            elif x0 <= mx <= x1 and my > y1:
                y1 = my - 1
            else:
                continue
            todo.remove(m)
            changed = True
    y0 = max(0, y0); x0 = max(0, x0)
    y1 = min(H - 1, y1); x1 = min(W - 1, x1)
    out[y0, x0:x1 + 1] = FC
    out[y1, x0:x1 + 1] = FC
    out[y0:y1 + 1, x0] = FC
    out[y0:y1 + 1, x1] = FC
    for y in rows:
        if y0 <= y <= y1:
            out[y, x0:x1 + 1] = FC
    for x in cols:
        if x0 <= x <= x1:
            out[y0:y1 + 1, x] = FC
    return out.tolist()
''' % (bg, fc, mc)
    return src
