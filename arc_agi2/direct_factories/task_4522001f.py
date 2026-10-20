def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[3])
    marker = int(palette[2])
    lines = [
        'import numpy as np',
        '',
        'BG = %d' % bg,
        'FILL = %d' % fill,
        'MARKER = %d' % marker,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    out = np.full((3 * H, 3 * W), BG, dtype=int)',
        '    cells = np.argwhere((g == FILL) | (g == MARKER))',
        '    if len(cells) == 0:',
        '        return out.tolist()',
        '    y0, x0 = [int(v) for v in cells.min(axis=0)]',
        '    y1, x1 = [int(v) for v in cells.max(axis=0)]',
        '    k = max(y1 - y0 + 1, x1 - x0 + 1)',
        '    s = 2 * k',
        '    m = np.argwhere(g == MARKER)',
        '    if len(m):',
        '        my, mx = int(m[0][0]), int(m[0][1])',
        '    else:',
        '        my, mx = y0, x0',
        '    dy, dx = my - y0, mx - x0',
        '    if dy == dx:',
        '        pos = [(y0, x0), (y0 + s, x0 + s)]',
        '    else:',
        '        pos = [(y0, x0 + s), (y0 + s, x0)]',
        '    for py, px in pos:',
        '        out[py:py + s, px:px + s] = FILL',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
