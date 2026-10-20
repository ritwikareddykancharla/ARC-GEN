def build_program(d4, palette):
    k = int(d4) % 4
    c_red = int(palette[2])
    c_yel = int(palette[4])
    c_div = int(palette[5])
    c_bg = int(palette[0])
    # Original divider is a full ROW; after an odd number of clockwise turns it is a full COLUMN.
    axis_rows = (k % 2 == 0)
    # The row reversal for d4>=4 does not move the top half. Clockwise turns move the
    # original top half to: k=0 top, k=1 right, k=2 bottom, k=3 left.
    # first_low is True when the original 'top' half has the lower indices.
    first_low = k in (0, 3)
    lines = []
    lines.append('AXIS_ROWS = ' + repr(axis_rows))
    lines.append('FIRST_LOW = ' + repr(first_low))
    lines.append('C_RED = ' + repr(c_red))
    lines.append('C_YEL = ' + repr(c_yel))
    lines.append('C_DIV = ' + repr(c_div))
    lines.append('C_BG = ' + repr(c_bg))
    body = '''

def _find_divider(g, H, W):
    if AXIS_ROWS:
        cands = [y for y in range(H) if all(g[y][x] == C_DIV for x in range(W))]
        mid = H // 2
    else:
        cands = [x for x in range(W) if all(g[y][x] == C_DIV for y in range(H))]
        mid = W // 2
    if not cands:
        return mid
    best = cands[0]
    for c in cands:
        if abs(c - mid) < abs(best - mid):
            best = c
    return best


def _count(g, H, W, colour, lo, hi):
    # Counts cells of colour in the band [lo, hi) along the split axis.
    n = 0
    if AXIS_ROWS:
        for y in range(max(lo, 0), min(hi, H)):
            for x in range(W):
                if g[y][x] == colour:
                    n += 1
    else:
        for y in range(H):
            for x in range(max(lo, 0), min(hi, W)):
                if g[y][x] == colour:
                    n += 1
    return n


def solve(demonstrations, grid):
    g = [list(r) for r in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    span = H if AXIS_ROWS else W
    d = _find_divider(g, H, W)
    low = (0, d)
    high = (d + 1, span)
    first, second = (low, high) if FIRST_LOW else (high, low)
    grow_red = _count(g, H, W, C_RED, second[0], second[1]) - _count(g, H, W, C_RED, first[0], first[1])
    grow_yel = _count(g, H, W, C_YEL, second[0], second[1]) - _count(g, H, W, C_YEL, first[0], first[1])
    if grow_red > grow_yel:
        win = C_RED
    elif grow_yel > grow_red:
        win = C_YEL
    else:
        # The generator never produces equal growth. This is a deterministic fallback, not a puzzle rule.
        win = C_RED
    return [[win, win], [win, win]]
'''
    return '\n'.join(lines) + body
