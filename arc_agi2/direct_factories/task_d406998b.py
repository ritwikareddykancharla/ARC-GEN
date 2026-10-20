def build_program(d4, palette):
    d4 = int(d4)
    flip = d4 >= 4
    k = d4 % 4
    # Original mechanism: the strip runs along columns (x). The anchor is the last column.
    # Grey cells whose distance from that anchor is even become green.
    # In visible coordinates, the strip runs along columns when k is even and along rows when k is odd.
    axis = 1 if k % 2 == 0 else 0
    if not flip:
        from_end = k in (0, 1)
    else:
        from_end = k in (2, 3)
    grey = int(palette[5])
    green = int(palette[3])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('GREY = ' + repr(grey))
    lines.append('GREEN = ' + repr(green))
    lines.append('AXIS = ' + repr(axis) + '  # 1: strip runs along columns, 0: strip runs along rows')
    lines.append('FROM_END = ' + repr(bool(from_end)) + '  # True: anchor is last index, False: anchor is index 0')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = g.copy()')
    lines.append('    H, W = g.shape')
    lines.append('    n = W if AXIS == 1 else H')
    lines.append('    for i in range(n):')
    lines.append('        dist = (n - 1 - i) if FROM_END else i')
    lines.append('        if dist % 2 != 0:')
    lines.append('            continue')
    lines.append('        if AXIS == 1:')
    lines.append('            m = g[:, i] == GREY')
    lines.append('            out[m, i] = GREEN')
    lines.append('        else:')
    lines.append('            m = g[i, :] == GREY')
    lines.append('            out[i, m] = GREEN')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
