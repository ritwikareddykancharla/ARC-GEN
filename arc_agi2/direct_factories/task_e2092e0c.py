def build_program(d4, palette):
    d4 = int(d4) % 8
    k = d4 % 4
    # Original key window sits at the top-left corner (corner index 0).
    # Corner indices clockwise: 0=TL, 1=TR, 2=BR, 3=BL.
    # A clockwise rotation advances the index by 1. A horizontal row-reversal maps TL to TR.
    idx = k if d4 < 4 else (1 + k) % 4
    at_top = idx in (0, 1)
    at_left = idx in (0, 3)
    grey = int(palette[5])
    lines = [
        'import numpy as np',
        '',
        'KEY_AT_TOP = ' + repr(bool(at_top)),
        'KEY_AT_LEFT = ' + repr(bool(at_left)),
        'GREY = ' + repr(grey),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    out = g.copy()',
        '    if H < 3 or W < 3:',
        '        return out.tolist()',
        '    top = 0 if KEY_AT_TOP else H - 3',
        '    left = 0 if KEY_AT_LEFT else W - 3',
        '    key = g[top:top + 3, left:left + 3]',
        '    found = None',
        '    for y in range(H - 2):',
        '        for x in range(W - 2):',
        '            if y == top and x == left:',
        '                continue',
        '            if np.array_equal(g[y:y + 3, x:x + 3], key):',
        '                found = (y, x)',
        '                break',
        '        if found is not None:',
        '            break',
        '    if found is None:',
        '        return out.tolist()',
        '    y, x = found',
        '    for yy in range(y - 1, y + 4):',
        '        for xx in range(x - 1, x + 4):',
        '            if 0 <= yy < H and 0 <= xx < W and (yy in (y - 1, y + 3) or xx in (x - 1, x + 3)):',
        '                out[yy, xx] = GREY',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
