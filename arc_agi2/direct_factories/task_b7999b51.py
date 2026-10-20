def build_program(d4, palette):
    k = int(d4) % 4
    flip = int(d4) >= 4
    # Work out where a canonical bar-chart cell (r, c) lands in visible coordinates.
    # The canonical chart has shape (H, W). Each bar is a column c that starts at the
    # top and runs down rows 0..h-1. Ranks go left to right.
    er, ec, dh, dw = 'r', 'c', 'H', 'W'
    if flip:
        ec = '(' + dw + '-1-' + ec + ')'
    for _ in range(k):
        er, ec = ec, '(' + dh + '-1-' + er + ')'
        dh, dw = dw, dh
    bg = int(palette[0])
    tall_axis = 0 if k % 2 == 0 else 1
    lines = [
        'import numpy as np',
        '',
        'BG = ' + str(bg),
        'TALL_AXIS = ' + str(tall_axis),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    pieces = []',
        '    for col in np.unique(g):',
        '        col = int(col)',
        '        if col == BG:',
        '            continue',
        '        pos = np.argwhere(g == col)',
        '        ext = pos.max(axis=0) - pos.min(axis=0) + 1',
        '        tall = int(ext[TALL_AXIS])',
        '        wide = int(ext[1 - TALL_AXIS])',
        '        pieces.append((tall, wide, col))',
        '    if not pieces:',
        '        return [[BG]]',
        '    pieces.sort(key=lambda p: (-p[0], -p[1], -p[2]))',
        '    H = pieces[0][0]',
        '    W = len(pieces)',
        '    out = np.full((' + dh + ', ' + dw + '), BG, dtype=int)',
        '    for c, (h, _w, col) in enumerate(pieces):',
        '        for r in range(h):',
        '            out[' + er + ', ' + ec + '] = col',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
