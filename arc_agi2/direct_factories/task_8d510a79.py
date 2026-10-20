def build_program(d4, palette):
    bg = int(palette[0])
    one = int(palette[1])
    two = int(palette[2])
    div = int(palette[5])
    horizontal_divider = (int(d4) % 4) in (0, 2)
    head = (
        "import numpy as np\n"
        "BG = %d\n"
        "ONE = %d\n"
        "TWO = %d\n"
        "DIV = %d\n"
    ) % (bg, one, two, div)
    if horizontal_divider:
        body = '''
def _find_divider(g):
    H, W = g.shape
    for y in range(H):
        if np.all(g[y, :] == DIV):
            return y
    for y in range(H):
        if g[y, 0] != BG and np.all(g[y, :] == g[y, 0]):
            return y
    return None

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    d = _find_divider(g)
    if d is None:
        return out.tolist()
    for y in range(H):
        if y == d:
            continue
        toward = 1 if y < d else -1
        for x in range(W):
            c = int(g[y, x])
            if c == TWO:
                step = toward
            elif c == ONE:
                step = -toward
            else:
                continue
            yy = y + step
            while 0 <= yy < H and out[yy, x] == BG:
                out[yy, x] = c
                yy += step
    return out.tolist()
'''
    else:
        body = '''
def _find_divider(g):
    H, W = g.shape
    for x in range(W):
        if np.all(g[:, x] == DIV):
            return x
    for x in range(W):
        if g[0, x] != BG and np.all(g[:, x] == g[0, x]):
            return x
    return None

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    d = _find_divider(g)
    if d is None:
        return out.tolist()
    for x in range(W):
        if x == d:
            continue
        toward = 1 if x < d else -1
        for y in range(H):
            c = int(g[y, x])
            if c == TWO:
                step = toward
            elif c == ONE:
                step = -toward
            else:
                continue
            xx = x + step
            while 0 <= xx < W and out[y, xx] == BG:
                out[y, xx] = c
                xx += step
    return out.tolist()
'''
    return head + body
