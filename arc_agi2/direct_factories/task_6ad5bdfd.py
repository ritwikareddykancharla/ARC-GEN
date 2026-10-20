def build_program(d4, palette):
    bg = int(palette[0])
    wall = int(palette[2])
    src = '''
BG = __BG__
WALL = __WALL__


def _components(g, H, W, skip):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            if seen[y][x] or g[y][x] == BG or (y, x) in skip:
                continue
            col = g[y][x]
            stack = [(y, x)]
            seen[y][x] = True
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and (ny, nx) not in skip and g[ny][nx] == col:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            comps.append((col, sorted(cells)))
    return comps


def _find_wall(g, H, W):
    lines = [
        ((-1, 0), [(0, x) for x in range(W)]),
        ((1, 0), [(H - 1, x) for x in range(W)]),
        ((0, -1), [(y, 0) for y in range(H)]),
        ((0, 1), [(y, W - 1) for y in range(H)]),
    ]
    for d, cells in lines:
        if all(g[y][x] == WALL for y, x in cells):
            return d, cells
    best = None
    for d, cells in lines:
        vals = [g[y][x] for y, x in cells]
        if vals[0] != BG and all(v == vals[0] for v in vals):
            if best is None or len(cells) > len(best[1]):
                best = (d, cells)
    if best is not None:
        return best
    return lines[0]


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0])
    (dy, dx), wcells = _find_wall(g, H, W)
    skip = set(wcells)
    comps = _components(g, H, W, skip)

    def dist(cells):
        if dy == -1:
            return min(y for y, x in cells)
        if dy == 1:
            return min(H - 1 - y for y, x in cells)
        if dx == -1:
            return min(x for y, x in cells)
        return min(W - 1 - x for y, x in cells)

    comps.sort(key=lambda c: (dist(c[1]), c[1][0]))
    out = [row[:] for row in g]
    for col, cells in comps:
        for y, x in cells:
            out[y][x] = BG
        k = 0
        while True:
            ok = True
            for y, x in cells:
                ny = y + dy * (k + 1)
                nx = x + dx * (k + 1)
                if not (0 <= ny < H and 0 <= nx < W) or out[ny][nx] != BG:
                    ok = False
                    break
            if not ok:
                break
            k += 1
        for y, x in cells:
            out[y + dy * k][x + dx * k] = col
    return out
'''
    return src.replace('__BG__', str(bg)).replace('__WALL__', str(wall))
