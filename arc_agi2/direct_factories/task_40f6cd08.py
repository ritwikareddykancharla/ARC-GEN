def build_program(d4, palette):
    bg = int(palette[0])
    src = r'''
import numpy as np
from collections import deque, defaultdict, Counter

BG = __BG__

def _components(g):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if g[y, x] != BG and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] != BG:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def _bbox(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return (min(ys), min(xs), max(ys), max(xs))

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    info = []
    for cells in _components(g):
        cols = set(int(g[y, x]) for y, x in cells)
        info.append((cells, _bbox(cells), cols))
    tmpls = [i for i in info if len(i[2]) > 1]
    if not tmpls:
        return out.tolist()
    tmpl = max(tmpls, key=lambda i: len(i[0]))
    targets = [i for i in info if len(i[2]) == 1]
    if not targets:
        return out.tolist()
    base = Counter(next(iter(i[2])) for i in targets).most_common(1)[0][0]
    ty0, tx0, ty1, tx1 = tmpl[1]
    per = defaultdict(list)
    for y, x in tmpl[0]:
        c = int(g[y, x])
        if c != base:
            per[c].append((y, x))
    layers = []
    for c, cells in per.items():
        y0, x0, y1, x1 = _bbox(cells)
        area = (y1 - y0 + 1) * (x1 - x0 + 1)
        layers.append((area, c, y0 - ty0, x0 - tx0, ty1 - y1, tx1 - x1))
    layers.sort(key=lambda t: -t[0])
    for cells, box, cols in targets:
        if next(iter(cols)) != base:
            continue
        y0, x0, y1, x1 = box
        for _, c, dt, dl, db, dr in layers:
            a, b, e, f = y0 + dt, x0 + dl, y1 - db, x1 - dr
            if a <= e and b <= f:
                out[a:e + 1, b:f + 1] = c
    return out.tolist()
'''
    return src.replace('__BG__', str(bg))
