def build_program(d4, palette):
    k = int(d4) % 4
    bg = int(palette[0])
    head = [
        'import numpy as np',
        '',
        'BG = %d' % bg,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    out = g.copy()',
    ]
    if k == 0:
        # seeds on the top row, markers on the left/right columns, lines go down
        body = [
            '    for x in range(W):',
            '        c = int(g[0, x])',
            '        if c == BG:',
            '            continue',
            '        my = None',
            '        mx = None',
            '        for y in range(1, H):',
            '            if g[y, 0] == c:',
            '                my, mx = y, 0',
            '                break',
            '            if g[y, W - 1] == c:',
            '                my, mx = y, W - 1',
            '                break',
            '        if my is None:',
            '            out[:, x] = c',
            '            continue',
            '        out[0:my + 1, x] = c',
            '        lo, hi = min(mx, x), max(mx, x)',
            '        out[my, lo:hi + 1] = c',
        ]
    elif k == 2:
        # seeds on the bottom row, markers on the left/right columns, lines go up
        body = [
            '    for x in range(W):',
            '        c = int(g[H - 1, x])',
            '        if c == BG:',
            '            continue',
            '        my = None',
            '        mx = None',
            '        for y in range(H - 2, -1, -1):',
            '            if g[y, 0] == c:',
            '                my, mx = y, 0',
            '                break',
            '            if g[y, W - 1] == c:',
            '                my, mx = y, W - 1',
            '                break',
            '        if my is None:',
            '            out[:, x] = c',
            '            continue',
            '        out[my:H, x] = c',
            '        lo, hi = min(mx, x), max(mx, x)',
            '        out[my, lo:hi + 1] = c',
        ]
    elif k == 3:
        # seeds on the left column, markers on the top/bottom rows, lines go right
        body = [
            '    for y in range(H):',
            '        c = int(g[y, 0])',
            '        if c == BG:',
            '            continue',
            '        my = None',
            '        mx = None',
            '        for x in range(1, W):',
            '            if g[0, x] == c:',
            '                mx, my = x, 0',
            '                break',
            '            if g[H - 1, x] == c:',
            '                mx, my = x, H - 1',
            '                break',
            '        if mx is None:',
            '            out[y, :] = c',
            '            continue',
            '        out[y, 0:mx + 1] = c',
            '        lo, hi = min(my, y), max(my, y)',
            '        out[lo:hi + 1, mx] = c',
        ]
    else:
        # k == 1: seeds on the right column, markers on the top/bottom rows, lines go left
        body = [
            '    for y in range(H):',
            '        c = int(g[y, W - 1])',
            '        if c == BG:',
            '            continue',
            '        my = None',
            '        mx = None',
            '        for x in range(W - 2, -1, -1):',
            '            if g[0, x] == c:',
            '                mx, my = x, 0',
            '                break',
            '            if g[H - 1, x] == c:',
            '                mx, my = x, H - 1',
            '                break',
            '        if mx is None:',
            '            out[y, :] = c',
            '            continue',
            '        out[y, mx:W] = c',
            '        lo, hi = min(my, y), max(my, y)',
            '        out[lo:hi + 1, mx] = c',
        ]
    tail = ['    return out.tolist()', '']
    return '\n'.join(head + body + tail)
