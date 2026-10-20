TEMPLATE = '''import numpy as np

BG = __BG__
FILL = __FILL__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    wall = g != BG
    ys, xs = np.nonzero(wall)
    if ys.size == 0:
        return out.tolist()
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    # 1. fill every background cell of the cup's bounding box (interior + gap)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if out[y, x] == BG:
                out[y, x] = FILL
    # each side: (cells along the wall, outward direction, along-wall direction)
    sides = [
        ([(y0, x) for x in range(x0, x1 + 1)], (-1, 0), (0, 1)),
        ([(y1, x) for x in range(x0, x1 + 1)], (1, 0), (0, 1)),
        ([(y, x0) for y in range(y0, y1 + 1)], (0, -1), (1, 0)),
        ([(y, x1) for y in range(y0, y1 + 1)], (0, 1), (1, 0)),
    ]
    best = None
    for cells, d, a in sides:
        gap = [i for i, (y, x) in enumerate(cells) if not wall[y, x]]
        if gap and (best is None or len(gap) > len(best[0])):
            best = (gap, cells, d, a)
    if best is None:
        return out.tolist()
    gap, cells, (dy, dx), (ay, ax) = best

    def ray(y, x, sy, sx):
        while 0 <= y < H and 0 <= x < W:
            if out[y, x] == BG:
                out[y, x] = FILL
            y += sy
            x += sx

    # 2. straight beam outward from every gap cell to the border
    for i in gap:
        y, x = cells[i]
        ray(y + dy, x + dx, dy, dx)
    # 3. two diagonals: start one step outward from the wall cell flanking the gap,
    #    then move outward + away from the gap
    s, e = min(gap), max(gap)
    for idx, sgn in ((s - 1, -1), (e + 1, 1)):
        if 0 <= idx < len(cells):
            by, bx = cells[idx]
        else:
            by, bx = cells[s] if sgn < 0 else cells[e]
            by += sgn * ay
            bx += sgn * ax
        ray(by + dy, bx + dx, dy + sgn * ay, dx + sgn * ax)
    return out.tolist()
'''


def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[4])
    return TEMPLATE.replace('__BG__', str(bg)).replace('__FILL__', str(fill))
