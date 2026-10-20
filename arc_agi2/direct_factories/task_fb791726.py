def build_program(d4, palette):
    import numpy as np
    k = d4 % 4
    flip = d4 >= 4
    # The original copies sit in quadrants (0,0) and (1,1) of the 2x2 block layout.
    # The D4 map permutes blocks the same way it moves the cells of a 2x2 matrix.
    m = np.array([[1, 0], [0, 1]])
    if flip:
        m = m[:, ::-1]
    m = np.rot90(m, -k)
    quads = [(int(i), int(j)) for i, j in zip(*np.nonzero(m))]
    vertical = (k % 2 == 0)
    bg = int(palette[0])
    line = int(palette[3])
    src = '''import numpy as np

BG = %d
LINE = %d
QUADS = %r
VERTICAL = %r


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = np.full((2 * h, 2 * w), BG, dtype=int)
    for qi, qj in QUADS:
        out[qi * h:(qi + 1) * h, qj * w:(qj + 1) * w] = g
    H, W = out.shape
    if VERTICAL:
        rows = set()
        for y in range(H - 2):
            for x in range(W):
                c = out[y, x]
                if c != BG and out[y + 2, x] == c and out[y + 1, x] == BG:
                    rows.add(y + 1)
        for r in sorted(rows):
            out[r, :] = LINE
    else:
        cols = set()
        for x in range(W - 2):
            for y in range(H):
                c = out[y, x]
                if c != BG and out[y, x + 2] == c and out[y, x + 1] == BG:
                    cols.add(x + 1)
        for cc in sorted(cols):
            out[:, cc] = LINE
    return out.tolist()
''' % (bg, line, quads, vertical)
    return src
