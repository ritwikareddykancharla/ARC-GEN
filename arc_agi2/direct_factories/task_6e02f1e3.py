def build_program(d4, palette):
    d4 = int(d4) % 8
    n = 3

    def tf(r, c):
        if d4 >= 4:
            c = n - 1 - c
        for _ in range(d4 % 4):
            r, c = c, n - 1 - r
        return r, c

    def classify(cells):
        pts = [tf(r, c) for r, c in cells]
        if all(r == 0 for r, _ in pts):
            return 0
        if all(r == n - 1 for r, _ in pts):
            return 1
        if all(c == 0 for _, c in pts):
            return 2
        if all(c == n - 1 for _, c in pts):
            return 3
        if all(r == c for r, c in pts):
            return 4
        return 5

    k1 = classify([(0, 0), (0, 1), (0, 2)])
    k2 = classify([(0, 0), (1, 1), (2, 2)])
    k3 = classify([(0, 2), (1, 1), (2, 0)])
    bg = int(palette[0])
    fg = int(palette[5])

    src = [
        'import numpy as np',
        '',
        'BG = ' + str(bg),
        'FG = ' + str(fg),
        'KIND_ONE = ' + str(k1),
        'KIND_TWO = ' + str(k2),
        'KIND_MANY = ' + str(k3),
        '',
        'def _cells(kind, h, w):',
        '    m = min(h, w)',
        '    if kind == 0:',
        '        return [(0, x) for x in range(w)]',
        '    if kind == 1:',
        '        return [(h - 1, x) for x in range(w)]',
        '    if kind == 2:',
        '        return [(y, 0) for y in range(h)]',
        '    if kind == 3:',
        '        return [(y, w - 1) for y in range(h)]',
        '    if kind == 4:',
        '        return [(i, i) for i in range(m)]',
        '    return [(i, w - 1 - i) for i in range(m)]',
        '',
        'def solve(demonstrations, grid):',
        '    g = np.asarray(grid, dtype=int)',
        '    h, w = g.shape',
        '    out = np.full((h, w), BG, dtype=int)',
        '    n = len(np.unique(g))',
        '    if n <= 1:',
        '        kind = KIND_ONE',
        '    elif n == 2:',
        '        kind = KIND_TWO',
        '    else:',
        '        kind = KIND_MANY',
        '    for y, x in _cells(kind, h, w):',
        '        out[y, x] = FG',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(src)
