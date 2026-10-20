def build_program(d4, palette):
    def T(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc
    down = T((1, 0))
    right = T((0, 1))
    src = '''import numpy as np
from collections import Counter, deque

DOWN_R = __DR__
DOWN_C = __DC__
SHIFT_R = __SR__
SHIFT_C = __SC__

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
                out.append(sorted(cells))
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    out = np.full_like(g, bg)
    for cells in _components(g != bg):
        cols = {}
        for y, x in cells:
            cols.setdefault(int(g[y, x]), []).append((y, x))
        # 'top' piece = the one extending furthest against the stacking direction
        order = sorted(cols, key=lambda c: min(y * DOWN_R + x * DOWN_C for y, x in cols[c]))
        for i, c in enumerate(order):
            s = -1 if i == 0 else 1
            for y, x in cols[c]:
                ny, nx = y + s * SHIFT_R, x + s * SHIFT_C
                if 0 <= ny < h and 0 <= nx < w:
                    out[ny, nx] = c
    return out.tolist()
'''
    src = src.replace('__DR__', str(down[0])).replace('__DC__', str(down[1]))
    src = src.replace('__SR__', str(right[0])).replace('__SC__', str(right[1]))
    return src
