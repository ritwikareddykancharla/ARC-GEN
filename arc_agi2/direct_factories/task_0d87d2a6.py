def build_program(d4, palette):
    bg = int(palette[0])
    line = int(palette[1])
    red = int(palette[2])
    src = '''import numpy as np
from collections import deque

BG = %d
LINE = %d
RED = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps = []
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
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    # Opposite edge markers define full-span lines (both orientations).
    rows = [r for r in range(h) if g[r, 0] == LINE and g[r, w - 1] == LINE]
    cols = [c for c in range(w) if g[0, c] == LINE and g[h - 1, c] == LINE]
    linemask = np.zeros((h, w), dtype=bool)
    for r in rows:
        linemask[r, :] = True
    for c in cols:
        linemask[:, c] = True
    # A red box is activated if a line crosses it or runs directly alongside it.
    for cells in _components(g == RED):
        hit = False
        for y, x in cells:
            if linemask[y, x]:
                hit = True
                break
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < h and 0 <= xx < w and linemask[yy, xx]:
                    hit = True
                    break
            if hit:
                break
        if hit:
            for y, x in cells:
                out[y, x] = LINE
    out[linemask] = LINE
    return out.tolist()
''' % (bg, line, red)
    return src
