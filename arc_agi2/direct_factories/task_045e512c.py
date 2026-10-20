PROGRAM = '''import numpy as np
from collections import Counter

BG_HINT = __BG__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    if g.ndim != 2 or g.size == 0:
        return [list(r) for r in grid]
    H, W = g.shape
    cnt = Counter(g.ravel().tolist())
    top = max(cnt.values())
    if cnt.get(BG_HINT, 0) == top:
        bg = BG_HINT
    else:
        bg = cnt.most_common(1)[0][0]
    # Template = largest 8-connected single-colour component (fragments have <=3 cells).
    seen = np.zeros((H, W), dtype=bool)
    best = None
    for y in range(H):
        for x in range(W):
            if seen[y, x] or int(g[y, x]) == bg:
                continue
            col = int(g[y, x])
            seen[y, x] = True
            stack = [(y, x)]
            comp = []
            while stack:
                cy, cx = stack.pop()
                comp.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and int(g[ny, nx]) == col:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            ys = [p[0] for p in comp]
            xs = [p[1] for p in comp]
            area = (max(ys) - min(ys) + 1) * (max(xs) - min(xs) + 1)
            key = (len(comp), area)
            if best is None or key > best[0]:
                best = (key, col, comp)
    if best is None:
        return g.tolist()
    _, tc, comp = best
    y0 = min(p[0] for p in comp)
    x0 = min(p[1] for p in comp)
    y1 = max(p[0] for p in comp)
    x1 = max(p[1] for p in comp)
    h = y1 - y0 + 1
    w = x1 - x0 + 1
    shape = [(y - y0, x - x0) for (y, x) in comp]
    py, px = h + 1, w + 1
    tset = set(comp)
    out = g.copy()

    def paint(iy, ix, col):
        oy = y0 + iy * py
        ox = x0 + ix * px
        hit = False
        for dy, dx in shape:
            yy, xx = oy + dy, ox + dx
            if 0 <= yy < H and 0 <= xx < W:
                out[yy, xx] = col
                hit = True
        return hit

    def sign(v):
        return (v > 0) - (v < 0)

    groups = []
    gset = set()
    for y in range(H):
        for x in range(W):
            v = int(g[y, x])
            if v == bg or (y, x) in tset:
                continue
            iy = (y - y0) // py
            ix = (x - x0) // px
            k = (v, iy, ix)
            if k not in gset:
                gset.add(k)
                groups.append(k)
    for (v, iy, ix) in groups:
        sy, sx = sign(iy), sign(ix)
        if sy == 0 and sx == 0:
            continue
        paint(iy, ix, v)
        k = 1
        while k < 200 and paint(iy + k * sy, ix + k * sx, v):
            k += 1
    return out.tolist()
'''


def build_program(d4, palette):
    bg_hint = int(palette[0])
    return PROGRAM.replace('__BG__', str(bg_hint))
