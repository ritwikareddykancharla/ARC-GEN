def build_program(d4, palette):
    k = d4 % 4
    # Original segments lie on anti-diagonals (x+y const). A horizontal flip or a
    # quarter-turn each swaps anti-diagonals with main diagonals (y-x const).
    flips = (1 if d4 >= 4 else 0) + k
    anti = (flips % 2 == 0)
    bg = int(palette[8])
    fill = int(palette[2])
    src = '''
BG = %d
FILL = %d
ANTI = %r


def _coords(y, x):
    # L: index of the diagonal line carrying the segments.
    # P: position along that line (neighbouring cells differ by 2).
    if ANTI:
        return x + y, y - x
    return y - x, x + y


def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    lines = {}
    for y in range(H):
        for x in range(W):
            if g[y][x] != BG:
                L, P = _coords(y, x)
                lines.setdefault(L, []).append(P)
    segs = []
    for L in sorted(lines):
        ps = sorted(lines[L])
        start = ps[0]
        prev = ps[0]
        for p in ps[1:]:
            if p == prev + 2:
                prev = p
            else:
                segs.append((L, start, prev))
                start = p
                prev = p
        segs.append((L, start, prev))
    out = [row[:] for row in g]
    for i, a in enumerate(segs):
        for b in segs[i + 1:]:
            if a[0] == b[0]:
                continue
            lo = max(a[1], b[1])
            hi = min(a[2], b[2])
            if lo > hi:
                continue
            l_lo = min(a[0], b[0])
            l_hi = max(a[0], b[0])
            for y in range(H):
                for x in range(W):
                    if g[y][x] != BG:
                        continue
                    L, P = _coords(y, x)
                    if l_lo < L < l_hi and lo <= P <= hi:
                        out[y][x] = FILL
    return out
''' % (bg, fill, anti)
    return src
