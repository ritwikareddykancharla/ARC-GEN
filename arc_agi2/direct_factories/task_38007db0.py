def build_program(d4, palette):
    horizontal = (int(d4) % 2 == 0)
    src = '''import numpy as np
from collections import Counter

HORIZONTAL_BANDS = %s

def _spans(cuts, n):
    edges = [-1] + sorted(cuts) + [n]
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        if b - a > 1:
            out.append((a + 1, b - 1))
    return out

def _odd_index(crops):
    keys = [c.tobytes() + bytes(str(c.shape), 'ascii') for c in crops]
    cnt = Counter(keys)
    return min(range(len(crops)), key=lambda i: (cnt[keys[i]], i))

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    frame = int(g[0, 0])
    div_rows = [y for y in range(H) if (g[y, :] == frame).all()]
    div_cols = [x for x in range(W) if (g[:, x] == frame).all()]
    ys = _spans(div_rows, H)
    xs = _spans(div_cols, W)
    if not ys or not xs:
        return g.tolist()
    if HORIZONTAL_BANDS:
        # bands are rows of panels; output keeps full height, one panel wide
        pw = xs[0][1] - xs[0][0] + 1
        out = np.full((H, pw + 2), frame, dtype=int)
        for (y0, y1) in ys:
            crops = [g[y0:y1 + 1, x0:x1 + 1].copy() for (x0, x1) in xs]
            k = _odd_index(crops)
            c = crops[k]
            out[y0:y1 + 1, 1:1 + c.shape[1]] = c
    else:
        # bands are columns of panels; output keeps full width, one panel tall
        ph = ys[0][1] - ys[0][0] + 1
        out = np.full((ph + 2, W), frame, dtype=int)
        for (x0, x1) in xs:
            crops = [g[y0:y1 + 1, x0:x1 + 1].copy() for (y0, y1) in ys]
            k = _odd_index(crops)
            c = crops[k]
            out[1:1 + c.shape[0], x0:x1 + 1] = c
    return out.tolist()
''' % ('True' if horizontal else 'False')
    return src
