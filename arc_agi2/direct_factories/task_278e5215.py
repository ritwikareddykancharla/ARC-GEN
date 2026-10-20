def build_program(d4, palette):
    k = d4 % 4
    bg = int(palette[0])
    shape = int(palette[5])
    horiz = (k % 2 == 0)
    side = {0: 'bottom', 1: 'left', 2: 'top', 3: 'right'}[k]
    lines = [
        'import numpy as np',
        'from collections import Counter',
        '',
        'BG = %d' % bg,
        'SHAPE = %d' % shape,
        'HORIZ = %s' % ('True' if horiz else 'False'),
        'BASE_SIDE = %r' % side,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    ys, xs = np.where(g == SHAPE)',
        '    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()',
        '    mask = g[y0:y1 + 1, x0:x1 + 1] == SHAPE',
        '    lm = (g != BG) & (g != SHAPE)',
        '    lys, lxs = np.where(lm)',
        '    block = g[lys.min():lys.max() + 1, lxs.min():lxs.max() + 1]',
        '    if BASE_SIDE == "bottom":',
        '        base_line, color_line = block[-1, :], block[0, :]',
        '    elif BASE_SIDE == "top":',
        '        base_line, color_line = block[0, :], block[-1, :]',
        '    elif BASE_SIDE == "left":',
        '        base_line, color_line = block[:, 0], block[:, -1]',
        '    else:',
        '        base_line, color_line = block[:, -1], block[:, 0]',
        '    base = int(Counter(base_line.tolist()).most_common(1)[0][0])',
        '    color_line = [int(v) for v in color_line.tolist()]',
        '    out = np.full(mask.shape, base, dtype=int)',
        '    if HORIZ:',
        '        for c in range(mask.shape[1]):',
        '            col = color_line[c] if c < len(color_line) else base',
        '            out[mask[:, c], c] = col',
        '    else:',
        '        for r in range(mask.shape[0]):',
        '            col = color_line[r] if r < len(color_line) else base',
        '            out[r, mask[r, :]] = col',
        '    return out.tolist()',
        ''
    ]
    return '\n'.join(lines)
