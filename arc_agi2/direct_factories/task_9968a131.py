def build_program(d4, palette):
    # Lane direction: the original block runs down its rows, so its unit vector is (+1, 0).
    lr, lc = 1, 0
    # Shift direction: swapped rows move one cell right, so its unit vector is (0, +1).
    sr, sc = 0, 1
    # Reflection: reverse each row, which negates the column component.
    if d4 >= 4:
        lc = -lc
        sc = -sc
    # Clockwise rotation maps a vector (dr, dc) to (dc, -dr).
    for _ in range(d4 % 4):
        lr, lc = lc, -lr
        sr, sc = sc, -sr
    bg = int(palette[7])
    lines = [
        'import numpy as np',
        '',
        'BG = %d' % bg,
        'LR = %d' % lr,
        'LC = %d' % lc,
        'SR = %d' % sr,
        'SC = %d' % sc,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    out = g.copy()',
        '    H, W = g.shape',
        '    ys, xs = np.nonzero(g != BG)',
        '    if len(ys) == 0:',
        '        return out.tolist()',
        '    y0, y1 = int(ys.min()), int(ys.max())',
        '    x0, x1 = int(xs.min()), int(xs.max())',
        '    if LC == 0:',
        '        # Lanes are rows; the block extends vertically and swapped rows shift horizontally.',
        '        ref_y = y0 if LR == 1 else y1',
        '        ref = g[ref_y, x0:x1 + 1].copy()',
        '        for y in range(y0, y1 + 1):',
        '            seg = g[y, x0:x1 + 1].copy()',
        '            if not np.array_equal(seg, ref):',
        '                out[y, x0:x1 + 1] = BG',
        '                for i, v in enumerate(seg):',
        '                    x = x0 + i + SC',
        '                    if 0 <= x < W:',
        '                        out[y, x] = v',
        '    else:',
        '        # Lanes are columns; the block extends horizontally and swapped columns shift vertically.',
        '        ref_x = x0 if LC == 1 else x1',
        '        ref = g[y0:y1 + 1, ref_x].copy()',
        '        for x in range(x0, x1 + 1):',
        '            seg = g[y0:y1 + 1, x].copy()',
        '            if not np.array_equal(seg, ref):',
        '                out[y0:y1 + 1, x] = BG',
        '                for i, v in enumerate(seg):',
        '                    y = y0 + i + SR',
        '                    if 0 <= y < H:',
        '                        out[y, x] = v',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
