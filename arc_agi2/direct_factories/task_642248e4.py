TEMPLATE = '''BG = __BG__
PIX = __PIX__


def _uniform(line):
    vals = set(line)
    if len(vals) != 1:
        return False
    v = line[0]
    return v != BG and v != PIX


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    out = [row[:] for row in g]
    if h == 0 or w == 0:
        return out
    top_line = g[0]
    bottom_line = g[h - 1]
    left_line = [g[y][0] for y in range(h)]
    right_line = [g[y][w - 1] for y in range(h)]
    horizontal = _uniform(top_line) and _uniform(bottom_line)
    if horizontal:
        c1 = g[0][0]
        c2 = g[h - 1][0]
        span = h - 1
    else:
        c1 = g[0][0]
        c2 = g[0][w - 1]
        span = w - 1
    pts = [(y, x) for y in range(h) for x in range(w) if g[y][x] == PIX]
    for which, col in ((0, c1), (1, c2)):
        for y, x in pts:
            p = y if horizontal else x
            d1 = p
            d2 = span - p
            near = 0 if d1 <= d2 else 1
            if near != which:
                continue
            step = -1 if near == 0 else 1
            if horizontal:
                ny, nx = y + step, x
            else:
                ny, nx = y, x + step
            if 0 <= ny < h and 0 <= nx < w and out[ny][nx] == BG:
                out[ny][nx] = col
    return out
'''


def build_program(d4, palette):
    bg = int(palette[0])
    pix = int(palette[1])
    return TEMPLATE.replace('__BG__', str(bg)).replace('__PIX__', str(pix))
