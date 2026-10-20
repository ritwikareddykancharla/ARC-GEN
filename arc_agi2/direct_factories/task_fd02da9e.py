def build_program(d4, palette):
    N = 8
    d4 = int(d4)

    def fmap(r, c):
        h, w = N, N
        if d4 >= 4:
            c = w - 1 - c
        for _ in range(d4 % 4):
            r, c = c, h - 1 - r
            h, w = w, h
        return r, c

    figs = {
        (0, 0): [(1, 1), (1, 2), (2, 1), (2, 2)],
        (0, 7): [(1, 5), (1, 6), (2, 5), (2, 6)],
        (7, 0): [(4, 2), (5, 2), (6, 3)],
        (7, 7): [(4, 5), (5, 5), (6, 4)],
    }
    table = {}
    for (cy, cx), cells in figs.items():
        vy, vx = fmap(cy, cx)
        key = (vy != 0, vx != 0)
        offs = []
        for (r, c) in cells:
            y, x = fmap(r, c)
            offs.append((abs(y - vy), abs(x - vx)))
        table[key] = sorted(offs)
    bg = int(palette[7])

    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = ' + repr(bg))
    lines.append('# key: (corner_is_bottom_row, corner_is_right_col) in visible coords;')
    lines.append('# value: inward offsets (dy away from corner row, dx away from corner col)')
    lines.append('OFFS = ' + repr(table))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    out = g.copy()')
    lines.append('    corners = []')
    lines.append('    for cy in (0, H - 1):')
    lines.append('        for cx in (0, W - 1):')
    lines.append('            if (cy, cx) not in corners:')
    lines.append('                corners.append((cy, cx))')
    lines.append('    seeds = []')
    lines.append('    for cy, cx in corners:')
    lines.append('        c = int(g[cy, cx])')
    lines.append('        if c != BG:')
    lines.append('            seeds.append((cy, cx, c))')
    lines.append('            out[cy, cx] = BG')
    lines.append('    for cy, cx, c in seeds:')
    lines.append('        bottom = cy != 0')
    lines.append('        right = cx != 0')
    lines.append('        sy = -1 if bottom else 1')
    lines.append('        sx = -1 if right else 1')
    lines.append('        for dy, dx in OFFS[(bottom, right)]:')
    lines.append('            y = cy + sy * dy')
    lines.append('            x = cx + sx * dx')
    lines.append('            if 0 <= y < H and 0 <= x < W:')
    lines.append('                out[y, x] = c')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
