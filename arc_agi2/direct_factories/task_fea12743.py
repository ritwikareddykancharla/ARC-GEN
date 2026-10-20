def build_program(d4, palette):
    d4 = int(d4)
    k = d4 % 4
    flip = 1 if d4 >= 4 else 0
    bg = int(palette[0])
    ink = int(palette[2])
    maxc = int(palette[3])
    partc = int(palette[8])
    lines = []
    lines.append('import numpy as np')
    lines.append('from itertools import combinations')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('INK = %d' % ink)
    lines.append('MAX_COLOR = %d' % maxc)
    lines.append('PART_COLOR = %d' % partc)
    lines.append('ROT = %d' % k)
    lines.append('FLIP = %d' % flip)
    lines.append('TILE = 4')
    lines.append('STEP = 5')
    body = '''

def _reading_rank(rv, cv):
    # Visible tile lattice position -> rank in the constructor's reading
    # order, which in visible coordinates is a transformed scan order.
    if ROT % 2:
        R, C = cv, rv
    else:
        R, C = rv, cv
    rank = {}
    for ty in range(R):
        for tx in range(C):
            y, x = ty, tx
            h, w = R, C
            if FLIP:
                x = w - 1 - x
            for _ in range(ROT):
                y, x = x, h - 1 - y
                h, w = w, h
            rank[(y, x)] = ty * C + tx
    return rank


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    rv = max(0, (H - 1) // STEP)
    cv = max(0, (W - 1) // STEP)
    out = g.copy()
    if rv == 0 or cv == 0:
        return out.tolist()
    rank = _reading_rank(rv, cv)
    tiles = {}
    for i in range(rv):
        for j in range(cv):
            y0 = 1 + STEP * i
            x0 = 1 + STEP * j
            tiles[(i, j)] = g[y0:y0 + TILE, x0:x0 + TILE] != BG
    keys = sorted(tiles, key=lambda p: rank.get(p, 0))
    mx = max(keys, key=lambda p: (int(tiles[p].sum()), -rank.get(p, 0)))
    M = tiles[mx]

    def paint(p, color):
        y0 = 1 + STEP * p[0]
        x0 = 1 + STEP * p[1]
        sub = out[y0:y0 + TILE, x0:x0 + TILE]
        sub[tiles[p]] = color

    paint(mx, MAX_COLOR)
    subs = [p for p in keys if p != mx and not (tiles[p] & ~M).any()]
    best = None
    best_key = None
    for a, b in combinations(subs, 2):
        if np.array_equal(tiles[a] | tiles[b], M):
            key = tuple(sorted((rank.get(a, 0), rank.get(b, 0))))
            if best_key is None or key < best_key:
                best_key = key
                best = (a, b)
    if best is not None:
        for p in best:
            paint(p, PART_COLOR)
    return out.tolist()
'''
    return '\n'.join(lines) + body
