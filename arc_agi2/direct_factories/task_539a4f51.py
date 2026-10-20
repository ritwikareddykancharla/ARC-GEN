def build_program(d4, palette):
    corners = ['TL', 'TR', 'BR', 'BL']
    start = 1 if d4 >= 4 else 0
    corner = corners[(start + (d4 % 4)) % 4]
    top = corner in ('TL', 'TR')
    left = corner in ('TL', 'BL')
    bg = int(palette[0])
    src = '''import numpy as np

TOP = %r
LEFT = %r
BG = %d

def _dist(r, c, H, W):
    dr = r if TOP else H - 1 - r
    dc = c if LEFT else W - 1 - c
    return max(dr, dc)

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    n = min(H, W)
    layers = []
    for k in range(n):
        r = k if TOP else H - 1 - k
        c = k if LEFT else W - 1 - k
        layers.append(int(g[r, c]))
    seq = [v for v in layers if v != BG]
    if not seq:
        seq = layers
    p = len(seq)
    OH, OW = 2 * H, 2 * W
    out = np.zeros((OH, OW), dtype=int)
    for r in range(OH):
        for c in range(OW):
            out[r, c] = seq[_dist(r, c, OH, OW) %% p]
    return out.tolist()
''' % (top, left, bg)
    return src
