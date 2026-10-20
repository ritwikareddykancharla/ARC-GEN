def build_program(d4, palette):
    dy, dx = 0, 1
    if d4 >= 4:
        dy, dx = 0, -1
    for _ in range(d4 % 4):
        dy, dx = dx, -dy
    bg = int(palette[0])
    src = '''import numpy as np
from collections import deque

DY = %d
DX = %d
BG = %d

def _components(g):
    H, W = g.shape
    seen = np.zeros((H, W), bool)
    out = []
    for y in range(H):
        for x in range(W):
            if g[y, x] == BG or seen[y, x]:
                continue
            col = int(g[y, x])
            q = deque([(y, x)])
            seen[y, x] = True
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for sy, sx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + sy, cx + sx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == col:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            out.append((sorted(cells), col))
    return out

def _lead(cells):
    return max(y * DY + x * DX for y, x in cells)

def _perp(cells):
    return min(y * DX - x * DY for y, x in cells)

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    objs = _components(g)
    objs.sort(key=lambda o: (-_lead(o[0]), _perp(o[0])))
    canvas = np.full_like(g, BG)

    def inb(y, x):
        return 0 <= y < H and 0 <= x < W

    placed = []
    for cells, col in objs:
        cells = list(cells)
        while all(inb(y + DY, x + DX) and canvas[y + DY, x + DX] == BG for y, x in cells):
            cells = [(y + DY, x + DX) for y, x in cells]
        for y, x in cells:
            canvas[y, x] = col
        placed.append([cells, col])

    moved = True
    guard = 0
    while moved and guard < 10000:
        guard += 1
        moved = False
        for p in placed:
            cells, col = p
            own = set(cells)
            while all(inb(y + DY, x + DX) and ((y + DY, x + DX) in own or canvas[y + DY, x + DX] == BG) for y, x in cells):
                for y, x in cells:
                    canvas[y, x] = BG
                cells = [(y + DY, x + DX) for y, x in cells]
                own = set(cells)
                for y, x in cells:
                    canvas[y, x] = col
                moved = True
            p[0] = cells
    return canvas.tolist()
''' % (dy, dx, bg)
    return src
