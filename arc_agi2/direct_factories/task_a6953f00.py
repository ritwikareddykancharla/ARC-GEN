def build_program(d4, palette):
    d4 = int(d4) % 8

    def _corner(r, c):
        # (r, c) in {0,1}^2: r=0 top / 1 bottom, c=0 left / 1 right.
        # Indices >= 4 first reverse each row, then rotate clockwise d4 % 4 times.
        if d4 >= 4:
            c = 1 - c
        for _ in range(d4 % 4):
            r, c = c, 1 - r
        return r, c

    odd_r, odd_c = _corner(0, 0)
    even_r, even_c = _corner(0, 1)
    parity_on_width = (d4 % 4) in (0, 2)
    NL = chr(10)
    lines = [
        'import numpy as np',
        '',
        'ODD_CORNER = (%d, %d)' % (odd_r, odd_c),
        'EVEN_CORNER = (%d, %d)' % (even_r, even_c),
        'PARITY_ON_WIDTH = %s' % ('True' if parity_on_width else 'False'),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.asarray(grid, dtype=int)',
        '    h, w = g.shape',
        '    n = w if PARITY_ON_WIDTH else h',
        '    r, c = EVEN_CORNER if n % 2 == 0 else ODD_CORNER',
        '    y = 0 if r == 0 else h - 2',
        '    x = 0 if c == 0 else w - 2',
        '    return [[int(v) for v in row] for row in g[y:y + 2, x:x + 2]]',
    ]
    return NL.join(lines) + NL
