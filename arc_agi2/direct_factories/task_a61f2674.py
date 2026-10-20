def build_program(d4, palette):
    k = d4 % 4
    bg = int(palette[0])
    bar = int(palette[5])
    c1 = int(palette[1])
    c2 = int(palette[2])
    # Original bars stand on the bottom edge. A row reversal keeps the bottom edge in place.
    # Each clockwise quarter turn moves that base edge: bottom -> left -> top -> right.
    if k == 0:
        axis, from_end = 'col', True
    elif k == 1:
        axis, from_end = 'row', False
    elif k == 2:
        axis, from_end = 'col', False
    else:
        axis, from_end = 'row', True
    src = '''
BG = %d
BAR = %d
C_TALL = %d
C_SHORT = %d
AXIS = %r
FROM_END = %r

def _line_cells(i, h, w):
    # Cells of line i, ordered starting from the base edge the bars stand on.
    if AXIS == 'col':
        ys = range(h - 1, -1, -1) if FROM_END else range(h)
        return [(y, i) for y in ys]
    xs = range(w - 1, -1, -1) if FROM_END else range(w)
    return [(i, x) for x in xs]

def solve(demonstrations, grid):
    g = [list(r) for r in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    out = [[BG] * w for _ in range(h)]
    n_lines = w if AXIS == 'col' else h
    bars = []
    for i in range(n_lines):
        cells = _line_cells(i, h, w)
        run = []
        for (y, x) in cells:
            if g[y][x] == BAR:
                run.append((y, x))
            else:
                break
        if run:
            bars.append((len(run), i, run))
    if not bars:
        return out
    tallest = max(bars, key=lambda b: b[0])
    shortest = min(bars, key=lambda b: b[0])
    for (y, x) in tallest[2]:
        out[y][x] = C_TALL
    for (y, x) in shortest[2]:
        out[y][x] = C_SHORT
    return out
''' % (bg, bar, c1, c2, axis, from_end)
    return src
