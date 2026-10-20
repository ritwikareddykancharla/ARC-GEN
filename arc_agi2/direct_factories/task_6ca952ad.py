def build_program(d4, palette):
    k = int(d4) % 4
    # Original gravity pulls toward the last row. Reversing each row (d4>=4) does not change
    # the vertical direction. Each clockwise turn maps original 'down' to:
    # k=0 down, k=1 left, k=2 up, k=3 right.
    dirs = {0: (1, 0), 1: (0, -1), 2: (-1, 0), 3: (0, 1)}
    dr, dc = dirs[k]
    bg = int(palette[7])
    template = '''import numpy as np
from collections import deque

BG = @BG@
DR = @DR@
DC = @DC@
MAX_STAY = 3

def _components(g):
    H, W = g.shape
    seen = np.zeros((H, W), dtype=bool)
    comps = []
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
                for ddy, ddx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + ddy, cx + ddx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == col:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            comps.append((cells, col))
    return comps

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    moves = []
    for cells, col in _components(g):
        if len(cells) <= MAX_STAY:
            continue
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        if DR == 1:
            sy, sx = H - 1 - max(ys), 0
        elif DR == -1:
            sy, sx = -min(ys), 0
        elif DC == 1:
            sy, sx = 0, W - 1 - max(xs)
        else:
            sy, sx = 0, -min(xs)
        moves.append((cells, col, sy, sx))
    for cells, col, sy, sx in moves:
        for y, x in cells:
            out[y, x] = BG
    for cells, col, sy, sx in moves:
        for y, x in cells:
            out[y + sy, x + sx] = col
    return out.tolist()
'''
    return template.replace('@BG@', str(bg)).replace('@DR@', str(dr)).replace('@DC@', str(dc))
