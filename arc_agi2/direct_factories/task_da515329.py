def build_program(d4, palette):
    bg = int(palette[0])
    fg = int(palette[8])
    mirrored = int(d4) >= 4
    template = '''
BG = __BG__
FG = __FG__
MIRROR = __MIRROR__


def _outer_turn(d):
    # The spiral's main turning sense in visible coordinates:
    # clockwise for pure rotations, counter-clockwise when the scene is mirrored.
    if MIRROR:
        return (-d[1], d[0])
    return (d[1], -d[0])


def _jog_turn(d):
    # Opposite turning sense, used to straighten out after the one-cell jog.
    if MIRROR:
        return (d[1], -d[0])
    return (-d[1], d[0])


def solve(demonstrations, grid):
    H = len(grid)
    W = len(grid[0])
    out = [list(row) for row in grid]
    cells = [(r, c) for r in range(H) for c in range(W) if grid[r][c] != BG]
    if not cells:
        return out
    col = FG
    if not any(grid[r][c] == FG for r, c in cells):
        col = grid[cells[0][0]][cells[0][1]]
    n = len(cells)
    cy = int(round(sum(r for r, _ in cells) / float(n)))
    cx = int(round(sum(c for _, c in cells) / float(n)))
    L = n // 4
    Lp = max(L, 2)
    lim = 2 * (H + W) + 10
    for d0 in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
        pos = [cy, cx]

        def walk(steps, d):
            for _ in range(steps):
                pos[0] += d[0]
                pos[1] += d[1]
                if 0 <= pos[0] < H and 0 <= pos[1] < W:
                    out[pos[0]][pos[1]] = col

        d = d0
        walk(Lp, d)
        k = 0
        while True:
            a = 4 * k + 2
            if a > lim:
                break
            d = _outer_turn(d)
            walk(a, d)
            d = _outer_turn(d)
            walk(Lp - 2, d)
            d = _jog_turn(d)
            walk(Lp, d)
            k += 1
    return out
'''
    return (template.replace('__BG__', repr(bg))
                    .replace('__FG__', repr(fg))
                    .replace('__MIRROR__', repr(mirrored)))
