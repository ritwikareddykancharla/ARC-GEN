def build_program(d4, palette):
    # Original roles: gravity points DOWN (objects sit on the last row),
    # packing runs RIGHT, starting at column 0.
    gy, gx = 1, 0
    py, px = 0, 1
    if d4 >= 4:
        # reversing each row negates horizontal components
        gx = -gx
        px = -px
    for _ in range(d4 % 4):
        # clockwise rotation maps displacement (dy, dx) -> (dx, -dy)
        gy, gx = gx, -gy
        py, px = px, -py
    bg = int(palette[7])
    template = '''from collections import deque

BG = __BG__
GY = __GY__
GX = __GX__
PY = __PY__
PX = __PX__


def _components(g, H, W):
    seen = [[False] * W for _ in range(H)]
    objs = []
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c == BG or seen[y][x]:
                continue
            seen[y][x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == c:
                        seen[ny][nx] = True
                        q.append((ny, nx))
            objs.append((c, cells))
    return objs


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0])
    items = []
    for c, cells in _components(g, H, W):
        ys = [p[0] for p in cells]
        xs = [p[1] for p in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        if y0 == 0 and x0 == 0 and y1 == H - 1 and x1 == W - 1:
            continue  # full-grid frame: a border, not an object
        items.append((len(cells), y0, x0, c, cells, y1 - y0 + 1, x1 - x0 + 1))
    items.sort(key=lambda t: (t[0], t[1], t[2]))
    out = [[BG] * W for _ in range(H)]
    cursor = 0
    for size, y0, x0, c, cells, h, w in items:
        if GY != 0:
            # gravity vertical: rest against top/bottom edge, pack along columns
            ty = H - h if GY > 0 else 0
            tx = cursor if PX > 0 else W - cursor - w
            cursor += w
        else:
            # gravity horizontal: rest against left/right edge, pack along rows
            tx = W - w if GX > 0 else 0
            ty = cursor if PY > 0 else H - cursor - h
            cursor += h
        for y, x in cells:
            yy = ty + y - y0
            xx = tx + x - x0
            if 0 <= yy < H and 0 <= xx < W:
                out[yy][xx] = c
    return out
'''
    return (template.replace('__BG__', str(bg))
            .replace('__GY__', str(gy)).replace('__GX__', str(gx))
            .replace('__PY__', str(py)).replace('__PX__', str(px)))
