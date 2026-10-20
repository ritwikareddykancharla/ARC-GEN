def build_program(d4, palette):
    # canonical 'down' (sky -> floor) direction is (+1, 0) in (dy, dx)
    dy, dx = 1, 0
    if d4 >= 4:
        dx = -dx  # reverse each row: x -> W-1-x
    for _ in range(d4 % 4):
        dy, dx = dx, -dy  # clockwise rotation: (r,c)->(c,H-1-r)
    if dy != 0:
        ly, lx = 0, 1
    else:
        ly, lx = 1, 0
    consts = {
        '__OBJ__': str(int(palette[5])),
        '__SKY__': str(int(palette[1])),
        '__STREAK__': str(int(palette[9])),
        '__DY__': str(int(dy)),
        '__DX__': str(int(dx)),
        '__LY__': str(int(ly)),
        '__LX__': str(int(lx)),
    }
    template = '''import numpy as np

OBJ = __OBJ__
SKY = __SKY__
STREAK = __STREAK__
DY = __DY__
DX = __DX__
LY = __LY__
LX = __LX__


def _lat(y, x):
    return y * LY + x * LX


def _dep(y, x):
    return y * DY + x * DX


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    cells = [(int(y), int(x)) for y, x in np.argwhere(g == OBJ)]
    if not cells:
        return out.tolist()
    N = W if LX else H
    ps = [_lat(y, x) for y, x in cells]
    pmin, pmax = min(ps), max(ps)
    w = pmax - pmin + 1
    if pmin == 0 and pmax != N - 1:
        from_low = True
    elif pmax == N - 1 and pmin != 0:
        from_low = False
    else:
        from_low = pmin <= N - 1 - pmax
    levels = {}
    for y, x in cells:
        levels.setdefault(_dep(y, x), set()).add(_lat(y, x))
    full = [d for d, s in levels.items() if len(s) == w]
    hdr = max(full) if full else min(levels) - 1
    start = N - w if from_low else 0
    sgn = -1 if from_low else 1
    for y, x in cells:
        out[y, x] = SKY
    dbot = max(levels)
    bottom = []
    for y, x in cells:
        d = _dep(y, x)
        k = max(0, d - hdr - 1)
        p = _lat(y, x)
        newp = p - pmin + start + sgn * k
        delta = newp - p
        ny, nx = y + LY * delta, x + LX * delta
        if 0 <= ny < H and 0 <= nx < W:
            out[ny, nx] = OBJ
            if d == dbot:
                bottom.append((ny, nx))
    if bottom:
        bps = [_lat(y, x) for y, x in bottom]
        if from_low:
            front = max(bps)
            rng = range(0, front)
        else:
            front = min(bps)
            rng = range(front + 1, N)
        by, bx = bottom[0]
        by += DY
        bx += DX
        pb = _lat(by, bx)
        for q in rng:
            yy, xx = by + LY * (q - pb), bx + LX * (q - pb)
            if 0 <= yy < H and 0 <= xx < W:
                out[yy, xx] = STREAK
    return out.tolist()
'''
    for key, val in consts.items():
        template = template.replace(key, val)
    return template
