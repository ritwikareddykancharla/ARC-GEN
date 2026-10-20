def build_program(d4, palette):
    one = int(palette[1])
    eight = int(palette[8])
    head = '''import numpy as np
from collections import Counter

ONE = __ONE__
EIGHT = __EIGHT__
'''
    if d4 % 2 == 0:
        body = '''
def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    c = int(np.argmax((g == EIGHT).sum(axis=0)))
    lines = []
    for y in range(H):
        if g[y, c] == ONE:
            cnt = Counter(int(v) for v in g[y, :] if v != ONE)
            if cnt:
                lines.append((y, cnt.most_common(1)[0][0]))
    out = np.full((H, W), ONE, dtype=int)
    if lines:
        for y in range(H):
            d = min(abs(y - ly) for ly, _ in lines)
            cols = set(col for ly, col in lines if abs(y - ly) == d)
            if len(cols) == 1:
                out[y, :] = cols.pop()
    out[:, c] = ONE
    for ly, _ in lines:
        out[ly, :] = ONE
        out[ly, c] = EIGHT
    return out.tolist()
'''
    else:
        body = '''
def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    r = int(np.argmax((g == EIGHT).sum(axis=1)))
    lines = []
    for x in range(W):
        if g[r, x] == ONE:
            cnt = Counter(int(v) for v in g[:, x] if v != ONE)
            if cnt:
                lines.append((x, cnt.most_common(1)[0][0]))
    out = np.full((H, W), ONE, dtype=int)
    if lines:
        for x in range(W):
            d = min(abs(x - lx) for lx, _ in lines)
            cols = set(col for lx, col in lines if abs(x - lx) == d)
            if len(cols) == 1:
                out[:, x] = cols.pop()
    out[r, :] = ONE
    for lx, _ in lines:
        out[:, lx] = ONE
        out[r, lx] = EIGHT
    return out.tolist()
'''
    return (head + body).replace('__ONE__', str(one)).replace('__EIGHT__', str(eight))
