def build_program(d4, palette):
    # The legend strip is original row 0. A horizontal mirror (d4 >= 4) keeps it
    # as the top row. Each clockwise quarter turn then moves it:
    # top -> right -> bottom -> left.
    # The per-cell rewrite along a line does not depend on travel direction,
    # so only the side of the strip has to be specialised.
    # Colour roles (background and seed colours) are read from the visible
    # pixels, so the palette needs no constants.
    side = ['top', 'right', 'bottom', 'left'][int(d4) % 4]
    template = """import numpy as np
from collections import Counter

SIDE = '__SIDE__'


def _background(strip, rest):
    # The legend strip is mostly background, with a few sparse seed cells.
    cnt = Counter(int(v) for v in strip)
    best = max(cnt.values())
    cands = [c for c, n in cnt.items() if n == best]
    if len(cands) == 1:
        return cands[0]
    rc = Counter(int(v) for v in np.asarray(rest).ravel())
    return max(cands, key=lambda c: (rc.get(c, 0), -c))


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    if SIDE == 'top':
        strip = g[0, :]
        rest = g[1:, :]
    elif SIDE == 'bottom':
        strip = g[H - 1, :]
        rest = g[:H - 1, :]
    elif SIDE == 'left':
        strip = g[:, 0]
        rest = g[:, 1:]
    else:
        strip = g[:, W - 1]
        rest = g[:, :W - 1]
    bg = _background(strip, rest if rest.size else strip)
    for i in range(len(strip)):
        c = int(strip[i])
        if c == bg:
            continue
        # Draw a perpendicular line from the seed across the whole grid.
        # A cell of the seed colour becomes background (the line cuts a gap).
        # Every other cell becomes the seed colour.
        if SIDE == 'top':
            seg = g[1:, i]
            out[1:, i] = np.where(seg == c, bg, c)
        elif SIDE == 'bottom':
            seg = g[:H - 1, i]
            out[:H - 1, i] = np.where(seg == c, bg, c)
        elif SIDE == 'left':
            seg = g[i, 1:]
            out[i, 1:] = np.where(seg == c, bg, c)
        else:
            seg = g[i, :W - 1]
            out[i, :W - 1] = np.where(seg == c, bg, c)
    return out.tolist()
"""
    return template.replace('__SIDE__', side)
