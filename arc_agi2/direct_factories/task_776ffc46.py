def build_program(d4, palette):
    bg = int(palette[0])
    target = int(palette[1])
    frame = int(palette[5])
    header = (
        "BG = %d\n"
        "TARGET = %d\n"
        "FRAME = %d\n"
    ) % (bg, target, frame)
    body = '''
from collections import deque


def _components(g, h, w):
    seen = [[False] * w for _ in range(h)]
    objs = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or g[y][x] == BG:
                continue
            col = g[y][x]
            seen[y][x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True
                        q.append((ny, nx))
            objs.append((col, sorted(cells)))
    return objs


def _box(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return min(ys), min(xs), max(ys), max(xs)


def _mask(cells):
    y0, x0, y1, x1 = _box(cells)
    m = [[0] * (x1 - x0 + 1) for _ in range(y1 - y0 + 1)]
    for y, x in cells:
        m[y - y0][x - x0] = 1
    return tuple(tuple(r) for r in m)


def _is_ring(cells):
    y0, x0, y1, x1 = _box(cells)
    hh, ww = y1 - y0 + 1, x1 - x0 + 1
    if hh < 3 or ww < 3 or len(cells) != 2 * (hh + ww) - 4:
        return False
    for y, x in cells:
        if not (y == y0 or y == y1 or x == x0 or x == x1):
            return False
    return True


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    objs = _components(g, h, w)
    rings = [_box(cells) for col, cells in objs if col == FRAME and _is_ring(cells)]
    templates = {}
    for col, cells in objs:
        if col == FRAME or col == TARGET:
            continue
        oy0, ox0, oy1, ox1 = _box(cells)
        for ry0, rx0, ry1, rx1 in rings:
            if ry0 < oy0 and oy1 < ry1 and rx0 < ox0 and ox1 < rx1:
                key = _mask(cells)
                if key not in templates:
                    templates[key] = col
                break
    out = [row[:] for row in g]
    for col, cells in objs:
        if col != TARGET:
            continue
        key = _mask(cells)
        if key in templates:
            c = templates[key]
            for y, x in cells:
                out[y][x] = c
    return out
'''
    return header + body
