def build_program(d4, palette):
    bg = int(palette[7])
    frame = int(palette[3])
    src = '''import numpy as np
from collections import deque

BG = %d
FRAME = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
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
    g = np.array(grid, dtype=int)
    out = g.copy()
    ys, xs = np.where(g == FRAME)
    if len(ys) == 0:
        return out.tolist()
    # The legend box is the bounding box of the frame colour, wherever the
    # corner sits in the visible grid.
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    legend = set(int(v) for v in g[y0:y1 + 1, x0:x1 + 1].ravel()) - {FRAME, BG}
    for comp in _components(g != BG):
        if any(y0 <= y <= y1 and x0 <= x <= x1 for y, x in comp):
            continue
        cols = set(int(g[y, x]) for y, x in comp)
        if legend <= cols:
            for y, x in comp:
                out[y, x] = BG
    return out.tolist()
''' % (bg, frame)
    return src
