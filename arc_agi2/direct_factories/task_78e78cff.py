PROGRAM = '''import numpy as np


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    vals, cnts = np.unique(g, return_counts=True)
    bg = int(vals[np.argmax(cnts)])
    others = [(int(c), int(n)) for c, n in zip(vals.tolist(), cnts.tolist()) if int(c) != bg]
    if len(others) < 2:
        return g.tolist()
    others.sort(key=lambda t: (t[1], t[0]))
    marker = others[0][0]
    fmask = (g != bg) & (g != marker)
    ys, xs = np.nonzero(fmask)
    if len(ys) == 0:
        return g.tolist()
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    out = g.copy()

    def paint(ya, yb, xa, xb):
        if ya > yb or xa > xb:
            return
        reg = out[ya:yb + 1, xa:xb + 1]
        reg[reg == bg] = marker

    # interior of the frame becomes the marker colour
    paint(y0 + 1, y1 - 1, x0 + 1, x1 - 1)
    # gaps in the top side leak upward to the grid edge (gap cell included)
    for x in range(x0 + 1, x1):
        if g[y0, x] == bg:
            paint(0, y0, x, x)
    # gaps in the bottom side leak downward
    for x in range(x0 + 1, x1):
        if g[y1, x] == bg:
            paint(y1, H - 1, x, x)
    # gaps in the left side leak leftward
    for y in range(y0 + 1, y1):
        if g[y, x0] == bg:
            paint(y, y, 0, x0)
    # gaps in the right side leak rightward
    for y in range(y0 + 1, y1):
        if g[y, x1] == bg:
            paint(y, y, x1, W - 1)
    return out.tolist()
'''


def build_program(d4, palette):
    # The mechanism maps to itself under every D4 element. The four side-leak
    # directions are permuted among themselves, and the frame bounding box
    # stays a bounding box. Colour roles are read from visible pixel counts:
    # background is the most common colour, the marker is the rarest
    # non-background colour, and the frame is the remaining colour. So the
    # program needs no d4 or palette constants and works directly in visible
    # coordinates.
    return PROGRAM
