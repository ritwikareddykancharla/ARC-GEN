def build_program(d4, palette):
    k = int(d4) % 4
    # The original divider is a full-height column. An odd number of clockwise
    # quarter turns makes it a full-width row. A row reversal (d4>=4) keeps it a
    # column. Under any D4 map, the two panels stay related by a pure
    # translation across the divider, so the cell-wise pairing is still
    # 'same offset within each half'.
    divider_is_row = (k % 2 == 1)
    bg = int(palette[0])
    div = int(palette[1])
    mark = int(palette[3])
    src = '''import numpy as np

BG = %d
DIV = %d
MARK = %d
DIVIDER_IS_ROW = %s


def _pick(cands, n):
    for x in cands:
        if 2 * x + 1 == n:
            return x
    if cands:
        return cands[0]
    return n // 2


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    if DIVIDER_IS_ROW:
        n = g.shape[0]
        cands = [y for y in range(n) if np.all(g[y, :] == DIV)]
        y = _pick(cands, n)
        a = g[:y, :]
        b = g[y + 1:, :]
    else:
        n = g.shape[1]
        cands = [x for x in range(n) if np.all(g[:, x] == DIV)]
        x = _pick(cands, n)
        a = g[:, :x]
        b = g[:, x + 1:]
    h = min(a.shape[0], b.shape[0])
    w = min(a.shape[1], b.shape[1])
    a = a[:h, :w]
    b = b[:h, :w]
    out = np.full((h, w), BG, dtype=int)
    out[(a == BG) & (b == BG)] = MARK
    return out.tolist()
''' % (bg, div, mark, 'True' if divider_is_row else 'False')
    return src
