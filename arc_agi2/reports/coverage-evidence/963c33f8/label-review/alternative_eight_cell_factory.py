TEMPLATE = '''import numpy as np

# Falling sticks, written directly in visible coordinates.
# Key sticks (STICK / TIP cells) travel toward the @EDGE@ edge.
BG = @BG@
OBS = @OBS@
STICK = @STICK@
TIP = @TIP@
DR = @DR@
DC = @DC@
LR = @LR@
LC = @LC@
LINE_IS_COLUMN = @LIC@
FLOOR_REACH = 0


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    keymask = (g == STICK) | (g == TIP)
    rs, cs = np.nonzero(keymask)
    if len(rs) == 0:
        return out.tolist()
    out[keymask] = BG
    lines = {}
    for r, c in zip(rs.tolist(), cs.tolist()):
        ln = c if LINE_IS_COLUMN else r
        lines.setdefault(ln, []).append((r, c))

    def inside(r, c):
        return 0 <= r < H and 0 <= c < W

    def leading(cells):
        return max(cells, key=lambda p: p[0] * DR + p[1] * DC)

    def edge_steps(r, c):
        k = 0
        while inside(r + (k + 1) * DR, c + (k + 1) * DC):
            k += 1
        return k

    lit = {}
    for ln, cells in lines.items():
        lit[ln] = any(int(g[r, c]) == TIP for r, c in cells)

    # Unlit sticks clear the far-edge floor within FLOOR_REACH of their line.
    for ln in sorted(lines):
        if lit[ln]:
            continue
        r0, c0 = leading(lines[ln])
        k = edge_steps(r0, c0)
        fr, fc = r0 + k * DR, c0 + k * DC
        for t in range(-FLOOR_REACH, FLOOR_REACH + 1):
            rr, cc = fr + t * LR, fc + t * LC
            if inside(rr, cc):
                out[rr, cc] = BG

    # Lit sticks fall until the next cell is an obstacle or out of the grid.
    for ln in sorted(lines):
        if not lit[ln]:
            continue
        cells = lines[ln]
        r0, c0 = leading(cells)
        k = 0
        while True:
            nr, nc = r0 + (k + 1) * DR, c0 + (k + 1) * DC
            if not inside(nr, nc) or int(out[nr, nc]) == OBS:
                break
            k += 1
        for r, c in cells:
            out[r + k * DR, c + k * DC] = g[r, c]

    # Unlit sticks go straight to the far edge and overwrite what is there.
    for ln in sorted(lines):
        if lit[ln]:
            continue
        cells = lines[ln]
        r0, c0 = leading(cells)
        k = edge_steps(r0, c0)
        for r, c in cells:
            out[r + k * DR, c + k * DC] = g[r, c]

    return out.tolist()
'''


def build_program(d4, palette):
    d4 = int(d4)
    dr, dc = 1, 0
    if d4 >= 4:
        dr, dc = dr, -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    dr, dc = int(dr), int(dc)
    lr, lc = abs(dc), abs(dr)
    edge = {(1, 0): 'bottom', (-1, 0): 'top', (0, 1): 'right', (0, -1): 'left'}[(dr, dc)]
    src = TEMPLATE
    src = src.replace('@EDGE@', edge)
    src = src.replace('@BG@', str(int(palette[7])))
    src = src.replace('@OBS@', str(int(palette[5])))
    src = src.replace('@STICK@', str(int(palette[9])))
    src = src.replace('@TIP@', str(int(palette[1])))
    src = src.replace('@DR@', str(dr))
    src = src.replace('@DC@', str(dc))
    src = src.replace('@LR@', str(lr))
    src = src.replace('@LC@', str(lc))
    src = src.replace('@LIC@', 'True' if dc == 0 else 'False')
    return src
