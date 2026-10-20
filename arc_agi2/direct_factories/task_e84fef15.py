def build_program(d4, palette):
    div = int(palette[3])
    mark = int(palette[1])
    bg = int(palette[8])
    src = '''import numpy as np
from collections import Counter

DIV = __DIV__
MARK = __MARK__
BG = __BG__


def _spans(full, n):
    out = []
    start = None
    for i in range(n):
        if full[i]:
            if start is not None:
                out.append((start, i - 1))
                start = None
        elif start is None:
            start = i
    if start is not None:
        out.append((start, n - 1))
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    # Divider lines are complete rows / columns of the divider colour.
    row_full = [bool((g[r] == DIV).all()) for r in range(H)]
    col_full = [bool((g[:, c] == DIV).all()) for c in range(W)]
    ys = _spans(row_full, H)
    xs = _spans(col_full, W)
    boxes = [(y0, y1, x0, x1) for (y0, y1) in ys for (x0, x1) in xs]
    if not boxes:
        return g.tolist()
    shapes = Counter((y1 - y0 + 1, x1 - x0 + 1) for (y0, y1, x0, x1) in boxes)
    shape = max(shapes.items(), key=lambda kv: (kv[1], kv[0][0] * kv[0][1]))[0]
    tiles = np.array([g[y0:y1 + 1, x0:x1 + 1] for (y0, y1, x0, x1) in boxes
                      if (y1 - y0 + 1, x1 - x0 + 1) == shape])
    h, w = shape
    motif = np.full((h, w), BG, dtype=int)
    for y in range(h):
        for x in range(w):
            cnt = Counter(tiles[:, y, x].tolist())
            best = max(cnt.values())
            motif[y, x] = min(v for v, k in cnt.items() if k == best)
    out = motif.copy()
    diff = (tiles != motif[None, :, :]).any(axis=0)
    out[diff] = MARK
    return out.tolist()
'''
    src = src.replace('__DIV__', repr(div)).replace('__MARK__', repr(mark)).replace('__BG__', repr(bg))
    return src
