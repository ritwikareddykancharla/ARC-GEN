def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[1])
    src = '''import numpy as np
from collections import deque

BG = %d
MARK = %d

def _components(g):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    objs = []
    for y in range(h):
        for x in range(w):
            if seen[y, x] or g[y, x] == BG:
                continue
            col = int(g[y, x])
            seen[y, x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == col:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            y0, x0, y1, x1 = min(ys), min(xs), max(ys), max(xs)
            mask = [[0] * (x1 - x0 + 1) for _ in range(y1 - y0 + 1)]
            for cy, cx in cells:
                mask[cy - y0][cx - x0] = 1
            key = tuple(tuple(r) for r in mask)
            objs.append({'colour': col, 'cells': cells, 'box': (y0, x0), 'key': key})
    objs.sort(key=lambda o: o['box'])
    return objs

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    objs = _components(g)
    lookup = {}
    for o in objs:
        if o['colour'] != MARK:
            lookup.setdefault(o['key'], o['colour'])
    out = g.copy()
    for o in objs:
        if o['colour'] != MARK:
            continue
        c = lookup.get(o['key'])
        if c is None:
            continue
        for y, x in o['cells']:
            out[y, x] = c
    return out.tolist()
''' % (bg, mark)
    return src
