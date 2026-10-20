def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np
from collections import deque

BG = __BG__

def _block_pattern(g, c):
    ys, xs = np.where(g == c)
    if len(ys) == 0:
        return None
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    h = y1 - y0 + 1
    w = x1 - x0 + 1
    if h != w or h % 3 != 0 or h < 6:
        return None
    m = h // 3
    pat = np.zeros((3, 3), dtype=bool)
    for r in range(3):
        for cc in range(3):
            blk = g[y0 + r * m:y0 + (r + 1) * m, x0 + cc * m:x0 + (cc + 1) * m] == c
            if blk.all():
                pat[r, cc] = True
            elif blk.any():
                return None
    return pat

def _largest_component_colour(g):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    best_size, best_col = -1, None
    for y in range(h):
        for x in range(w):
            if g[y, x] == BG or seen[y, x]:
                continue
            col = g[y, x]
            seen[y, x] = True
            q = deque([(y, x)])
            n = 0
            while q:
                cy, cx = q.popleft()
                n += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == col:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            if n > best_size:
                best_size, best_col = n, int(col)
    return best_col

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    cols = [int(c) for c in np.unique(g) if int(c) != BG]
    out = np.full((3, 3), BG, dtype=int)
    if not cols:
        return out.tolist()
    counts = {c: int((g == c).sum()) for c in cols}
    cands = []
    for c in cols:
        p = _block_pattern(g, c)
        if p is not None:
            cands.append((counts[c], c, p))
    if cands:
        cands.sort(key=lambda t: (-t[0], t[1]))
        _, sc, pat = cands[0]
    else:
        sc = _largest_component_colour(g)
        ys, xs = np.where(g == sc)
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        bh = max(1, (y1 - y0 + 1) // 3)
        bw = max(1, (x1 - x0 + 1) // 3)
        pat = np.zeros((3, 3), dtype=bool)
        for r in range(3):
            for c in range(3):
                cy = min(g.shape[0] - 1, y0 + r * bh + bh // 2)
                cx = min(g.shape[1] - 1, x0 + c * bw + bw // 2)
                pat[r, c] = g[cy, cx] == sc
    others = [c for c in cols if c != sc]
    if others:
        others.sort(key=lambda c: (-counts[c], c))
        nc = others[0]
    else:
        nc = sc
    out[pat] = nc
    return out.tolist()
'''
    return src.replace('__BG__', str(bg))
