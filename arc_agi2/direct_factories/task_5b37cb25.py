PROGRAM = '''
import numpy as np
from collections import Counter


def _mode(vals):
    vals = [int(v) for v in vals]
    if not vals:
        return 0
    return Counter(vals).most_common(1)[0][0]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    if H < 5 or W < 5:
        return out.tolist()
    # Frame colours read from the visible edges (corners excluded).
    top = _mode(g[0, 1:W - 1].tolist())
    bottom = _mode(g[H - 1, 1:W - 1].tolist())
    left = _mode(g[1:H - 1, 0].tolist())
    right = _mode(g[1:H - 1, W - 1].tolist())
    # Background: the ring just inside the frame never holds blob cells.
    ring = (g[1, 1:W - 1].tolist() + g[H - 2, 1:W - 1].tolist()
            + g[1:H - 1, 1].tolist() + g[1:H - 1, W - 2].tolist())
    bg = _mode(ring)

    def inside(y, x):
        return 1 <= y <= H - 2 and 1 <= x <= W - 2

    def isbg(y, x):
        return inside(y, x) and g[y, x] == bg

    def isfg(y, x):
        return inside(y, x) and g[y, x] != bg

    # A notch opening in direction d (perpendicular p) centred at C:
    #   background: C, C+d (outer arm), C-d (inner arm), C+p, C-p
    #   blob wall : C-2d, C-d+p, C-d-p, C+2p, C-2p
    # The plus is painted with the colour of the frame side d faces.
    openings = (((-1, 0), top), ((1, 0), bottom), ((0, -1), left), ((0, 1), right))
    stamps = []
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if g[y, x] != bg:
                continue
            for (dy, dx), col in openings:
                py, px = dx, dy
                hole = (isbg(y + dy, x + dx) and isbg(y - dy, x - dx)
                        and isbg(y + py, x + px) and isbg(y - py, x - px))
                if not hole:
                    continue
                walls = (isfg(y - 2 * dy, x - 2 * dx)
                         and isfg(y - dy + py, x - dx + px)
                         and isfg(y - dy - py, x - dx - px)
                         and isfg(y + 2 * py, x + 2 * px)
                         and isfg(y - 2 * py, x - 2 * px))
                if walls:
                    stamps.append((y, x, col))
    painted = {}
    for cy, cx, col in stamps:
        for dy, dx in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            target = (cy + dy, cx + dx)
            if target in painted and painted[target] != col:
                raise ValueError("Overlapping stamps specify different colours")
            painted[target] = col
            out[cy + dy, cx + dx] = col
    return out.tolist()
'''


def build_program(d4, palette):
    # The notch template is written for all four opening directions in
    # visible coordinates. Each direction is tied to the visible frame side it
    # faces. Background, blob and frame colours are read from pixels. Every
    # D4 element permutes the four (direction, side) pairs together, and the
    # palette only renames colours that are read from the grid, so no constant
    # needs specialising.
    d4 = int(d4) % 8
    _ = [int(c) for c in palette]
    return PROGRAM
