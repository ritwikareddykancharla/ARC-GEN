def build_program(d4, palette):
    bg = int(palette[0])
    d = int(d4) % 8
    # Copy k is placed at slot (R, C) on an s x s grid of tile-sized slots.
    # q = k // s and p = k % s, where s = number of background cells.
    # In the original orientation, q is the slot row (top to bottom) and p is
    # the slot column (left to right). Each D4 view below rewrites that fill
    # order directly in visible coordinates.
    formulas = {
        0: ('q', 'p'),                  # fill rows left->right, top->bottom
        1: ('p', 's - 1 - q'),          # fill columns top->bottom, right->left
        2: ('s - 1 - q', 's - 1 - p'),  # fill rows right->left, bottom->top
        3: ('s - 1 - p', 'q'),          # fill columns bottom->top, left->right
        4: ('q', 's - 1 - p'),          # fill rows right->left, top->bottom
        5: ('s - 1 - p', 's - 1 - q'),  # fill columns bottom->top, right->left
        6: ('s - 1 - q', 'p'),          # fill rows left->right, bottom->top
        7: ('p', 'q'),                  # fill columns top->bottom, left->right
    }
    fr, fc = formulas[d]
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    s = int((g == BG).sum())')
    lines.append('    n = int((g != BG).sum())')
    lines.append('    if s <= 0:')
    lines.append('        return np.zeros((0, 0), dtype=int).tolist()')
    lines.append('    out = np.full((h * s, w * s), BG, dtype=int)')
    lines.append('    for k in range(min(n, s * s)):')
    lines.append('        q, p = divmod(k, s)')
    lines.append('        R = ' + fr)
    lines.append('        C = ' + fc)
    lines.append('        out[R * h:(R + 1) * h, C * w:(C + 1) * w] = g')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
