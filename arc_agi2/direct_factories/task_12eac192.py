def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[3])
    src = '''import numpy as np
from collections import deque

BG = %d
MARK = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    seen = np.zeros((h, w), dtype=bool)
    for y in range(h):
        for x in range(w):
            if seen[y, x] or g[y, x] == BG:
                continue
            col = g[y, x]
            seen[y, x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == col:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            if len(cells) < 3:
                for cy, cx in cells:
                    out[cy, cx] = MARK
    return out.tolist()
''' % (bg, mark)
    return src
