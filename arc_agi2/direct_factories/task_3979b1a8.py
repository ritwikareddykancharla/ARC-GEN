def build_program(d4, palette):
    # Track where the original top-left corner (the copy anchor / layer origin) lands.
    top, left = True, True
    if d4 >= 4:
        left = not left  # reverse each row: horizontal mirror
    for _ in range(d4 % 4):
        # clockwise rotation: (r,c)->(c,H-1-r); new top iff old left, new left iff old bottom
        top, left = left, (not top)
    flip_r = not top
    flip_c = not left
    lines = [
        'import numpy as np',
        '',
        'FLIP_R = %s' % ('True' if flip_r else 'False'),
        'FLIP_C = %s' % ('True' if flip_c else 'False'),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    n = g.shape[0]',
        '    # Roles read from the visible tile (the tile is D4-symmetric, so these cells keep their roles)',
        '    A = int(g[0, 0])',
        '    B = int(g[0, 1])',
        '    C = int(g[n // 2, n // 2])',
        '    seq = [A, C, B]',
        '    N = 2 * n',
        '    out = np.zeros((N, N), dtype=int)',
        '    for vr in range(N):',
        '        R = (N - 1 - vr) if FLIP_R else vr',
        '        for vc in range(N):',
        '            K = (N - 1 - vc) if FLIP_C else vc',
        '            if R < n and K < n:',
        '                continue',
        '            # L-shaped layer index measured from the anchor corner; the diagonal through',
        '            # the anchor corner takes the next layer colour',
        '            m = max(R, K) + (1 if R == K else 0)',
        '            out[vr, vc] = seq[(m - n) % 3]',
        '    r0 = n if FLIP_R else 0',
        '    c0 = n if FLIP_C else 0',
        '    out[r0:r0 + n, c0:c0 + n] = g',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
