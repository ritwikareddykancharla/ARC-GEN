def build_program(d4, palette):
    black = int(palette[0])
    src = '''import numpy as np

BLACK = __BLACK__


def _line_label(values):
    for v in values:
        if int(v) != BLACK:
            return int(v)
    return -1


def _lines_uniform(lines):
    for line in lines:
        vals = set(int(v) for v in line if int(v) != BLACK)
        if len(vals) > 1:
            return False
    return True


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    blacks = [(y, x) for y in range(H) for x in range(W) if g[y, x] == BLACK]
    rows = [g[y, :] for y in range(H)]
    cols = [g[:, x] for x in range(W)]
    if _lines_uniform(rows):
        # Horizontal bands: each black cell becomes a vertical segment
        # spanning its band's rows in its own column.
        lab = [_line_label(r) for r in rows]
        for y, x in blacks:
            y0 = y
            while y0 - 1 >= 0 and lab[y0 - 1] == lab[y]:
                y0 -= 1
            y1 = y
            while y1 + 1 < H and lab[y1 + 1] == lab[y]:
                y1 += 1
            out[y0:y1 + 1, x] = BLACK
    else:
        # Vertical bands: each black cell becomes a horizontal segment
        # spanning its band's columns in its own row.
        lab = [_line_label(c) for c in cols]
        for y, x in blacks:
            x0 = x
            while x0 - 1 >= 0 and lab[x0 - 1] == lab[x]:
                x0 -= 1
            x1 = x
            while x1 + 1 < W and lab[x1 + 1] == lab[x]:
                x1 += 1
            out[y, x0:x1 + 1] = BLACK
    return out.tolist()
'''
    return src.replace('__BLACK__', str(black))
