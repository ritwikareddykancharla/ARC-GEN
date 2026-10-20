TEMPLATE = '''from collections import deque

BG = __BG__
TABLE = __TABLE__


def _holes(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    hh, ww = y1 - y0 + 1, x1 - x0 + 1
    obj = [[False] * ww for _ in range(hh)]
    for y, x in cells:
        obj[y - y0][x - x0] = True
    vis = [[False] * ww for _ in range(hh)]
    n = 0
    for sy in range(hh):
        for sx in range(ww):
            if obj[sy][sx] or vis[sy][sx]:
                continue
            vis[sy][sx] = True
            q = deque([(sy, sx)])
            touches = False
            while q:
                cy, cx = q.popleft()
                if cy == 0 or cx == 0 or cy == hh - 1 or cx == ww - 1:
                    touches = True
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < hh and 0 <= nx < ww and not obj[ny][nx] and not vis[ny][nx]:
                        vis[ny][nx] = True
                        q.append((ny, nx))
            if not touches:
                n += 1
    return n


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    out = [row[:] for row in g]
    seen = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if g[y][x] == BG or seen[y][x]:
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
            k = _holes(cells)
            new = TABLE.get(k, col)
            for cy, cx in cells:
                out[cy][cx] = new
    return out
'''


def build_program(d4, palette):
    bg = int(palette[0])
    table = {1: int(palette[1]), 2: int(palette[2]), 3: int(palette[3]), 4: int(palette[7])}
    return TEMPLATE.replace('__BG__', repr(bg)).replace('__TABLE__', repr(table))
