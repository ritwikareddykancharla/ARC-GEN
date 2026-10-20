def build_program(d4, palette):
    # Track where the canonical directions land in visible coordinates.
    # down  = canonical +row (the stripe direction; the grey bar starts at canonical row 0)
    # right = canonical +col (from the grey bar toward the stripe block)
    down = (1, 0)
    right = (0, 1)
    if d4 >= 4:
        down = (down[0], -down[1])
        right = (right[0], -right[1])
    for _ in range(d4 % 4):
        # clockwise rotation: (r, c) -> (c, H-1-r), so (dr, dc) -> (dc, -dr)
        down = (down[1], -down[0])
        right = (right[1], -right[0])
    bg = int(palette[0])
    bar = int(palette[5])

    if down[1] == 0:
        # Stripes are visible COLUMNS; the block sits at the left or right edge.
        rs = right[1]
        ds = down[0]
        template = '''
BG = __BG__
BAR = __BAR__
RS = __RS__
DS = __DS__

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0])
    if RS == 1:
        xs = list(range(W - 1, -1, -1))
        bar_x = 0
    else:
        xs = list(range(W))
        bar_x = W - 1
    stripes = []
    for x in xs:
        col = [g[y][x] for y in range(H)]
        if col[0] != BG and all(v == col[0] for v in col):
            stripes.append(x)
        else:
            break
    if not stripes or len(stripes) >= W:
        return g
    ordered = sorted(stripes) if RS == 1 else sorted(stripes, reverse=True)
    colours = [g[0][x] for x in ordered]
    k = len(colours)
    L = sum(1 for y in range(H) if g[y][bar_x] == BAR)
    if L < 1:
        L = sum(1 for y in range(H) if g[y][bar_x] != BG)
    if L < 1:
        L = 1
    out = [row[:] for row in g]
    for x in stripes:
        for y in range(H):
            out[y][x] = BG
    tx = W - k - 1 if RS == 1 else k
    for y in range(H):
        t = y if DS == 1 else H - 1 - y
        out[y][tx] = colours[(t // L) % k]
    return out
'''
    else:
        # Stripes are visible ROWS; the block sits at the top or bottom edge.
        rs = right[0]
        ds = down[1]
        template = '''
BG = __BG__
BAR = __BAR__
RS = __RS__
DS = __DS__

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0])
    if RS == 1:
        ys = list(range(H - 1, -1, -1))
        bar_y = 0
    else:
        ys = list(range(H))
        bar_y = H - 1
    stripes = []
    for y in ys:
        line = g[y]
        if line[0] != BG and all(v == line[0] for v in line):
            stripes.append(y)
        else:
            break
    if not stripes or len(stripes) >= H:
        return g
    ordered = sorted(stripes) if RS == 1 else sorted(stripes, reverse=True)
    colours = [g[y][0] for y in ordered]
    k = len(colours)
    L = sum(1 for x in range(W) if g[bar_y][x] == BAR)
    if L < 1:
        L = sum(1 for x in range(W) if g[bar_y][x] != BG)
    if L < 1:
        L = 1
    out = [row[:] for row in g]
    for y in stripes:
        for x in range(W):
            out[y][x] = BG
    ty = H - k - 1 if RS == 1 else k
    for x in range(W):
        t = x if DS == 1 else W - 1 - x
        out[ty][x] = colours[(t // L) % k]
    return out
'''
    prog = template.replace('__BG__', str(bg)).replace('__BAR__', str(bar))
    prog = prog.replace('__RS__', str(int(rs))).replace('__DS__', str(int(ds)))
    return prog
