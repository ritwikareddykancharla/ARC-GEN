TEMPLATE = r'''import numpy as np
from collections import deque

BG = __BG__
BODY = __BODY__
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _pieces(g, bg):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if g[y, x] == bg or seen[y, x]:
                continue
            seen[y, x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in DIRS:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and (not seen[ny, nx]) and g[ny, nx] != bg:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            y0 = min(c[0] for c in cells)
            x0 = min(c[1] for c in cells)
            y1 = max(c[0] for c in cells)
            x1 = max(c[1] for c in cells)
            rel = {(cy - y0, cx - x0): int(g[cy, cx]) for cy, cx in cells}
            out.append({'cells': rel, 'h': y1 - y0 + 1, 'w': x1 - x0 + 1})
    return out


def _outside(p, y, x):
    return not (0 <= y < p['h'] and 0 <= x < p['w'])


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    bg = BG
    if not np.any(g == bg):
        vals, counts = np.unique(g, return_counts=True)
        bg = int(vals[np.argmax(counts)])
    pieces = _pieces(g, bg)
    if not pieces:
        return np.asarray(grid, dtype=int).tolist()
    found = {}
    for i, p in enumerate(pieces):
        for cell, v in sorted(p['cells'].items()):
            if v != BODY:
                found.setdefault(v, []).append((i, cell))
    links = []
    for v in sorted(found):
        lst = found[v]
        if len(lst) == 2 and lst[0][0] != lst[1][0]:
            links.append((lst[0], lst[1]))
    pos = {0: (0, 0)}
    occupied = set(pieces[0]['cells'])
    order = [0]
    changed = True
    while changed:
        changed = False
        for la, lb in links:
            for (a, ma), (b, mb) in ((la, lb), (lb, la)):
                if a not in pos or b in pos:
                    continue
                pa, pb = pieces[a], pieces[b]
                for dy, dx in DIRS:
                    if not _outside(pa, ma[0] + dy, ma[1] + dx):
                        continue
                    if not _outside(pb, mb[0] - dy, mb[1] - dx):
                        continue
                    ay, ax = pos[a]
                    oy = ay + ma[0] + dy - mb[0]
                    ox = ax + ma[1] + dx - mb[1]
                    cells = {(oy + y, ox + x) for y, x in pb['cells']}
                    if cells & occupied:
                        continue
                    pos[b] = (oy, ox)
                    occupied |= cells
                    order.append(b)
                    changed = True
                    break
    miny = min(y for y, x in occupied)
    minx = min(x for y, x in occupied)
    H = max(y for y, x in occupied) - miny + 1
    W = max(x for y, x in occupied) - minx + 1
    out = np.full((H, W), bg, dtype=int)
    for i in order:
        oy, ox = pos[i]
        for (y, x), v in pieces[i]['cells'].items():
            out[oy + y - miny, ox + x - minx] = v
    return out.tolist()
'''


def build_program(d4, palette):
    bg = int(palette[2])
    body = int(palette[1])
    return TEMPLATE.replace('__BG__', str(bg)).replace('__BODY__', str(body))
