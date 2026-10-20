def build_program(d4, palette):
    start = 1 if d4 >= 4 else 0
    corner = (start + (d4 % 4)) % 4
    # corner: 0=top-left, 1=top-right, 2=bottom-right, 3=bottom-left
    src = '''import numpy as np

CORNER = %d

def _colour_boxes(g):
    info = {}
    H, W = g.shape
    for c in sorted(set(g.ravel().tolist())):
        ys, xs = np.nonzero(g == c)
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        info[c] = (y1 - y0 + 1, x1 - x0 + 1, int(len(ys)))
    return info

def _background(info):
    # Boxes are at most 10x10 while the grid is at least 14x14, so the
    # background is the colour whose bounding span exceeds 10 in some
    # dimension; break ties by pixel count.
    best = None
    bestkey = None
    for c, (h, w, n) in info.items():
        key = (1 if (h > 10 or w > 10) else 0, n, -c)
        if bestkey is None or key > bestkey:
            bestkey = key
            best = c
    return best

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    info = _colour_boxes(g)
    bg = _background(info)
    rects = []
    for c, (h, w, n) in info.items():
        if c == bg:
            continue
        rects.append((h * w, h, w, c))
    if not rects:
        return g.tolist()
    rects.sort(key=lambda r: (-r[0], -r[1], -r[2], r[3]))
    _, H, W, c0 = rects[0]
    canvas = np.full((H, W), c0, dtype=int)
    for _, h, w, c in rects[1:]:
        h = min(h, H)
        w = min(w, W)
        if CORNER == 0:
            canvas[:h, :w] = c
        elif CORNER == 1:
            canvas[:h, W - w:] = c
        elif CORNER == 2:
            canvas[H - h:, W - w:] = c
        else:
            canvas[H - h:, :w] = c
    return canvas.tolist()
''' % corner
    return src
