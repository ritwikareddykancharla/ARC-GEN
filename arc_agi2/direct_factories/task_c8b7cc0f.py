def build_program(d4, palette):
    k = d4 % 4
    flip = d4 >= 4
    order = []
    for i in range(9):
        r, c = i // 3, i % 3
        if flip:
            c = 2 - c
        for _ in range(k):
            r, c = c, 2 - r
        order.append((r, c))
    bg = int(palette[0])
    fc = int(palette[1])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('FC = %d' % fc)
    lines.append('ORDER = %r' % (order,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = [[BG for _ in range(3)] for _ in range(3)]')
    lines.append('    ys, xs = np.nonzero(g == FC)')
    lines.append('    if len(ys) == 0:')
    lines.append('        return out')
    lines.append('    y0, y1 = int(ys.min()), int(ys.max())')
    lines.append('    x0, x1 = int(xs.min()), int(xs.max())')
    lines.append('    inner = g[y0 + 1:y1, x0 + 1:x1]')
    lines.append('    cands = [int(v) for v in np.unique(g) if int(v) != BG and int(v) != FC]')
    lines.append('    if not cands:')
    lines.append('        return out')
    lines.append('    best = None')
    lines.append('    for v in cands:')
    lines.append('        key = (int(np.sum(inner == v)), int(np.sum(g == v)), -v)')
    lines.append('        if best is None or key > best[0]:')
    lines.append('            best = (key, v)')
    lines.append('    dc = best[1]')
    lines.append('    n = min(int(np.sum(inner == dc)), 9)')
    lines.append('    for i in range(n):')
    lines.append('        r, c = ORDER[i]')
    lines.append('        out[r][c] = dc')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
