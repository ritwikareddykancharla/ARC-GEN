def build_program(d4, palette):
    d4 = int(d4) % 8
    bg = int(palette[0])
    # p = SX*X + SY*Y + A*(N-1) + B*(L-1): visible input index feeding visible output cell (Y, X)
    table = {
        0: (1, 1, -1, 0),
        7: (1, 1, -1, 0),
        2: (1, 1, -1, 1),
        5: (1, 1, -1, 1),
        1: (-1, 1, 0, 0),
        6: (1, -1, 0, 0),
        3: (-1, 1, 0, 1),
        4: (1, -1, 0, 1),
    }
    sx, sy, a, b = table[d4]
    horiz = d4 in (0, 2, 4, 6)
    lines = [
        'import numpy as np',
        '',
        'BG = %d' % bg,
        'SX = %d' % sx,
        'SY = %d' % sy,
        'A = %d' % a,
        'B = %d' % b,
        'HORIZ = %s' % ('True' if horiz else 'False'),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    if HORIZ:',
        '        seq = g[0, :] if g.shape[0] == 1 or g.shape[1] != 1 else g[:, 0]',
        '    else:',
        '        seq = g[:, 0] if g.shape[1] == 1 or g.shape[0] != 1 else g[0, :]',
        '    L = int(len(seq))',
        '    n = int(np.sum(seq != BG))',
        '    N = L * n',
        '    if N == 0:',
        '        return [[BG]]',
        '    out = np.full((N, N), BG, dtype=int)',
        '    off = A * (N - 1) + B * (L - 1)',
        '    for p in range(L):',
        '        k = int(seq[p])',
        '        if k == BG:',
        '            continue',
        '        for Y in range(N):',
        '            X = SX * (p - off - SY * Y)',
        '            if 0 <= X < N:',
        '                out[Y, X] = k',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
