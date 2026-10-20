def build_program(d4, palette):
    k = d4 % 4
    split_cols = (k % 2 == 1)
    bg = int(palette[0])
    fill = int(palette[3])
    div = int(palette[4])
    src = '''import numpy as np

BG = __BG__
FILL = __FILL__
DIV = __DIV__
SPLIT_COLS = __SPLIT__


def _split_rows(g):
    n = g.shape[0]
    cands = [y for y in range(n) if (g[y, :] == DIV).all()]
    if cands:
        r = min(cands, key=lambda t: (abs(t - (n - 1) / 2.0), t))
        a = g[:r, :]
        b = g[r + 1:, :]
    else:
        h = n // 2
        a = g[:h, :]
        b = g[n - h:, :]
    m = min(a.shape[0], b.shape[0])
    return a[:m, :], b[:m, :]


def _split_cols(g):
    n = g.shape[1]
    cands = [x for x in range(n) if (g[:, x] == DIV).all()]
    if cands:
        r = min(cands, key=lambda t: (abs(t - (n - 1) / 2.0), t))
        a = g[:, :r]
        b = g[:, r + 1:]
    else:
        h = n // 2
        a = g[:, :h]
        b = g[:, n - h:]
    m = min(a.shape[1], b.shape[1])
    return a[:, :m], b[:, :m]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    if SPLIT_COLS:
        a, b = _split_cols(g)
    else:
        a, b = _split_rows(g)
    out = np.full(a.shape, BG, dtype=int)
    out[(a != BG) | (b != BG)] = FILL
    return out.tolist()
'''
    src = src.replace('__BG__', repr(bg))
    src = src.replace('__FILL__', repr(fill))
    src = src.replace('__DIV__', repr(div))
    src = src.replace('__SPLIT__', 'True' if split_cols else 'False')
    return src
