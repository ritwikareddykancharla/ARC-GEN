def build_program(d4, palette):
    bg = int(palette[7])
    key = int(palette[0])
    tgt = int(palette[5])
    mark = int(palette[6])
    src = '''
from collections import deque

BG = __BG__
KEY = __KEY__
TGT = __TGT__
MARK = __MARK__


def _components(g, colour):
    h = len(g)
    w = len(g[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            if g[y][x] == colour and not seen[y][x]:
                seen[y][x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == colour:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _box(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return (min(ys), min(xs), max(ys), max(xs))


def _split(cells):
    cs = set(cells)
    y0, x0, y1, x1 = _box(cells)
    best = None
    for a in range(y0, y1 + 1):
        for b in range(a, y1 + 1):
            for c in range(x0, x1 + 1):
                for d in range(c, x1 + 1):
                    area = (b - a + 1) * (d - c + 1)
                    if best is not None and area <= best[0]:
                        continue
                    ok = True
                    for yy in range(a, b + 1):
                        for xx in range(c, d + 1):
                            if (yy, xx) not in cs:
                                ok = False
                                break
                        if not ok:
                            break
                    if ok:
                        best = (area, (a, c, b, d))
    a, c, b, d = best[1]
    stem = [p for p in cells if not (a <= p[0] <= b and c <= p[1] <= d)]
    return (a, c, b, d), stem


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    fives = _components(g, TGT)
    if not fives:
        return g
    f = max(fives, key=lambda cs: len(cs))
    fy0, fx0, fy1, fx1 = _box(f)
    fcy = (fy0 + fy1) / 2.0
    fcx = (fx0 + fx1) / 2.0
    keys = _components(g, KEY)
    keys.sort(key=lambda cs: (_box(cs)[0], _box(cs)[1]))
    cands = []
    for cells in keys:
        if len(cells) < 3:
            continue
        rect, stem = _split(cells)
        if not stem:
            continue
        a, c, b, d = rect
        rows = not (b < fy0 or a > fy1)
        cols = not (d < fx0 or c > fx1)
        if not (rows or cols):
            continue
        dist = abs((a + b) / 2.0 - fcy) + abs((c + d) / 2.0 - fcx)
        cands.append((dist, len(cands), rect, stem, rows))
    if not cands:
        return g
    cands.sort(key=lambda t: (t[0], t[1]))
    _, _, (a, c, b, d), stem, rows = cands[0]
    for y, x in stem:
        g[y][x] = BG
    if rows:
        x = c if fcx < (c + d) / 2.0 else d
        for y in range(a, b + 1):
            g[y][x] = MARK
    else:
        y = a if fcy < (a + b) / 2.0 else b
        for x in range(c, d + 1):
            g[y][x] = MARK
    return g
'''
    src = src.replace('__BG__', repr(bg)).replace('__KEY__', repr(key))
    src = src.replace('__TGT__', repr(tgt)).replace('__MARK__', repr(mark))
    return src
