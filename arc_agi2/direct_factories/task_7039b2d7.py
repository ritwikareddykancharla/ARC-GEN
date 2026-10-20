def build_program(d4, palette):
    # The panel-count mechanism is invariant in visible coordinates:
    # every D4 transform maps full divider rows/columns to full divider
    # rows/columns. An odd rotation swaps the axes, and the output shape
    # (row panels x column panels) swaps in the same way. Colour roles are
    # inferred from pixels, so no palette constants are needed.
    d4 = int(d4) % 8
    body = '''
import numpy as np
from collections import Counter


def _background(g):
    # The divider colour fills at least one complete row or column.
    # The background never does, because both axes always carry a divider.
    H, W = g.shape
    counts = Counter(int(v) for v in g.ravel().tolist())
    colours = sorted(counts)
    if len(colours) == 1:
        return colours[0]
    line_colours = set()
    for y in range(H):
        if np.all(g[y, :] == g[y, 0]):
            line_colours.add(int(g[y, 0]))
    for x in range(W):
        if np.all(g[:, x] == g[0, x]):
            line_colours.add(int(g[0, x]))
    others = [c for c in colours if c not in line_colours]
    pool = others if others else colours
    return max(pool, key=lambda c: (counts[c], -c))


def _count_runs(flags):
    # Count the maximal runs of non-divider indices.
    n = 0
    prev = True
    for f in flags:
        if (not f) and prev:
            n += 1
        prev = f
    return n


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    if g.ndim != 2 or g.size == 0:
        return [[0]]
    H, W = g.shape
    bg = int(_background(g))
    div_r = [bool(np.all(g[y, :] != bg)) for y in range(H)]
    div_c = [bool(np.all(g[:, x] != bg)) for x in range(W)]
    nr = max(_count_runs(div_r), 1)
    nc = max(_count_runs(div_c), 1)
    return [[bg for _ in range(nc)] for _ in range(nr)]
'''
    return '# direct-coordinate panel counter (d4=' + str(d4) + ')' + body
