PROGRAM_TEMPLATE = '''import numpy as np

MASK = __MASK__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    h, w = g.shape
    known = g != MASK

    def partners(y, x):
        # Mirror partners in visible coordinates: left-right, up-down, 180 rotation.
        c = [(y, w - 1 - x), (h - 1 - y, x), (h - 1 - y, w - 1 - x)]
        if h == w:
            # Square canvas: diagonal / anti-diagonal mirrors and quarter turns.
            c += [(x, y), (x, h - 1 - y), (w - 1 - x, y), (w - 1 - x, h - 1 - y)]
        return c

    changed = True
    while changed:
        changed = False
        for y in range(h):
            for x in range(w):
                if known[y, x]:
                    continue
                for py, px in partners(y, x):
                    if 0 <= py < h and 0 <= px < w and known[py, px]:
                        g[y, x] = g[py, px]
                        known[y, x] = True
                        changed = True
                        break
    return g.tolist()
'''


def build_program(d4, palette):
    mask = int(palette[4])
    return PROGRAM_TEMPLATE.replace('__MASK__', str(mask))
