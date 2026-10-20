def build_program(d4, palette):
    k = d4 % 4
    flip = d4 >= 4

    def mp(r, c, dr, dc):
        # abstract 2x2 frame: corner coordinates in {0,1}
        h = w = 2
        if flip:
            c = w - 1 - c
            dc = -dc
        for _ in range(k):
            r, c = c, h - 1 - r
            dr, dc = dc, -dr
        return r, c, dr, dc

    sr, sc, _, _ = mp(0, 0, 0, 0)
    dirs = []
    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        _, _, a, b = mp(0, 0, dr, dc)
        dirs.append((a, b))
    line = int(palette[3])

    src = '''import numpy as np

LINE = %d
START_BOTTOM = %s
START_RIGHT = %s
DIRS = %r

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    painted = np.zeros((h, w), bool)
    y = h - 1 if START_BOTTOM else 0
    x = w - 1 if START_RIGHT else 0
    out[y, x] = LINE
    painted[y, x] = True
    d = 0

    def can_move(y, x, d):
        dy, dx = DIRS[d]
        ny, nx = y + dy, x + dx
        if not (0 <= ny < h and 0 <= nx < w) or painted[ny, nx]:
            return False
        my, mx = ny + dy, nx + dx
        if 0 <= my < h and 0 <= mx < w and painted[my, mx]:
            return False
        return True

    while True:
        while can_move(y, x, d):
            dy, dx = DIRS[d]
            y, x = y + dy, x + dx
            out[y, x] = LINE
            painted[y, x] = True
        d = (d + 1) %% 4
        if not can_move(y, x, d):
            break
    return out.tolist()
''' % (line, 'True' if sr == 1 else 'False', 'True' if sc == 1 else 'False', dirs)
    return src
