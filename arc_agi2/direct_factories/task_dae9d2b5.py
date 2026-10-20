def build_program(d4, palette):
    d4 = int(d4)
    bg = int(palette[0])
    fg = int(palette[6])
    # Native split is horizontal (two panels side by side along the width).
    # A row reversal keeps the split along the width. An odd number of clockwise
    # rotations moves it to the height. Any flip or rotation of the whole grid
    # turns the native translation between panels into another translation, so
    # visible cell i of the first half lines up with visible cell i + half of the
    # second half.
    axis = 0 if (d4 % 4) in (1, 3) else 1
    lines = [
        'import numpy as np',
        '',
        'AXIS = %d' % axis,
        'BG = %d' % bg,
        'FG = %d' % fg,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    if AXIS == 1:',
        '        half = g.shape[1] // 2',
        '        a = g[:, :half]',
        '        b = g[:, half:2 * half]',
        '    else:',
        '        half = g.shape[0] // 2',
        '        a = g[:half, :]',
        '        b = g[half:2 * half, :]',
        '    out = np.full(a.shape, BG, dtype=int)',
        '    out[(a != BG) | (b != BG)] = FG',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
