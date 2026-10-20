def build_program(d4, palette):
    n = 6
    marker = [[1 if (r % 2 == 0 and c % 2 == 0) else 0 for c in range(n)] for r in range(n)]
    g = [row[:] for row in marker]
    if d4 >= 4:
        g = [row[::-1] for row in g]
    for _ in range(d4 % 4):
        h = len(g)
        w = len(g[0])
        g = [[g[h - 1 - j][i] for j in range(h)] for i in range(w)]
    first_r = min(r for r in range(n) if any(g[r]))
    first_c = min(c for c in range(n) if any(g[r][c] for r in range(n)))
    rev_r = 1 if first_r != 0 else 0
    rev_c = 1 if first_c != 0 else 0
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('ROW_FROM_END = %d' % rev_r)
    lines.append('COL_FROM_END = %d' % rev_c)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    r0 = (H - 1) % 2 if ROW_FROM_END else 0')
    lines.append('    c0 = (W - 1) % 2 if COL_FROM_END else 0')
    lines.append('    out = g[r0::2, c0::2]')
    lines.append('    return out.astype(int).tolist()')
    return '\n'.join(lines) + '\n'
