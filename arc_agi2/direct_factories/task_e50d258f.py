def build_program(d4, palette):
    bg = int(palette[0])
    red = int(palette[2])
    template = '''import numpy as np
from collections import deque

BG = __BG__
RED = __RED__

def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
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
    g = np.asarray(grid, dtype=int)
    comps = _components(g != BG)
    if not comps:
        return [row[:] for row in np.asarray(grid).tolist()]
    best = None
    best_key = None
    for cells in comps:
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        cnt = sum(1 for (cy, cx) in cells if g[cy, cx] == RED)
        # deterministic tie-break: larger area, then reading order of top-left
        key = (cnt, len(cells), -y0, -x0)
        if best_key is None or key > best_key:
            best_key = key
            best = (y0, x0, y1, x1)
    y0, x0, y1, x1 = best
    return g[y0:y1 + 1, x0:x1 + 1].tolist()
'''
    return template.replace('__BG__', str(bg)).replace('__RED__', str(red))
