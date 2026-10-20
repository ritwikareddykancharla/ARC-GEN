def build_program(d4, palette):
    green = int(palette[3])
    cyan = int(palette[8])
    src = '''import numpy as np
from collections import deque

GREEN = %d
CYAN = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    mask = (g == GREEN)
    seen = np.zeros((h, w), dtype=bool)
    steps = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                if len(cells) >= 2:
                    for cy, cx in cells:
                        out[cy, cx] = CYAN
    return out.tolist()
''' % (green, cyan)
    return src
