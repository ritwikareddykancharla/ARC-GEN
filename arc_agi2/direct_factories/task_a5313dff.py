def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[1])
    wall = int(palette[2])
    src = '''import numpy as np
from collections import deque

BG = %d
FILL = %d
WALL = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    seen = np.zeros((H, W), dtype=bool)
    for sy in range(H):
        for sx in range(W):
            if g[sy, sx] != BG or seen[sy, sx]:
                continue
            seen[sy, sx] = True
            q = deque([(sy, sx)])
            cells = []
            open_region = False
            while q:
                y, x = q.popleft()
                cells.append((y, x))
                if y == 0 or x == 0 or y == H - 1 or x == W - 1:
                    open_region = True
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == BG:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            if not open_region:
                for y, x in cells:
                    out[y, x] = FILL
    return out.tolist()
''' % (bg, fill, wall)
    return src
