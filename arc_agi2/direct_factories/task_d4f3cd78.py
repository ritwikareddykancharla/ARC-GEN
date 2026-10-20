def build_program(d4, palette):
    bg = int(palette[0])
    frame = int(palette[5])
    fill = int(palette[8])
    src = '''import numpy as np
from collections import Counter

BG = %d
FRAME = %d
FILL = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                stack = [(y, x)]
                seen[y, x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    bg = BG
    if not np.any(g == bg):
        bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    fr = FRAME
    if not np.any(g == fr):
        comps = _components(g != bg)
        if not comps:
            return g.tolist()
        best = max(comps, key=len)
        fr = int(g[best[0]])
        ys = [c[0] for c in best]
        xs = [c[1] for c in best]
    else:
        ys, xs = np.nonzero(g == fr)
        ys = ys.tolist()
        xs = xs.tolist()
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    # 1. fill interior background cells
    for y in range(y0 + 1, y1):
        for x in range(x0 + 1, x1):
            if g[y, x] == bg:
                g[y, x] = FILL
    # 2. find the gap on the frame border
    gap = None
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (y in (y0, y1) or x in (x0, x1)) and g[y, x] == bg:
                gap = (y, x)
                break
        if gap is not None:
            break
    if gap is None:
        return g.tolist()
    gy, gx = gap
    if gy == y0:
        d = (-1, 0)
    elif gy == y1:
        d = (1, 0)
    elif gx == x0:
        d = (0, -1)
    else:
        d = (0, 1)
    # 3. gap plus outward ray to the grid edge
    y, x = gy, gx
    while 0 <= y < H and 0 <= x < W:
        if g[y, x] == bg:
            g[y, x] = FILL
        y += d[0]
        x += d[1]
    return g.tolist()
''' % (bg, frame, fill)
    return src
