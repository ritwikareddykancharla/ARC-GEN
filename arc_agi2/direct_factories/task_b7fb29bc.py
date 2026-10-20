def build_program(d4, palette):
    bg = int(palette[0])
    fr = int(palette[3])
    odd = int(palette[4])
    even = int(palette[2])
    src = '''import numpy as np
from collections import deque

BG = __BG__
FRAME = __FR__
ODD = __ODD__
EVEN = __EVEN__

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    mask = (g == FRAME)
    seen = np.zeros((h, w), dtype=bool)
    best = []
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
                if len(cells) > len(best):
                    best = cells
    if not best:
        return out.tolist()
    ys = [c[0] for c in best]
    xs = [c[1] for c in best]
    iy0, iy1 = min(ys) + 1, max(ys) - 1
    ix0, ix1 = min(xs) + 1, max(xs) - 1
    if iy0 > iy1 or ix0 > ix1:
        return out.tolist()
    seeds = [(y, x) for y in range(iy0, iy1 + 1) for x in range(ix0, ix1 + 1) if g[y, x] != BG]
    if not seeds:
        return out.tolist()
    for y in range(iy0, iy1 + 1):
        for x in range(ix0, ix1 + 1):
            if g[y, x] == BG:
                d = min(max(abs(y - sy), abs(x - sx)) for sy, sx in seeds)
                out[y, x] = ODD if d % 2 == 1 else EVEN
    return out.tolist()
'''
    src = src.replace('__BG__', repr(bg)).replace('__FR__', repr(fr))
    src = src.replace('__ODD__', repr(odd)).replace('__EVEN__', repr(even))
    return src
