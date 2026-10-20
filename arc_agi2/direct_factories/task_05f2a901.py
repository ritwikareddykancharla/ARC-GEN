def build_program(d4, palette):
    bg = int(palette[0])
    mover = int(palette[2])
    anchor = int(palette[8])
    template = '''
BG = __BG__
MOVER = __MOVER__
ANCHOR = __ANCHOR__

def _bbox(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return min(ys), min(xs), max(ys), max(xs)

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    mcells = [(y, x) for y in range(H) for x in range(W) if g[y][x] == MOVER]
    acells = [(y, x) for y in range(H) for x in range(W) if g[y][x] == ANCHOR]
    if not mcells or not acells:
        return g
    my0, mx0, my1, mx1 = _bbox(mcells)
    ay0, ax0, ay1, ax1 = _bbox(acells)
    dy = 0
    dx = 0
    rows_overlap = not (my1 < ay0 or ay1 < my0)
    if rows_overlap:
        # shapes side by side: slide horizontally until bboxes touch
        if mx1 < ax0:
            dx = ax0 - 1 - mx1
        else:
            dx = ax1 + 1 - mx0
    else:
        # shapes stacked: slide vertically until bboxes touch
        if my1 < ay0:
            dy = ay0 - 1 - my1
        else:
            dy = ay1 + 1 - my0
    out = [row[:] for row in g]
    for y, x in mcells:
        out[y][x] = BG
    for y, x in mcells:
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W:
            out[ny][nx] = MOVER
    return out
'''
    return (template.replace('__BG__', str(bg))
                    .replace('__MOVER__', str(mover))
                    .replace('__ANCHOR__', str(anchor)))
