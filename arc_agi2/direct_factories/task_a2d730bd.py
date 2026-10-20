PROGRAM = '''import numpy as np
from collections import Counter, deque


def _components(g, bg):
    H, W = g.shape
    seen = np.zeros((H, W), dtype=bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if seen[y, x] or g[y, x] == bg:
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
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == col:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            comps.append({'colour': col, 'cells': cells, 'size': len(cells),
                          'box': (min(ys), min(xs), max(ys), max(xs))})
    return comps


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    comps = _components(g, bg)
    rects = [c for c in comps if c['size'] > 1]
    dots = [c for c in comps if c['size'] == 1]
    out = g.copy()
    jobs = []
    for d in dots:
        col = d['colour']
        dy, dx = d['cells'][0]
        best = None
        for r in rects:
            if r['colour'] != col:
                continue
            y0, x0, y1, x1 = r['box']
            if y0 <= dy <= y1 and (dx > x1 or dx < x0):
                dist = (dx - x1) if dx > x1 else (x0 - dx)
                cand = (dist, 'h', r)
            elif x0 <= dx <= x1 and (dy > y1 or dy < y0):
                dist = (dy - y1) if dy > y1 else (y0 - dy)
                cand = (dist, 'v', r)
            else:
                continue
            if best is None or cand[0] < best[0]:
                best = cand
        if best is None:
            continue
        out[dy, dx] = bg
        jobs.append((dy, dx, col, best[1], best[2]['box']))

    def put(y, x, c):
        if 0 <= y < H and 0 <= x < W:
            out[y, x] = c

    for dy, dx, c, kind, box in jobs:
        y0, x0, y1, x1 = box
        if kind == 'h':
            if dx > x1:
                s = x1 + 1
                xs = range(s, dx)
            else:
                s = x0 - 1
                xs = range(dx + 1, s + 1)
            for yy in (dy - 1, dy, dy + 1):
                put(yy, s, c)
            for xx in xs:
                put(dy, xx, c)
        else:
            if dy > y1:
                s = y1 + 1
                ys = range(s, dy)
            else:
                s = y0 - 1
                ys = range(dy + 1, s + 1)
            for xx in (dx - 1, dx, dx + 1):
                put(s, xx, c)
            for yy in ys:
                put(yy, dx, c)
        for ny, nx in ((dy - 1, dx), (dy + 1, dx), (dy, dx - 1), (dy, dx + 1)):
            put(ny, nx, c)
    return out.tolist()
'''


def build_program(d4, palette):
    # The mechanism is expressed symmetrically in visible coordinates.
    # A dot inside a rectangle's row span gets a horizontal connector, and a
    # dot inside its column span gets a vertical one. Both directions on each
    # axis are handled explicitly. Every D4 image of the family is therefore
    # solved by the same direct-coordinate code.
    # Colour roles are inferred from pixels: the background is the most common
    # colour, and each dot is paired with the rectangle of the same colour.
    # No palette constants are needed and no colours are permuted.
    return PROGRAM
