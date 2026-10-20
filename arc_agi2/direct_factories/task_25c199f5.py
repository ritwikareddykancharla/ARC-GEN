def build_program(d4, palette):
    g = (1, 0)   # original gravity: downward (increasing row)
    o = (0, 1)   # original panel order: left to right (increasing column)
    def flip(v):
        return (v[0], -v[1])
    def rot(v):
        # clockwise rotation (r,c)->(c,H-1-r) maps direction (dr,dc)->(dc,-dr)
        return (v[1], -v[0])
    if d4 >= 4:
        g = flip(g)
        o = flip(o)
    for _ in range(d4 % 4):
        g = rot(g)
        o = rot(o)
    bg = int(palette[7])
    sep = int(palette[6])
    src = '''import numpy as np

BG = %d
SEP = %d
GR, GC = %d, %d
OR, OC = %d, %d


def _spans(cuts, n):
    edges = [-1] + sorted(cuts) + [n]
    out = []
    for i in range(len(edges) - 1):
        a, b = edges[i], edges[i + 1]
        if b - a > 1:
            out.append((a + 1, b - 1))
    return out


def solve(demonstrations, grid):
    a = np.array(grid, dtype=int)
    H, W = a.shape
    boxes = []
    if OC != 0:
        # panels sit side by side, separated by full columns of SEP
        cuts = [x for x in range(W) if (a[:, x] == SEP).all()]
        for x0, x1 in _spans(cuts, W):
            boxes.append((0, x0, H - 1, x1))
        if OC < 0:
            boxes = boxes[::-1]
    else:
        # panels stacked vertically, separated by full rows of SEP
        cuts = [y for y in range(H) if (a[y, :] == SEP).all()]
        for y0, y1 in _spans(cuts, H):
            boxes.append((y0, 0, y1, W - 1))
        if OR < 0:
            boxes = boxes[::-1]
    if not boxes:
        return a.tolist()
    h = boxes[0][2] - boxes[0][0] + 1
    w = boxes[0][3] - boxes[0][1] + 1
    canvas = np.full((h, w), BG, dtype=int)
    # smallest projection onto gravity over the canvas = entry edge
    target = min(0, GR * (h - 1)) + min(0, GC * (w - 1))
    for (y0, x0, y1, x1) in boxes:
        sub = a[y0:y1 + 1, x0:x1 + 1]
        cells = []
        for y in range(min(h, sub.shape[0])):
            for x in range(min(w, sub.shape[1])):
                v = int(sub[y, x])
                if v != BG and v != SEP:
                    cells.append((y, x, v))
        if not cells:
            continue
        m = min(y * GR + x * GC for y, x, _ in cells)
        s = target - m
        cells = [(y + GR * s, x + GC * s, v) for y, x, v in cells]
        d = 0
        while True:
            nd = d + 1
            ok = True
            for y, x, _ in cells:
                ny, nx = y + GR * nd, x + GC * nd
                if not (0 <= ny < h and 0 <= nx < w) or canvas[ny, nx] != BG:
                    ok = False
                    break
            if ok:
                d = nd
            else:
                break
        for y, x, v in cells:
            ny, nx = y + GR * d, x + GC * d
            if 0 <= ny < h and 0 <= nx < w:
                canvas[ny, nx] = v
    return canvas.tolist()
''' % (bg, sep, g[0], g[1], o[0], o[1])
    return src
