def build_program(d4, palette):
    k = d4 % 4
    # Canonical stacking: four equal layers along rows (axis 0), layer 0 (colour 5) at top.
    # A horizontal row reversal (d4>=4) does not change vertical stacking order.
    # Each clockwise rotation moves the stack: k=1 -> columns, layer 0 at right;
    # k=2 -> rows, layer 0 at bottom; k=3 -> columns, layer 0 at left.
    axis = 0 if k in (0, 2) else 1
    rev = k in (1, 2)
    bg = int(palette[0])
    # paint order low->high priority: layer2 (colour 2), layer3 (8), layer1 (4), layer0 (5)
    order = [2, 3, 1, 0]
    src = '''import numpy as np

AXIS = %d
REV = %r
BG = %d
ORDER = %r

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    if AXIS == 0:
        n = g.shape[0] // 4
        chunks = [g[i * n:(i + 1) * n, :] for i in range(4)]
    else:
        n = g.shape[1] // 4
        chunks = [g[:, i * n:(i + 1) * n] for i in range(4)]
    if REV:
        chunks = chunks[::-1]
    out = np.full(chunks[0].shape, BG, dtype=int)
    for i in ORDER:
        L = chunks[i]
        m = L != BG
        out[m] = L[m]
    return out.tolist()
''' % (axis, rev, bg, order)
    return src
