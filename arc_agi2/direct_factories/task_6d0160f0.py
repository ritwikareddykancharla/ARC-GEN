def build_program(d4, palette):
    bg = int(palette[0])
    div = int(palette[5])
    mark = int(palette[4])
    template = '''import numpy as np

BG = __BG__
DIV = __DIV__
MARK = __MARK__


def _spans(cuts, n):
    edges = [-1] + sorted(cuts) + [n]
    out = []
    for a, b in zip(edges, edges[1:]):
        if b - a > 1:
            out.append((a + 1, b - 1))
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    # Full-length divider lines of the divider colour, in visible coordinates.
    rcuts = [y for y in range(H) if (g[y] == DIV).all()]
    ccuts = [x for x in range(W) if (g[:, x] == DIV).all()]
    ys = _spans(rcuts, H)
    xs = _spans(ccuts, W)
    out = g.copy()
    src = None
    for (y0, y1) in ys:
        for (x0, x1) in xs:
            sub = g[y0:y1 + 1, x0:x1 + 1]
            hits = np.argwhere(sub == MARK)
            if src is None and len(hits):
                src = (y0, y1, x0, x1, int(hits[0][0]), int(hits[0][1]))
            out[y0:y1 + 1, x0:x1 + 1] = BG
    if src is None:
        return out.tolist()
    y0, y1, x0, x1, ly, lx = src
    # The marker's local (row, col) inside its panel indexes the destination panel.
    if ly < len(ys) and lx < len(xs):
        dy0, dy1 = ys[ly]
        dx0, dx1 = xs[lx]
        content = g[y0:y1 + 1, x0:x1 + 1]
        h = min(content.shape[0], dy1 - dy0 + 1)
        w = min(content.shape[1], dx1 - dx0 + 1)
        out[dy0:dy0 + h, dx0:dx0 + w] = content[:h, :w]
    return out.tolist()
'''
    return (template.replace('__BG__', str(bg))
                    .replace('__DIV__', str(div))
                    .replace('__MARK__', str(mark)))
