def build_program(d4, palette):
    k = int(d4) % 4
    # Original bands are stacked along rows: top(colour1), middle(colour8), bottom(colour6).
    # A horizontal flip (d4>=4) leaves row order intact. A clockwise rotation sends old row r to
    # new column H-1-r, so top becomes rightmost. Two rotations put top at the bottom. Three
    # rotations send old row r to column r, so top becomes leftmost.
    horizontal = k in (1, 3)
    reverse = k in (1, 2)
    bg = int(palette[0])
    lines = [
        'import numpy as np',
        '',
        'BG = %d' % bg,
        'HORIZONTAL = %s' % ('True' if horizontal else 'False'),
        'REVERSE = %s' % ('True' if reverse else 'False'),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    if HORIZONTAL:',
        '        n = g.shape[1] // 3',
        '        bands = [g[:, i * n:(i + 1) * n] for i in range(3)]',
        '    else:',
        '        n = g.shape[0] // 3',
        '        bands = [g[i * n:(i + 1) * n, :] for i in range(3)]',
        '    if REVERSE:',
        '        bands = bands[::-1]',
        '    # bands are now [first sheet (orig 1), middle sheet (orig 8), last sheet (orig 6)]',
        '    out = np.full(bands[0].shape, BG, dtype=int)',
        '    # paint lowest to highest: middle sheet, then first sheet, then last sheet',
        '    for i in (1, 0, 2):',
        '        b = bands[i]',
        '        m = b != BG',
        '        out[m] = b[m]',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
