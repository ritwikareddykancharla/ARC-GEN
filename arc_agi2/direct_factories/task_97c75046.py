def build_program(d4, palette):
    bg = int(palette[7])
    shape_c = int(palette[0])
    ball = int(palette[5])
    template = '''import numpy as np

BG = __BG__
SHAPE = __SHAPE__
BALL = __BALL__


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [list(row) for row in g]
    pos = [(r, c) for r in range(H) for c in range(W) if g[r][c] == BALL]
    if len(pos) != 1:
        return out
    y, x = pos[0]
    shape = [[g[r][c] == SHAPE for c in range(W)] for r in range(H)]

    def inside(a, b):
        return 0 <= a < H and 0 <= b < W

    def touches(a, b):
        for ey in (-1, 0, 1):
            for ex in (-1, 0, 1):
                aa, bb = a + ey, b + ex
                if inside(aa, bb) and shape[aa][bb]:
                    return True
        return False

    def valid(a, b):
        return inside(a, b) and not shape[a][b] and touches(a, b)

    # Approach direction: the row/column ray from the ball that meets the shape.
    best = None
    d = None
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a, b, k = y + dy, x + dx, 1
        while inside(a, b):
            if shape[a][b]:
                if best is None or k < best:
                    best, d = k, (dy, dx)
                break
            a += dy
            b += dx
            k += 1
    if d is None:
        return out
    dy, dx = d
    out[y][x] = BG
    # Straight run until the next cell is shape.
    while inside(y + dy, x + dx) and not shape[y + dy][x + dx]:
        y += dy
        x += dx
    # Sideways diagonals: forward plus one perpendicular side.
    sides = [(dx, dy), (-dx, -dy)]
    options = [(py, px) for py, px in sides if valid(y + dy + py, x + dx + px)]
    if len(options) == 1:
        sy = dy + options[0][0]
        sx = dx + options[0][1]
        while valid(y + sy, x + sx):
            y += sy
            x += sx
    out[y][x] = BALL
    return out
'''
    return (template.replace('__BG__', str(bg))
            .replace('__SHAPE__', str(shape_c))
            .replace('__BALL__', str(ball)))
