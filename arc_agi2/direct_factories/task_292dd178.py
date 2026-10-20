def build_program(d4, palette):
    box_c = int(palette[1])
    fill_c = int(palette[2])
    src = '''import numpy as np
from collections import Counter, deque

BOX = %d
FILL = %d

def _components(mask):
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
    cnt = Counter(int(v) for v in g.ravel() if int(v) != BOX)
    if not cnt:
        return g.tolist()
    bg = cnt.most_common(1)[0][0]
    out = g.copy()
    for cells in _components(g == BOX):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        for y in range(y0 + 1, y1):
            for x in range(x0 + 1, x1):
                if g[y, x] == bg:
                    out[y, x] = FILL
        gaps = []
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (y in (y0, y1) or x in (x0, x1)) and g[y, x] == bg:
                    gaps.append((y, x))
        for gy, gx in gaps:
            if gy == y0:
                d = (-1, 0)
            elif gy == y1:
                d = (1, 0)
            elif gx == x0:
                d = (0, -1)
            else:
                d = (0, 1)
            y, x = gy, gx
            while 0 <= y < H and 0 <= x < W:
                if g[y, x] == bg:
                    out[y, x] = FILL
                y += d[0]
                x += d[1]
    return out.tolist()
''' % (box_c, fill_c)
    return src
