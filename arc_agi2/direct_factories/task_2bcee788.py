def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[2])
    fill = int(palette[3])
    src = '''import numpy as np

BG = %d
MARK = %d
FILL = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = np.full((H, W), FILL, dtype=int)
    shape_mask = (g != BG) & (g != MARK)
    ys, xs = np.nonzero(shape_mask)
    if len(ys) == 0:
        return out.tolist()
    vals, counts = np.unique(g[shape_mask], return_counts=True)
    col = int(vals[int(np.argmax(counts))])
    out[shape_mask] = g[shape_mask]
    my, mx = np.nonzero(g == MARK)
    if len(my) == 0:
        return out.tolist()
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    # The marker lies strictly outside one edge of the shape bounding box;
    # that edge is the mirror line. Pick the side directly in visible coords.
    if mx.min() > x1:
        f = lambda y, x: (y, 2 * x1 + 1 - x)
    elif mx.max() < x0:
        f = lambda y, x: (y, 2 * x0 - 1 - x)
    elif my.min() > y1:
        f = lambda y, x: (2 * y1 + 1 - y, x)
    elif my.max() < y0:
        f = lambda y, x: (2 * y0 - 1 - y, x)
    else:
        # Fallback: choose the side whose edge is nearest to the marker centroid.
        cy, cx = float(my.mean()), float(mx.mean())
        d = {
            'r': cx - x1, 'l': x0 - cx, 'b': cy - y1, 'a': y0 - cy,
        }
        side = max(d, key=lambda k: d[k])
        if side == 'r':
            f = lambda y, x: (y, 2 * x1 + 1 - x)
        elif side == 'l':
            f = lambda y, x: (y, 2 * x0 - 1 - x)
        elif side == 'b':
            f = lambda y, x: (2 * y1 + 1 - y, x)
        else:
            f = lambda y, x: (2 * y0 - 1 - y, x)
    for y, x in zip(ys.tolist(), xs.tolist()):
        ny, nx = f(y, x)
        if 0 <= ny < H and 0 <= nx < W:
            out[ny, nx] = int(g[y, x])
    return out.tolist()
''' % (bg, mark, fill)
    return src
