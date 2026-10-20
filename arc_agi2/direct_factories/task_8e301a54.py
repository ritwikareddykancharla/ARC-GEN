def build_program(d4, palette):
    k = d4 % 4
    dr, dc = 1, 0
    for _ in range(k):
        dr, dc = dc, -dr
    bg = int(palette[7])
    src = '''import numpy as np
from collections import deque

BG = %d
DR = %d
DC = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for sy, sx in steps:
                        ny, nx = cy + sy, cx + sx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = np.full((H, W), BG, dtype=int)
    colours = sorted(set(int(v) for v in g.ravel().tolist()) - {BG})
    for col in colours:
        for cells in _components(g == col):
            s = len(cells)
            for y, x in cells:
                ny, nx = y + DR * s, x + DC * s
                if 0 <= ny < H and 0 <= nx < W:
                    out[ny, nx] = col
    return out.tolist()
''' % (bg, dr, dc)
    return src
