def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np

BG = %d

def _find_best(g):
    H, W = g.shape
    best = None
    colours = sorted(set(int(v) for v in g.ravel().tolist()) - {BG})
    for c in colours:
        m = (g == c)
        right = np.zeros((H, W + 1), dtype=int)
        down = np.zeros((H + 1, W), dtype=int)
        for y in range(H):
            for x in range(W - 1, -1, -1):
                if m[y, x]:
                    right[y, x] = right[y, x + 1] + 1
        for x in range(W):
            for y in range(H - 1, -1, -1):
                if m[y, x]:
                    down[y, x] = down[y + 1, x] + 1
        ys, xs = np.nonzero(m)
        for y0, x0 in zip(ys.tolist(), xs.tolist()):
            rmax = int(right[y0, x0])
            dmax = int(down[y0, x0])
            if rmax < 3 or dmax < 3:
                continue
            for w in range(3, rmax + 1):
                x1 = x0 + w - 1
                dr = int(down[y0, x1])
                if dr < 3:
                    continue
                for h in range(3, min(dmax, dr) + 1):
                    y1 = y0 + h - 1
                    if int(right[y1, x0]) >= w:
                        area = (h - 2) * (w - 2)
                        if best is None or area > best[0]:
                            best = (area, y0, x0, y1, x1)
    return best

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    best = _find_best(g)
    if best is None:
        return g.tolist()
    _, y0, x0, y1, x1 = best
    inner = g[y0 + 1:y1, x0 + 1:x1]
    return inner.tolist()
''' % bg
    return src
