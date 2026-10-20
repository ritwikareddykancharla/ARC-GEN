def build_program(d4, palette):
    bg = int(palette[0])
    start = 1 if d4 >= 4 else 0
    corner = (start + (d4 % 4)) % 4
    # corner: 0=top-left, 1=top-right, 2=bottom-right, 3=bottom-left
    src = '''import numpy as np

BG = %d
CORNER = %d

def _half_dims(demonstrations, ys, xs):
    shapes = set()
    for d in demonstrations or []:
        try:
            o = np.asarray(d["output"])
            if o.ndim == 2:
                shapes.add((int(o.shape[0]), int(o.shape[1])))
        except Exception:
            pass
    if len(shapes) == 1:
        return shapes.pop()
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    return (int((y1 - y0 + 2) // 2), int((x1 - x0 + 2) // 2))

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    H, W = g.shape
    ys, xs = np.nonzero(g != BG)
    if len(ys) == 0:
        return [[BG]]
    h, w = _half_dims(demonstrations, ys, xs)
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    # The pattern is symmetric in both axes, so the occupied bounding box is
    # centred on the full (2h x 2w) box even if outer lines are empty.
    top = (y0 + y1 + 1) // 2 - h
    left = (x0 + x1 + 1) // 2 - w
    r0 = top + (h if CORNER in (2, 3) else 0)
    c0 = left + (w if CORNER in (1, 2) else 0)
    out = []
    for r in range(r0, r0 + h):
        row = []
        for c in range(c0, c0 + w):
            if 0 <= r < H and 0 <= c < W:
                row.append(int(g[r, c]))
            else:
                row.append(BG)
        out.append(row)
    return out
''' % (bg, corner)
    return src
