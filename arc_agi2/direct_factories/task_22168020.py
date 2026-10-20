def build_program(d4, palette):
    bg = int(palette[0])
    vertical = (d4 % 4) in (1, 3)
    if not vertical:
        body = '''
def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    out = [row[:] for row in g]
    BG = %d
    for y in range(h):
        pos = {}
        for x in range(w):
            c = g[y][x]
            if c == BG:
                continue
            if c in pos:
                lo, hi = pos[c]
                pos[c] = (min(lo, x), max(hi, x))
            else:
                pos[c] = (x, x)
        for c, (lo, hi) in pos.items():
            if hi > lo:
                for x in range(lo, hi + 1):
                    if out[y][x] == BG:
                        out[y][x] = c
    return out
''' % bg
    else:
        body = '''
def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    out = [row[:] for row in g]
    BG = %d
    for x in range(w):
        pos = {}
        for y in range(h):
            c = g[y][x]
            if c == BG:
                continue
            if c in pos:
                lo, hi = pos[c]
                pos[c] = (min(lo, y), max(hi, y))
            else:
                pos[c] = (y, y)
        for c, (lo, hi) in pos.items():
            if hi > lo:
                for y in range(lo, hi + 1):
                    if out[y][x] == BG:
                        out[y][x] = c
    return out
''' % bg
    return body
