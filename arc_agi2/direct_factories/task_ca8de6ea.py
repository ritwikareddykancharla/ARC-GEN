def build_program(d4, palette):
    d4 = int(d4) % 8

    def tf(r, c, n):
        # D4 convention: for d4 >= 4 first reverse each row, then rotate clockwise d4 % 4 times.
        if d4 >= 4:
            c = n - 1 - c
        for _ in range(d4 % 4):
            r, c = c, n - 1 - r
        return r, c

    # Native mechanism: each output cell in the 3x3 block takes its colour from one X pixel of the 5x5 input.
    # Corners stay corners, the centre stays the centre, and the inner diagonal ring turns 45 degrees onto the plus positions.
    src = {
        (0, 0): (0, 0), (0, 2): (0, 4), (2, 0): (4, 0), (2, 2): (4, 4),
        (1, 1): (2, 2),
        (0, 1): (1, 1), (1, 2): (1, 3), (2, 1): (3, 3), (1, 0): (3, 1),
    }
    pairs = []
    for (orr, occ), (ir, ic) in sorted(src.items()):
        vo = tf(orr, occ, 3)
        vi = tf(ir, ic, 5)
        pairs.append((int(vo[0]), int(vo[1]), int(vi[0]), int(vi[1])))
    bg = int(palette[0])

    lines = [
        'import numpy as np',
        '',
        '# Background colour of the transformed episode (canvas initial fill; every cell gets overwritten).',
        'BG = %d' % bg,
        '# (out_row, out_col, in_row, in_col) in visible coordinates:',
        '# corners -> corners, centre -> centre, inner diagonal ring -> edge midpoints.',
        'MAP = %r' % (pairs,),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.asarray(grid, dtype=int)',
        '    out = np.full((3, 3), BG, dtype=int)',
        '    for orow, ocol, irow, icol in MAP:',
        '        out[orow, ocol] = int(g[irow, icol])',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
