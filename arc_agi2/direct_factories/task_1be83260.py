def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np
from collections import deque

BG = %d

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
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    bg = BG
    vals, cnt = np.unique(g[g != bg], return_counts=True)
    if len(vals) == 0:
        return g.tolist()
    tc = int(vals[int(np.argmax(cnt))])
    best = None
    for comp in _components(g != bg):
        ys = [c[0] for c in comp]
        xs = [c[1] for c in comp]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        sub = g[y0:y1 + 1, x0:x1 + 1]
        n_marks = int(((sub != tc) & (sub != bg)).sum())
        if n_marks > 0 and (best is None or n_marks > best[0]):
            best = (n_marks, y0, x0, y1, x1)
    if best is None:
        return g.tolist()
    _, y0, x0, y1, x1 = best
    mc = g[y0:y1 + 1, x0:x1 + 1]
    h, w = mc.shape
    holes = mc != tc
    nr = (h - 1) // 2
    nc = (w - 1) // 2
    out = np.full((nr * (h + 1) - 1, nc * (w + 1) - 1), tc, dtype=int)
    for i in range(nr):
        for j in range(nc):
            v = int(mc[2 * i + 1, 2 * j + 1])
            if v == tc:
                continue
            r0 = i * (h + 1)
            c0 = j * (w + 1)
            block = np.full((h, w), v, dtype=int)
            block[holes] = tc
            out[r0:r0 + h, c0:c0 + w] = block
    return out.tolist()
''' % bg
    return src
