def build_program(d4, palette):
    axis = 0 if (d4 % 4) in (0, 2) else 1
    bg = int(palette[0])
    sep = int(palette[4])
    mark = int(palette[3])
    lines = [
        'import numpy as np',
        '',
        'AXIS = ' + repr(axis),
        'BG = ' + repr(bg),
        'SEP = ' + repr(sep),
        'MARK = ' + repr(mark),
        '',
        'def _line(g, i):',
        '    return g[i, :] if AXIS == 0 else g[:, i]',
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    n = g.shape[AXIS]',
        '    mid = (n - 1) / 2.0',
        '    full = [i for i in range(n) if np.all(_line(g, i) == SEP)]',
        '    if full:',
        '        s = min(full, key=lambda i: (abs(i - mid), i))',
        '    else:',
        '        s = n // 2',
        '    if AXIS == 0:',
        '        a = g[:s, :]',
        '        b = g[s + 1:, :]',
        '        h = min(a.shape[0], b.shape[0])',
        '        a = a[:h, :]',
        '        b = b[:h, :]',
        '    else:',
        '        a = g[:, :s]',
        '        b = g[:, s + 1:]',
        '        w = min(a.shape[1], b.shape[1])',
        '        a = a[:, :w]',
        '        b = b[:, :w]',
        '    out = np.where((a != BG) | (b != BG), MARK, BG)',
        '    return out.astype(int).tolist()',
        '',
    ]
    return '\n'.join(lines)
