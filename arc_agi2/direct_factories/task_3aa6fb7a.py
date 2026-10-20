def build_program(d4, palette):
    bg = int(palette[0])
    fg = int(palette[8])
    fill = int(palette[1])
    src = '''
import numpy as np
from collections import deque

BG = %d
FG = %d
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
    out = g.copy()
    for cells in _components(g == FG):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if g[y, x] == BG:
                    out[y, x] = FILL
    return out.tolist()
''' % (bg, fg, fill)
    return src
