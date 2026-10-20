def build_program(d4, palette):
    B = int(palette[0])
    U = int(palette[1])
    G = int(palette[5])
    # The 3x3 stamp (grey corners, blue edge-middles, background centre) is
    # invariant under every D4 transform, so in visible coordinates the
    # geometry is the same for every d4. Only the colour roles change.
    src = '''import numpy as np

BG = %d
BLUE = %d
GREY = %d

EDGE_OFFSETS = ((-1, 0), (1, 0), (0, -1), (0, 1))
CORNER_OFFSETS = ((-1, -1), (-1, 1), (1, -1), (1, 1))

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    H, W = g.shape
    out = np.full((H, W), BG, dtype=int)
    seeds = [(int(r), int(c)) for r, c in zip(*np.nonzero(g == GREY))]
    for r, c in seeds:
        for dr, dc in EDGE_OFFSETS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < H and 0 <= cc < W:
                out[rr, cc] = BLUE
    for r, c in seeds:
        for dr, dc in CORNER_OFFSETS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < H and 0 <= cc < W:
                out[rr, cc] = GREY
    return out.tolist()
''' % (B, U, G)
    return src
