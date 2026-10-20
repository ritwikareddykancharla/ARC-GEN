def build_program(d4, palette):
    marker = int(palette[0])
    src = '''import numpy as np
from collections import Counter

MARKER = %d

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    H, W = g.shape
    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    oh, ow = 3, 3
    bh, bw = H // oh, W // ow
    out = np.full((oh, ow), bg, dtype=int)
    for by in range(oh):
        for bx in range(ow):
            block = g[by * bh:(by + 1) * bh, bx * bw:(bx + 1) * bw]
            if np.any(block != bg):
                vals = block[block != bg]
                if np.any(vals == MARKER):
                    out[by, bx] = MARKER
                else:
                    out[by, bx] = int(np.bincount(vals).argmax())
    return out.tolist()
''' % marker
    return src
