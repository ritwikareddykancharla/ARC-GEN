def build_program(d4, palette):
    bg = int(palette[1])
    sh = int(palette[7])
    mk = int(palette[2])
    src = '''
BG = %d
SH = %d
MK = %d

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0])
    out = [row[:] for row in g]
    shape = [(y, x) for y in range(H) for x in range(W) if g[y][x] == SH]
    shp = set(shape)
    markers = [(y, x) for y in range(H) for x in range(W) if g[y][x] == MK]
    vline = hline = None
    vedge = hedge = None
    for (y, x) in markers:
        if y == 0 or y == H - 1:
            vline = x
            vedge = 'top' if y == 0 else 'bottom'
        else:
            hline = y
            hedge = 'left' if x == 0 else 'right'
    for (y, x) in shape:
        out[y][x] = BG
    if vline is not None:
        ys = [y for (y, x) in shape if x == vline]
        if vedge == 'top':
            rng = range(0, max(ys) + 1) if ys else range(H)
        else:
            rng = range(min(ys) if ys else 0, H)
        for y in rng:
            out[y][vline] = SH if (y, vline) in shp else MK
    if hline is not None:
        xs = [x for (y, x) in shape if y == hline]
        if hedge == 'left':
            rng = range(0, max(xs) + 1) if xs else range(W)
        else:
            rng = range(min(xs) if xs else 0, W)
        for x in rng:
            out[hline][x] = SH if (hline, x) in shp else MK
    if vline is not None and hline is not None:
        out[hline][vline] = MK
    groups = {}
    for (y, x) in shape:
        if x == vline or y == hline:
            continue
        if vline is not None:
            hs = 'left' if x < vline else 'right'
        else:
            hs = hedge
        if hline is not None:
            vs = 'top' if y < hline else 'bottom'
        else:
            vs = vedge
        groups.setdefault((vs, hs), []).append((y, x))
    for (vs, hs), cells in groups.items():
        if vline is not None and hline is not None:
            if vs != vedge and hs != hedge:
                continue
        y0 = min(c[0] for c in cells)
        y1 = max(c[0] for c in cells)
        x0 = min(c[1] for c in cells)
        x1 = max(c[1] for c in cells)
        dy = -y0 if vs == 'top' else H - 1 - y1
        dx = -x0 if hs == 'left' else W - 1 - x1
        for (y, x) in cells:
            out[y + dy][x + dx] = SH
    return out
''' % (bg, sh, mk)
    return src
