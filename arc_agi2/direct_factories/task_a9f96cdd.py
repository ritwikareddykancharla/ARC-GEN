def build_program(d4, palette):
    flip = d4 >= 4
    k = d4 % 4
    base = [((-1, -1), 3), ((-1, 1), 6), ((1, -1), 8), ((1, 1), 7)]
    table = []
    for (dy, dx), c in base:
        if flip:
            dx = -dx
        for _ in range(k):
            # clockwise rotation maps (r, c) -> (c, H-1-r), so offset (dy, dx) -> (dx, -dy)
            dy, dx = dx, -dy
        table.append(((dy, dx), int(palette[c])))
    bg = int(palette[0])
    seed = int(palette[2])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('SEED = %d' % seed)
    lines.append('TABLE = %r' % (table,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    out = g.copy()')
    lines.append('    seeds = list(zip(*np.where(g == SEED)))')
    lines.append('    for y, x in seeds:')
    lines.append('        out[y, x] = BG')
    lines.append('    for y, x in seeds:')
    lines.append('        for (dy, dx), c in TABLE:')
    lines.append('            ny, nx = int(y) + dy, int(x) + dx')
    lines.append('            if 0 <= ny < H and 0 <= nx < W:')
    lines.append('                out[ny, nx] = c')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
