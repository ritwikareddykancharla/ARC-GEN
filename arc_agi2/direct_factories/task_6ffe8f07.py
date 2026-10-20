def build_program(d4, palette):
    # Rays leave all four sides of the anchor rectangle. Every D4 transform maps
    # the set {up, down, left, right} onto itself, and maps the rectangle's
    # columns/rows onto the visible rectangle's columns/rows. So the visible-
    # coordinate mechanism is the same for every d4; only colour roles change.
    anchor = int(palette[8])
    wall = int(palette[1])
    paint = int(palette[4])
    src = '''import numpy as np

ANCHOR = %d   # solid rectangle that emits the rays
WALL = %d     # blocker colour; a ray stops before it
PAINT = %d    # colour painted along each ray
D4_INDEX = %d # informational only: the four-way mechanism is D4-closed


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    cells = np.argwhere(g == ANCHOR)
    if len(cells) == 0:
        return g.tolist()
    y0, x0 = (int(v) for v in cells.min(0))
    y1, x1 = (int(v) for v in cells.max(0))

    def ray(y, x, dy, dx):
        y += dy
        x += dx
        while 0 <= y < H and 0 <= x < W:
            v = g[y, x]
            if v == WALL or v == ANCHOR:
                break
            g[y, x] = PAINT
            y += dy
            x += dx

    # Vertical rays: one per anchor column, from the top and bottom edges.
    for x in range(x0, x1 + 1):
        ray(y0, x, -1, 0)
        ray(y1, x, 1, 0)
    # Horizontal rays: one per anchor row, from the left and right edges.
    for y in range(y0, y1 + 1):
        ray(y, x0, 0, -1)
        ray(y, x1, 0, 1)
    return g.tolist()
''' % (anchor, wall, paint, int(d4))
    return src
