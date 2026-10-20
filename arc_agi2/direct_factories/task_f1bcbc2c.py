def build_program(d4, palette):
    side = ('top', 'right', 'bottom', 'left')[d4 % 4]
    bg = int(palette[0])
    wall = int(palette[7])
    plug = int(palette[9])
    paint = int(palette[8])
    template = """import numpy as np

BG = __BG__
WALL = __WALL__
PLUG = __PLUG__
PAINT = __PAINT__
START_SIDE = '__SIDE__'
SIDES = ('top', 'right', 'bottom', 'left')


def _openings(g, side):
    H, W = g.shape
    out = []
    if side in ('top', 'bottom'):
        if H < 2 or W < 3:
            return out
        y = 0 if side == 'top' else H - 1
        iy = 1 if side == 'top' else H - 2
        for x in range(1, W - 1):
            if g[y, x] == BG and g[y, x - 1] == WALL and g[y, x + 1] == WALL:
                out.append(((y, x), 0 if g[iy, x] in (BG, PLUG) else 1))
    else:
        if W < 2 or H < 3:
            return out
        x = 0 if side == 'left' else W - 1
        ix = 1 if side == 'left' else W - 2
        for y in range(1, H - 1):
            if g[y, x] == BG and g[y - 1, x] == WALL and g[y + 1, x] == WALL:
                out.append(((y, x), 0 if g[y, ix] in (BG, PLUG) else 1))
    out.sort(key=lambda t: t[1])
    return [p for p, _ in out]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    order = [START_SIDE] + [s for s in SIDES if s != START_SIDE]
    start = None
    for s in order:
        cands = _openings(g, s)
        if cands:
            start = cands[0]
            break
    if start is None:
        return g.tolist()
    visited = {start}
    g[start] = PAINT
    cur = start
    while True:
        nxt = None
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cur[0] + dy, cur[1] + dx
            if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in visited and g[ny, nx] in (BG, PLUG):
                nxt = (ny, nx, dy, dx)
                break
        if nxt is None:
            break
        ny, nx, dy, dx = nxt
        if g[ny, nx] == PLUG:
            by, bx = ny + dy, nx + dx
            if not (0 <= by < H and 0 <= bx < W and g[by, bx] == BG):
                break
        g[ny, nx] = PAINT
        visited.add((ny, nx))
        cur = (ny, nx)
    return g.tolist()
"""
    return (template.replace('__BG__', repr(bg))
                    .replace('__WALL__', repr(wall))
                    .replace('__PLUG__', repr(plug))
                    .replace('__PAINT__', repr(paint))
                    .replace('__SIDE__', side))
