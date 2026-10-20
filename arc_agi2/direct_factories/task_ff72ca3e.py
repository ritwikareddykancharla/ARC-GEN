def build_program(d4, palette):
    # The mechanism (Chebyshev-distance squares centred on cells) is invariant
    # under every D4 transform, so d4 changes no geometry. Only colour roles are
    # specialised through the palette.
    bg = int(palette[0])
    red = int(palette[2])
    yellow = int(palette[4])
    grey = int(palette[5])
    src = '''import numpy as np

BG = %d
RED = %d
YELLOW = %d
GREY = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    centres = list(zip(*np.where(g == YELLOW)))
    blockers = list(zip(*np.where(g == GREY)))
    for y, x in centres:
        y = int(y); x = int(x)
        if blockers:
            d = min(max(abs(y - int(a)), abs(x - int(b))) for a, b in blockers)
        else:
            d = max(H, W)
        r = d - 1
        if r <= 0:
            continue
        y0 = max(0, y - r); y1 = min(H - 1, y + r)
        x0 = max(0, x - r); x1 = min(W - 1, x + r)
        region = out[y0:y1 + 1, x0:x1 + 1]
        region[region == BG] = RED
    return out.tolist()
''' % (bg, red, yellow, grey)
    return src
