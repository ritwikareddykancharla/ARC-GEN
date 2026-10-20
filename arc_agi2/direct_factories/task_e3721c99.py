def build_program(d4, palette):
    bg = int(palette[0])
    grey = int(palette[5])
    divider = int(palette[1])
    src = '''
BG = %d
GREY = %d
DIVIDER = %d

_N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(grid, H, W):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if seen[r][c] or grid[r][c] == BG:
                continue
            col = grid[r][c]
            seen[r][c] = True
            stack = [(r, c)]
            cells = []
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for dy, dx in _N4:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and grid[ny][nx] == col:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            cells.sort()
            comps.append((col, cells))
    return comps


def _holes(cells):
    ys = [p[0] for p in cells]
    xs = [p[1] for p in cells]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    h, w = y1 - y0 + 1, x1 - x0 + 1
    occ = [[False] * w for _ in range(h)]
    for y, x in cells:
        occ[y - y0][x - x0] = True
    seen = [[False] * w for _ in range(h)]
    n = 0
    for r in range(h):
        for c in range(w):
            if occ[r][c] or seen[r][c]:
                continue
            seen[r][c] = True
            stack = [(r, c)]
            edge = False
            while stack:
                y, x = stack.pop()
                if y == 0 or x == 0 or y == h - 1 or x == w - 1:
                    edge = True
                for dy, dx in _N4:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and not occ[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            if not edge:
                n += 1
    return n


def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    comps = _components(g, H, W)
    keys = []
    blobs = []
    for col, cells in comps:
        if col == GREY:
            blobs.append(cells)
            continue
        touches = any(y == 0 or x == 0 or y == H - 1 or x == W - 1 for y, x in cells)
        if touches:
            # divider (straight full line or L-shaped corner box); never a key
            continue
        keys.append((cells[0], col, _holes(cells)))
    keys.sort()
    legend = {}
    for _, col, h in keys:
        if h not in legend:
            legend[h] = col
    for cells in blobs:
        target = legend.get(_holes(cells), BG)
        for y, x in cells:
            out[y][x] = target
    return out
''' % (bg, grey, divider)
    return src
