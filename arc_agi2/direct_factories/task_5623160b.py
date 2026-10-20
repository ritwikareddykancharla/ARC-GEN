def build_program(d4, palette):
    bg = int(palette[7])
    anchor = int(palette[9])
    src = '''
BG = %d
ANCHOR = %d
STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))

def _components(g, H, W):
    seen = [[False] * W for _ in range(H)]
    out = []
    for y in range(H):
        for x in range(W):
            col = g[y][x]
            if col == BG or col == ANCHOR or seen[y][x]:
                continue
            seen[y][x] = True
            stack = [(y, x)]
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in STEPS:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            out.append((col, sorted(cells)))
    out.sort(key=lambda t: t[1][0])
    return out

def _push_dir(g, cells, H, W):
    # Direction of motion = from touching anchor cell toward the object (away from the anchor).
    cs = set(cells)
    first = None
    sides = []
    for y, x in cells:
        for dy, dx in STEPS:
            ny, nx = y - dy, x - dx
            if 0 <= ny < H and 0 <= nx < W and g[ny][nx] == ANCHOR and (ny, nx) not in cs:
                if (dy, dx) not in sides:
                    sides.append((dy, dx))
    if not sides:
        return None
    return sides[0]

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    comps = _components(g, H, W)
    movers = []
    for col, cells in comps:
        d = _push_dir(g, cells, H, W)
        if d is not None:
            movers.append((col, cells, d))
    # erase every mover first so movement order cannot matter
    for col, cells, d in movers:
        for y, x in cells:
            g[y][x] = BG
    for col, cells, (dy, dx) in movers:
        k = 0
        while True:
            ok = True
            for y, x in cells:
                ny, nx = y + (k + 1) * dy, x + (k + 1) * dx
                if not (0 <= ny < H and 0 <= nx < W) or g[ny][nx] != BG:
                    ok = False
                    break
            if not ok:
                break
            k += 1
        for y, x in cells:
            g[y + k * dy][x + k * dx] = col
    return g
''' % (bg, anchor)
    return src
