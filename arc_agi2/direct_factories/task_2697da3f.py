def build_program(d4, palette):
    k = d4 % 4
    start = 2 if d4 >= 4 else 0
    side = ['left', 'top', 'right', 'bottom'][(start + k) % 4]
    bg = int(palette[0])
    lines = [
        'import numpy as np',
        '',
        'SIDE = ' + repr(side),
        'BG = ' + repr(bg),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    ys, xs = np.where(g != BG)',
        '    if len(ys) == 0:',
        '        return g.tolist()',
        '    s = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]',
        '    R, C = s.shape',
        '    if SIDE in ("left", "right"):',
        '        a, b = C, R',
        '    else:',
        '        a, b = R, C',
        '    N = 2 * a + b',
        '    P = np.full((N, N), BG, dtype=int)',
        '    if SIDE == "left":',
        '        P[a:a + b, 0:a] = s',
        '    elif SIDE == "right":',
        '        P[a:a + b, a + b:N] = s',
        '    elif SIDE == "top":',
        '        P[0:a, a:a + b] = s',
        '    else:',
        '        P[a + b:N, a:a + b] = s',
        '    out = P.copy()',
        '    for r in (1, 2, 3):',
        '        Q = np.rot90(P, r)',
        '        m = Q != BG',
        '        out[m] = Q[m]',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
