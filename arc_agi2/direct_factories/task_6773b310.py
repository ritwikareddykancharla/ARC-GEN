def build_program(d4, palette):
    bg = int(palette[0])
    div = int(palette[8])
    pink = int(palette[6])
    mark = int(palette[1])
    src = '''import numpy as np

BG = %d
DIV = %d
PINK = %d
MARK = %d

def _spans(cuts, n):
    edges = [-1] + sorted(cuts) + [n]
    out = []
    for k in range(len(edges) - 1):
        a, b = edges[k], edges[k + 1]
        if b - a > 1:
            out.append((a + 1, b - 1))
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    rcuts = [y for y in range(H) if (g[y, :] == DIV).all()]
    ccuts = [x for x in range(W) if (g[:, x] == DIV).all()]
    ys = _spans(rcuts, H)
    xs = _spans(ccuts, W)
    if not ys or not xs:
        return [[BG]]
    out = np.full((len(ys), len(xs)), BG, dtype=int)
    for i, (y0, y1) in enumerate(ys):
        for j, (x0, x1) in enumerate(xs):
            p = g[y0:y1 + 1, x0:x1 + 1]
            cnt = int(np.sum((p != BG) & (p != DIV)))
            if cnt == 2:
                out[i, j] = MARK
    return out.tolist()
''' % (bg, div, pink, mark)
    return src
