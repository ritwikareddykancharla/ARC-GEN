TEMPLATE = '''import numpy as np
from collections import deque

BG = @BG@
GREY = @GREY@
AXIS = @AXIS@
SIGN = @SIGN@
LUR = @LUR@
LUC = @LUC@


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    legend_cells = [(r, c) for r in range(H) for c in range(W)
                    if g[r, c] != BG and g[r, c] != GREY]
    legend_cells.sort(key=lambda rc: rc[0] * LUR + rc[1] * LUC)
    legend = [int(g[r, c]) for r, c in legend_cells]
    n = len(legend)
    if n == 0:
        return out.tolist()
    seen = np.zeros((H, W), dtype=bool)
    for r0 in range(H):
        for c0 in range(W):
            if g[r0, c0] != GREY or seen[r0, c0]:
                continue
            seen[r0, c0] = True
            queue = deque([(r0, c0)])
            cells = []
            while queue:
                cy, cx = queue.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and g[ny, nx] == GREY and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
            ab = [(cell[AXIS], cell[1 - AXIS]) for cell in cells]
            amin = min(a for a, b in ab)
            amax = max(a for a, b in ab)
            bmin = min(b for a, b in ab)
            bmax = max(b for a, b in ab)
            start = amin if SIGN > 0 else amax
            first = [b for a, b in ab if a == start]
            w = len(first)
            from_low = min(first) == bmin
            cap = amax - amin + 1 - w
            for (cy, cx), (a, b) in zip(cells, ab):
                p = abs(a - start)
                q = (b - bmin) if from_low else (bmax - b)
                d = min(p, q, cap)
                if d < 0:
                    d = 0
                out[cy, cx] = legend[d % n]
    return out.tolist()
'''


def build_program(d4, palette):
    d4 = int(d4)

    def tf(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc

    vr, vc = tf((1, 0))
    ur, uc = tf((0, 1))
    if vr != 0:
        axis, sign = 0, vr
    else:
        axis, sign = 1, vc
    subs = {
        '@BG@': int(palette[0]),
        '@GREY@': int(palette[5]),
        '@AXIS@': axis,
        '@SIGN@': sign,
        '@LUR@': ur,
        '@LUC@': uc,
    }
    src = TEMPLATE
    for k, v in subs.items():
        src = src.replace(k, str(v))
    return src
