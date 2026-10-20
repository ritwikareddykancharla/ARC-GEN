def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(palette[i]) for i in range(10)]
    bg = pal[0]
    paint = pal[2]
    n = 3
    base = [(0, 0), (0, 1), (0, 2), (1, 1)]
    order = []
    for (r, c) in base:
        if d4 >= 4:
            c = n - 1 - c
        for _ in range(d4 % 4):
            r, c = c, n - 1 - r
        order.append((r, c))
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('PAINT = %d' % paint)
    lines.append('ORDER = %r' % (order,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    count = int(np.sum(g != BG))')
    lines.append('    out = np.full((h, w), BG, dtype=int)')
    lines.append('    for (r, c) in ORDER[:count]:')
    lines.append('        if 0 <= r < h and 0 <= c < w:')
    lines.append('            out[r, c] = PAINT')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
