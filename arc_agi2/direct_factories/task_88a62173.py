def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np
from collections import Counter

BG = %d

def _panels(g):
    H, W = g.shape
    # Fixed geometry: one separator line through the middle in each axis.
    # The geometry is symmetric under every D4 transform, so the panel
    # bounds do not depend on the orientation.
    sr = H // 2
    sc = W // 2
    row_spans = [(0, sr), (sr + 1, H)]
    col_spans = [(0, sc), (sc + 1, W)]
    pans = []
    for r0, r1 in row_spans:
        for c0, c1 in col_spans:
            if r1 > r0 and c1 > c0:
                pans.append(g[r0:r1, c0:c1].copy())
    return pans

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    pans = _panels(g)
    if not pans:
        return g.tolist()
    keys = [tuple(map(tuple, p.tolist())) for p in pans]
    cnt = Counter(keys)
    for k, p in zip(keys, pans):
        if cnt[k] == 1:
            return p.tolist()
    # Degenerate case, which the generator cannot produce: no unique panel.
    return pans[0].tolist()
''' % bg
    return src
