def build_program(d4, palette):
    d4 = int(d4) % 8
    # In the original frame the L-shaped border occupies the bottom row and the right column.
    edges = {'bottom', 'right'}
    if d4 >= 4:
        # Reversing each row swaps the left and right columns. Top and bottom stay where they are.
        flip = {'left': 'right', 'right': 'left', 'top': 'top', 'bottom': 'bottom'}
        edges = {flip[e] for e in edges}
    # One clockwise rotation moves top->right, right->bottom, bottom->left, left->top.
    rot = {'top': 'right', 'right': 'bottom', 'bottom': 'left', 'left': 'top'}
    for _ in range(d4 % 4):
        edges = {rot[e] for e in edges}
    br = -1 if 'bottom' in edges else 0
    bc = -1 if 'right' in edges else 0
    bg = int(palette[0])
    red = int(palette[2])
    lines = [
        'import numpy as np',
        '',
        'BORDER_ROW = ' + repr(br),
        'BORDER_COL = ' + repr(bc),
        'BG = ' + repr(bg),
        'RAY = ' + repr(red),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    h, w = g.shape',
        '    br = BORDER_ROW % h',
        '    bc = BORDER_COL % w',
        '    border = set(g[br, :].tolist()) | set(g[:, bc].tolist())',
        '    border.discard(BG)',
        '    k = len(border) + 1',
        '    out = np.kron(g, np.ones((k, k), dtype=int))',
        '    ys = []',
        '    xs = []',
        '    for y in range(h):',
        '        if y == br:',
        '            continue',
        '        for x in range(w):',
        '            if x == bc:',
        '                continue',
        '            if g[y, x] != BG:',
        '                ys.append(y)',
        '                xs.append(x)',
        '    if ys:',
        '        Y0 = min(ys) * k',
        '        X0 = min(xs) * k',
        '        Y1 = (max(ys) + 1) * k - 1',
        '        X1 = (max(xs) + 1) * k - 1',
        '        H, W = out.shape',
        '        for cy, cx, dy, dx in ((Y0, X0, -1, -1), (Y0, X1, -1, 1), (Y1, X0, 1, -1), (Y1, X1, 1, 1)):',
        '            y, x = cy + dy, cx + dx',
        '            while 0 <= y < H and 0 <= x < W and out[y, x] == BG:',
        '                out[y, x] = RAY',
        '                y += dy',
        '                x += dx',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
