_PICK = '''
def _pick(lst, n):
    # lst: list of (length, line_index, cells). Rank by total length, tallest first.
    lst = sorted(lst, key=lambda t: -t[0])
    if not (1 <= n <= len(lst)):
        return None
    h = lst[n - 1][0]
    # Height ties make the rank ambiguous (outside the constructor domain): do nothing.
    if sum(1 for t in lst if t[0] == h) > 1:
        return None
    return lst[n - 1]
'''

_VERT = '''
def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    if H == 0 or W == 0:
        return out
    # Legend strips hang from row lr and run along direction d.
    # Bars stand on the opposite row br and grow in direction -d.
    if LEG_FIRST:
        lr, d = 0, 1
    else:
        lr, d = H - 1, -1
    br = H - 1 - lr
    legend = {}
    for x in range(W):
        c = g[lr][x]
        if c == BG:
            continue
        n = 0
        r = lr
        while 0 <= r < H and g[r][x] == c:
            n += 1
            r += d
        legend[c] = n
    bars = {}
    for x in range(W):
        c = g[br][x]
        if c == BG:
            continue
        cells = []
        r = br
        while 0 <= r < H and g[r][x] != BG:
            cells.append(r)
            r -= d
        bars.setdefault(c, []).append((len(cells), x, cells))
    for c, n in legend.items():
        p = _pick(bars.get(c, []), n)
        if p is None:
            continue
        x = p[1]
        for r in p[2]:
            out[r][x] = c
    return out
'''

_HORZ = '''
def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    if H == 0 or W == 0:
        return out
    # Legend strips hang from column lc and run along direction d.
    # Bars stand on the opposite column bc and grow in direction -d.
    if LEG_FIRST:
        lc, d = 0, 1
    else:
        lc, d = W - 1, -1
    bc = W - 1 - lc
    legend = {}
    for y in range(H):
        c = g[y][lc]
        if c == BG:
            continue
        n = 0
        x = lc
        while 0 <= x < W and g[y][x] == c:
            n += 1
            x += d
        legend[c] = n
    bars = {}
    for y in range(H):
        c = g[y][bc]
        if c == BG:
            continue
        cells = []
        x = bc
        while 0 <= x < W and g[y][x] != BG:
            cells.append(x)
            x -= d
        bars.setdefault(c, []).append((len(cells), y, cells))
    for c, n in legend.items():
        p = _pick(bars.get(c, []), n)
        if p is None:
            continue
        y = p[1]
        for x in p[2]:
            out[y][x] = c
    return out
'''


def build_program(d4, palette):
    k = int(d4) % 4
    bg = int(palette[0])
    # Original 'down' (legend -> bars) maps under clockwise rotations to:
    # k=0 down, k=1 left, k=2 up, k=3 right. Row reversal leaves it unchanged.
    if k % 2 == 0:
        first = (k == 0)   # legend on top row (k=0) or bottom row (k=2)
        body = _VERT
    else:
        first = (k == 3)   # legend on left column (k=3) or right column (k=1)
        body = _HORZ
    header = 'BG = %d\nLEG_FIRST = %s\n' % (bg, 'True' if first else 'False')
    return header + _PICK + body
