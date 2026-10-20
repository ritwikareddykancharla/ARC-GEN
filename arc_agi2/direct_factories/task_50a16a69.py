def build_program(d4, palette):
    k = d4 % 4
    flip = d4 >= 4
    # Image of the original column-increase unit vector (0, +1).
    dr, dc = 0, 1
    # Original filler corner is bottom-right: (bottom=True, right=True).
    bottom, right = True, True
    if flip:
        dc = -dc
        right = not right
    for _ in range(k):
        # Clockwise rotation: (r, c) -> (c, H-1-r); vector (dr, dc) -> (dc, -dr)
        dr, dc = dc, -dr
        bottom, right = right, (not bottom)
    src = '''
DR = %d
DC = %d
CORNER_BOTTOM = %s
CORNER_RIGHT = %s


def solve(demonstrations, grid):
    g = [list(row) for row in grid]
    H = len(g)
    W = len(g[0])
    # The filler colour sits in the corner opposite the patterned block.
    fill = g[H - 1 if CORNER_BOTTOM else 0][W - 1 if CORNER_RIGHT else 0]
    ys = []
    xs = []
    for y in range(H):
        for x in range(W):
            if g[y][x] != fill:
                ys.append(y)
                xs.append(x)
    if not ys:
        return g
    r0, r1 = min(ys), max(ys)
    c0, c1 = min(xs), max(xs)
    block = [row[c0:c1 + 1] for row in g[r0:r1 + 1]]
    bh = len(block)
    bw = len(block[0])
    py = bh
    for p in range(1, bh + 1):
        if all(block[i] == block[i + p] for i in range(bh - p)):
            py = p
            break
    px = bw
    for p in range(1, bw + 1):
        ok = True
        for i in range(bh):
            row = block[i]
            for j in range(bw - p):
                if row[j] != row[j + p]:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            px = p
            break
    # Extend the tiling over the whole grid (anchored at the block) and
    # sample it one step further along the visible tiling-advance direction.
    out = [[0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            out[y][x] = block[(y + DR - r0) %% py][(x + DC - c0) %% px]
    return out
''' % (dr, dc, 'True' if bottom else 'False', 'True' if right else 'False')
    return src
