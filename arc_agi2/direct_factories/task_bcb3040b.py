def build_program(d4, palette):
    mark = int(palette[2])
    zero = int(palette[0])
    one = int(palette[1])
    cross = int(palette[3])
    header = (
        'MARK = ' + repr(mark) + '\n'
        'ZERO = ' + repr(zero) + '\n'
        'ONE = ' + repr(one) + '\n'
        'CROSS = ' + repr(cross) + '\n'
    )
    body = '''

def _sign(v):
    return (v > 0) - (v < 0)


def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    out = [row[:] for row in g]
    h = len(g)
    w = len(g[0]) if h else 0
    pts = [(r, c) for r in range(h) for c in range(w) if g[r][c] == MARK]
    if len(pts) < 2:
        return out
    pts.sort()
    (y0, x0), (y1, x1) = pts[0], pts[-1]
    dy = _sign(y1 - y0)
    dx = _sign(x1 - x0)
    n = max(abs(y1 - y0), abs(x1 - x0))
    for k in range(1, n):
        y = y0 + k * dy
        x = x0 + k * dx
        if not (0 <= y < h and 0 <= x < w):
            break
        v = g[y][x]
        if v == ZERO:
            out[y][x] = MARK
        elif v == ONE:
            out[y][x] = CROSS
    return out
'''
    return header + body
