def build_program(d4, palette):
    # The mechanism is symmetric under D4: horizontal dividers count output rows
    # and vertical dividers count output columns, both in visible coordinates.
    # A rotation swaps the two divider families, and that swaps the output
    # dimensions in exactly the way the transformed label expects.
    # Colour roles are read from the pixels. Every grid corner lies inside a
    # background panel, so a corner gives the background. That stays true
    # under any D4 transform and any palette.
    prog = '''
import numpy as np

def _bands(divs, length):
    bounds = [-1] + sorted(divs) + [length]
    return sum(1 for a, b in zip(bounds, bounds[1:]) if b - a > 1)

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    H, W = g.shape
    corners = [int(g[0, 0]), int(g[0, W - 1]), int(g[H - 1, 0]), int(g[H - 1, W - 1])]
    bg = max(set(corners), key=corners.count)
    row_divs = [y for y in range(H) if g[y, 0] != bg and np.all(g[y] == g[y, 0])]
    col_divs = [x for x in range(W) if g[0, x] != bg and np.all(g[:, x] == g[0, x])]
    nr = max(1, _bands(row_divs, H))
    nc = max(1, _bands(col_divs, W))
    return np.full((nr, nc), bg, dtype=int).tolist()
'''
    return prog
