def build_program(d4, palette):
    bg = int(palette[0])
    fg = int(palette[5])
    src = '''import numpy as np

BG = %d
FG = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = np.full((5 * h, 5 * w), BG, dtype=int)
    cells = [(r, c) for r in range(h) for c in range(w) if g[r, c] != BG]
    # Core: the input scaled by the tile size, placed at tile offset (1,1).
    for r, c in cells:
        out[(r + 1) * h:(r + 2) * h, (c + 1) * w:(c + 2) * w] = int(g[r, c])
    # Ring: each filled core tile on a core edge emits one copy of the input
    # into the adjacent outer tile, once for each side of the core it touches.
    for r, c in cells:
        dirs = []
        if r == 0:
            dirs.append((-1, 0))
        if r == h - 1:
            dirs.append((1, 0))
        if c == 0:
            dirs.append((0, -1))
        if c == w - 1:
            dirs.append((0, 1))
        for dr, dc in dirs:
            tr, tc = r + 1 + dr, c + 1 + dc
            out[tr * h:(tr + 1) * h, tc * w:(tc + 1) * w] = g
    return out.tolist()
''' % (bg, fg)
    return src
