def build_program(d4, palette):
    bg = int(palette[7])
    src = '''import numpy as np
from collections import deque

BG = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
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

def _is_plus(cells):
    if len(cells) != 5:
        return None
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    if y1 - y0 != 2 or x1 - x0 != 2:
        return None
    cy, cx = y0 + 1, x0 + 1
    want = {(cy, cx), (cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)}
    if set(cells) == want:
        return (cy, cx)
    return None

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    colours = sorted(set(g.ravel().tolist()) - {BG})
    plus = None
    for c in colours:
        comps = _components(g == c)
        for cells in comps:
            ctr = _is_plus(cells)
            if ctr is not None:
                plus = (c, ctr, cells)
                break
        if plus is not None:
            break
    if plus is None:
        return out.tolist()
    pc, (pr, pcl), pcells = plus
    pset = set(pcells)
    row_al = False
    col_al = False
    for c in colours:
        mask = (g == c)
        for (y, x) in pcells:
            mask[y, x] = False
        for cells in _components(mask):
            ys = [q[0] for q in cells]
            xs = [q[1] for q in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            h = y1 - y0 + 1
            w = x1 - x0 + 1
            if h == w and h %% 2 == 1 and len(cells) == h * w:
                cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
                out[cy, cx] = pc
                if cy == pr:
                    row_al = True
                if cx == pcl:
                    col_al = True
    if not (row_al or col_al):
        for (y, x) in pcells:
            out[y, x] = BG
    return out.tolist()
''' % bg
    return src
