def build_program(d4, palette):
    # The mechanism is defined relative to the seed's own edge, which is read
    # from the visible pixels. d4 therefore needs no special handling here.
    # Colour roles become palette constants.
    header = (
        "BG = %d\n" % palette[8] +
        "SEED = %d\n" % palette[3] +
        "BAR = %d\n" % palette[2] +
        "ONE = %d\n" % palette[1]
    )
    body = '''
def _components(g, H, W):
    lab = {}
    comps = []
    for r in range(H):
        for c in range(W):
            if (g[r][c] == BAR or g[r][c] == ONE) and (r, c) not in lab:
                idx = len(comps)
                stack = [(r, c)]
                lab[(r, c)] = idx
                cells = []
                while stack:
                    y, x = stack.pop()
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in lab and (g[ny][nx] == BAR or g[ny][nx] == ONE):
                            lab[(ny, nx)] = idx
                            stack.append((ny, nx))
                comps.append(cells)
    return comps, lab


def solve(demonstrations, grid):
    H = len(grid)
    W = len(grid[0])
    g = [list(row) for row in grid]
    out = [[BAR if v == ONE else v for v in row] for row in g]
    seeds = [(r, c) for r in range(H) for c in range(W) if g[r][c] == SEED]
    if not seeds:
        return out
    sy, sx = seeds[0]
    # The path heads straight away from the edge the seed sits on.
    if sy == 0 and 0 < sx < W - 1:
        dy, dx = 1, 0
    elif sy == H - 1 and 0 < sx < W - 1:
        dy, dx = -1, 0
    elif sx == 0:
        dy, dx = 0, 1
    elif sx == W - 1:
        dy, dx = 0, -1
    elif sy == 0:
        dy, dx = 1, 0
    else:
        dy, dx = -1, 0
    comps, lab = _components(g, H, W)
    vertical = dy != 0
    lat_max = (W - 1) if vertical else (H - 1)
    y, x = sy, sx
    inside = lambda a, b: 0 <= a < H and 0 <= b < W
    for _ in range(len(comps) + 2):
        # Scan ahead in the travel direction for the next bar.
        ty, tx, hit = y + dy, x + dx, None
        while inside(ty, tx):
            if (ty, tx) in lab:
                hit = lab[(ty, tx)]
                break
            ty += dy
            tx += dx
        if hit is None:
            ty, tx = y + dy, x + dx
            while inside(ty, tx):
                out[ty][tx] = SEED
                ty += dy
                tx += dx
            break
        cells = comps[hit]
        k = sum(1 for (a, b) in cells if g[a][b] == ONE) + 1
        # Advance until the path is k cells short of the bar.
        dist = abs(ty - y) + abs(tx - x)
        n = dist - k
        for _i in range(max(n, 0)):
            y += dy
            x += dx
            out[y][x] = SEED
        # Sidestep past the bar's free end by k cells.
        lats = [b for (a, b) in cells] if vertical else [a for (a, b) in cells]
        lo, hi = min(lats), max(lats)
        if lo == 0 and hi < lat_max:
            target, st = hi + k, 1
        elif hi == lat_max and lo > 0:
            target, st = lo - k, -1
        elif lat_max - hi > lo:
            target, st = hi + k, 1
        else:
            target, st = lo - k, -1
        target = max(0, min(lat_max, target))
        if vertical:
            while x != target:
                x += st
                out[y][x] = SEED
        else:
            while y != target:
                y += st
                out[y][x] = SEED
    return out
'''
    return header + body
