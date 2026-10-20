def build_program(d4, palette):
    four = int(palette[4])
    src = '''import numpy as np
from collections import deque

FOUR = __FOUR__

def _comps(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    comps = _comps(g == FOUR)
    if not comps:
        return g.tolist()
    box = max(comps, key=len)
    ys = [c[0] for c in box]
    xs = [c[1] for c in box]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
    C = int(g[cy, cx])
    boxset = set((int(a), int(b)) for a, b in box)
    starts = [(int(y), int(x)) for y, x in zip(*np.where(g == C)) if (int(y), int(x)) != (cy, cx)]
    ends = [(int(y), int(x)) for y, x in zip(*np.where(g == FOUR)) if (int(y), int(x)) not in boxset]
    if starts and ends:
        dy, dx = ends[0][0] - starts[0][0], ends[0][1] - starts[0][1]
    else:
        dy, dx = 0, 0
    out = np.full((H, W), C, dtype=int)
    ny0, nx0, ny1, nx1 = y0 + dy, x0 + dx, y1 + dy, x1 + dx
    for y in range(ny0, ny1 + 1):
        for x in range(nx0, nx1 + 1):
            if 0 <= y < H and 0 <= x < W and (y in (ny0, ny1) or x in (nx0, nx1)):
                out[y, x] = FOUR
    for y, x, sy, sx in ((ny0, nx0, -1, -1), (ny0, nx1, -1, 1), (ny1, nx0, 1, -1), (ny1, nx1, 1, 1)):
        y, x = y + sy, x + sx
        while 0 <= y < H and 0 <= x < W:
            out[y, x] = FOUR
            y += sy
            x += sx
    return out.tolist()
'''
    return src.replace('__FOUR__', str(four))
