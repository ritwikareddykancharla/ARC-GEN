def build_program(d4, palette):
    mask = int(palette[1])
    d4 = int(d4) % 8
    # The colour-cycle (+1 per step) axis is vertical in the native frame;
    # an odd number of clockwise quarter turns makes it horizontal. The repair
    # mechanism needs no special casing, because it looks for periods along
    # both visible axes. The value is recorded in the program for clarity.
    cycle_axis = 'columns' if (d4 % 4) % 2 == 1 else 'rows'
    src = '''
# Masked doubly-periodic wallpaper repair, in visible coordinates.
# Mask / unknown colour (original colour 1): MASK_COLOUR
# The colour cycle advances along: CYCLE_AXIS
MASK = MASK_COLOUR


def _shift_ok(g, H, W, p, axis):
    pairs = False
    if axis == 0:
        for y in range(H - p):
            ra = g[y]
            rb = g[y + p]
            for x in range(W):
                a = ra[x]
                b = rb[x]
                if a != MASK and b != MASK:
                    if a != b:
                        return False
                    pairs = True
    else:
        for y in range(H):
            r = g[y]
            for x in range(W - p):
                a = r[x]
                b = r[x + p]
                if a != MASK and b != MASK:
                    if a != b:
                        return False
                    pairs = True
    return pairs


def _period(g, H, W, axis):
    n = H if axis == 0 else W
    for p in range(1, n):
        if _shift_ok(g, H, W, p, axis):
            return p
    return n


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    if H == 0 or W == 0:
        return g
    py = _period(g, H, W, 0)
    px = _period(g, H, W, 1)
    counts = {}
    order = {}
    k = 0
    for y in range(H):
        for x in range(W):
            v = g[y][x]
            if v == MASK:
                continue
            key = (y % py, x % px)
            c = counts.setdefault(key, {})
            c[v] = c.get(v, 0) + 1
            if (key, v) not in order:
                order[(key, v)] = k
                k += 1
    tile = {}
    for key, c in counts.items():
        best = None
        for v, n in c.items():
            cand = (-n, order[(key, v)], v)
            if best is None or cand < best:
                best = cand
        tile[key] = best[2]
    out = [row[:] for row in g]
    for y in range(H):
        for x in range(W):
            if g[y][x] == MASK:
                out[y][x] = tile.get((y % py, x % px), MASK)
    return out
'''
    src = src.replace('MASK_COLOUR', str(mask)).replace('CYCLE_AXIS', cycle_axis)
    return src
