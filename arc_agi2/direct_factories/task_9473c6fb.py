def build_program(d4, palette):
    # Track where the original +row and +column directions point in visible coordinates.
    # For d4 >= 4, reversing each row negates the column direction.
    # A clockwise rotation maps (dr, dc) to (dc, -dr).
    U = (1, 0)
    V = (0, -1) if d4 >= 4 else (0, 1)
    for _ in range(d4 % 4):
        U = (U[1], -U[0])
        V = (V[1], -V[0])
    # Find the walk direction along each visible axis.
    # Original walks always ascend along the axis whose lines each hold one pixel.
    sr = U[0] if U[0] != 0 else V[0]
    sc = U[1] if U[1] != 0 else V[1]
    bg = int(palette[7])
    cyc = [int(palette[2]), int(palette[8]), int(palette[5])]
    lines = [
        'import numpy as np',
        '',
        'BG = %d' % bg,
        'CYCLE = [%d, %d, %d]' % (cyc[0], cyc[1], cyc[2]),
        'SR = %d' % sr,
        'SC = %d' % sc,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    cells = [(r, c) for r in range(H) for c in range(W) if g[r, c] != BG]',
        '    rows = [r for r, _ in cells]',
        '    cols = [c for _, c in cells]',
        '    runiq = len(set(rows)) == len(rows)',
        '    cuniq = len(set(cols)) == len(cols)',
        '    if runiq and not cuniq:',
        '        # One pixel per visible row: walk the rows in direction SR.',
        '        order = sorted(cells, key=lambda p: (SR * p[0], SC * p[1]))',
        '    elif cuniq and not runiq:',
        '        # One pixel per visible column: walk the columns in direction SC.',
        '        order = sorted(cells, key=lambda p: (SC * p[1], SR * p[0]))',
        '    else:',
        '        # Outside the generator domain: neither axis or both axes unique.',
        '        order = sorted(cells, key=lambda p: (SR * p[0], SC * p[1]))',
        '    out = g.copy()',
        '    for i, (r, c) in enumerate(order):',
        '        out[r, c] = CYCLE[i % 3]',
        '    return out.tolist()',
        ''
    ]
    return '\n'.join(lines)
