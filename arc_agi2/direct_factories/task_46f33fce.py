def build_program(d4, palette):
    k = int(d4) % 8
    table = {
        0: (False, False),
        1: (False, True),
        2: (True, True),
        3: (True, False),
        4: (False, True),
        5: (True, True),
        6: (True, False),
        7: (False, False),
    }
    row_rev, col_rev = table[k]
    bg = int(palette[0])
    row_off = 0 if row_rev else -2
    col_off = 0 if col_rev else -2
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('ROW_OFF = %d' % row_off)
    lines.append('COL_OFF = %d' % col_off)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    out = np.full((2 * H, 2 * W), BG, dtype=int)')
    lines.append('    for y in range(H):')
    lines.append('        for x in range(W):')
    lines.append('            c = int(g[y, x])')
    lines.append('            if c == BG:')
    lines.append('                continue')
    lines.append('            y0 = 2 * y + ROW_OFF')
    lines.append('            x0 = 2 * x + COL_OFF')
    lines.append('            y1 = y0 + 4')
    lines.append('            x1 = x0 + 4')
    lines.append('            y0 = max(0, y0)')
    lines.append('            x0 = max(0, x0)')
    lines.append('            y1 = min(2 * H, y1)')
    lines.append('            x1 = min(2 * W, x1)')
    lines.append('            if y1 > y0 and x1 > x0:')
    lines.append('                out[y0:y1, x0:x1] = c')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
