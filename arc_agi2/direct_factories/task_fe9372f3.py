def build_program(d4, palette):
    # The mechanism is invariant under every D4 transform. The plus is symmetric,
    # the four diagonal rays map onto diagonal rays, the four orthogonal rays map
    # onto orthogonal rays, and the 8,8,4 cadence depends only on the distance
    # from the centre. So d4 does not change any direction or axis. Only the
    # colour roles are specialised through the palette.
    P = [int(v) for v in palette]
    BG, PLUS, DIAG, MARK, FILL = P[0], P[2], P[1], P[4], P[8]
    src = '''import numpy as np

BG = %d
PLUS = %d
DIAG = %d
MARK = %d
FILL = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    ys, xs = np.nonzero(g == PLUS)
    if len(ys) == 0:
        ys, xs = np.nonzero(g != BG)
    if len(ys) == 0:
        return out.tolist()
    cy = (int(ys.min()) + int(ys.max())) // 2
    cx = (int(xs.min()) + int(xs.max())) // 2
    # Diagonal rays start one step from the centre and run to the border.
    for dy, dx in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        d = 1
        while 0 <= cy + dy * d < H and 0 <= cx + dx * d < W:
            y, x = cy + dy * d, cx + dx * d
            if out[y, x] == BG:
                out[y, x] = DIAG
            d += 1
    # Orthogonal rays continue each arm. Distance d%%3==1 gets MARK, else FILL.
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d = 2
        while 0 <= cy + dy * d < H and 0 <= cx + dx * d < W:
            y, x = cy + dy * d, cx + dx * d
            if out[y, x] == BG:
                out[y, x] = MARK if d %% 3 == 1 else FILL
            d += 1
    return out.tolist()
''' % (BG, PLUS, DIAG, MARK, FILL)
    return src
