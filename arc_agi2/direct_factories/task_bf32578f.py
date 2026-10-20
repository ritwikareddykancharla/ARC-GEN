def build_program(d4, palette):
    d4 = int(d4)
    # Opening direction of the bracket in canonical coords is right: (dr, dc) = (0, +1).
    dr, dc = 0, 1
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    bg = int(palette[0])
    head = [
        'import numpy as np',
        '',
        'BG = %d' % bg,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    mask = g != BG',
        '    out = np.full_like(g, BG)',
        '    if not mask.any():',
        '        return out.tolist()',
        '    ys, xs = np.nonzero(mask)',
        '    colour = int(g[ys[0], xs[0]])',
        '    r0, r1 = int(ys.min()), int(ys.max())',
        '    c0, c1 = int(xs.min()), int(xs.max())',
        '    cells = []',
    ]
    if (dr, dc) == (0, 1):
        mid = [
            '    # bracket opens rightward: per row, fill right of the rightmost stroke up to bbox right edge',
            '    for r in range(r0, r1 + 1):',
            '        cols = np.nonzero(mask[r])[0]',
            '        if len(cols) == 0:',
            '            continue',
            '        for c in range(int(cols.max()) + 1, c1 + 1):',
            '            cells.append((r, c, r, 2 * c1 + 1 - c))',
        ]
    elif (dr, dc) == (0, -1):
        mid = [
            '    # bracket opens leftward: per row, fill left of the leftmost stroke down to bbox left edge',
            '    for r in range(r0, r1 + 1):',
            '        cols = np.nonzero(mask[r])[0]',
            '        if len(cols) == 0:',
            '            continue',
            '        for c in range(c0, int(cols.min())):',
            '            cells.append((r, c, r, 2 * c0 - 1 - c))',
        ]
    elif (dr, dc) == (1, 0):
        mid = [
            '    # bracket opens downward: per column, fill below the lowest stroke down to bbox bottom edge',
            '    for c in range(c0, c1 + 1):',
            '        rows = np.nonzero(mask[:, c])[0]',
            '        if len(rows) == 0:',
            '            continue',
            '        for r in range(int(rows.max()) + 1, r1 + 1):',
            '            cells.append((r, c, 2 * r1 + 1 - r, c))',
        ]
    else:
        mid = [
            '    # bracket opens upward: per column, fill above the highest stroke up to bbox top edge',
            '    for c in range(c0, c1 + 1):',
            '        rows = np.nonzero(mask[:, c])[0]',
            '        if len(rows) == 0:',
            '            continue',
            '        for r in range(r0, int(rows.min())):',
            '            cells.append((r, c, 2 * r0 - 1 - r, c))',
        ]
    tail = [
        '    for r, c, mr, mc in cells:',
        '        out[r, c] = colour',
        '        if 0 <= mr < H and 0 <= mc < W:',
        '            out[mr, mc] = colour',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(head + mid + tail)
