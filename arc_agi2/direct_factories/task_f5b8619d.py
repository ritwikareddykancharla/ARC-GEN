def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[8])
    k = d4 % 4
    # Original vertical lines (columns) stay columns under 0/180-degree rotations
    # (with or without the row-reversal); under 90/270-degree rotations they become rows.
    axis = 'cols' if k % 2 == 0 else 'rows'
    src = []
    src.append('import numpy as np')
    src.append('')
    src.append('BG = %d' % bg)
    src.append('FILL = %d' % fill)
    src.append('AXIS = %r' % axis)
    src.append('')
    src.append('def solve(demonstrations, grid):')
    src.append('    g = np.array(grid, dtype=int)')
    src.append('    h, w = g.shape')
    src.append('    out = np.empty((2 * h, 2 * w), dtype=int)')
    src.append('    out[:h, :w] = g')
    src.append('    out[:h, w:] = g')
    src.append('    out[h:, :w] = g')
    src.append('    out[h:, w:] = g')
    src.append('    if AXIS == "cols":')
    src.append('        for x in range(out.shape[1]):')
    src.append('            line = out[:, x]')
    src.append('            if np.any(line != BG):')
    src.append('                out[line == BG, x] = FILL')
    src.append('    else:')
    src.append('        for y in range(out.shape[0]):')
    src.append('            line = out[y, :]')
    src.append('            if np.any(line != BG):')
    src.append('                out[y, line == BG] = FILL')
    src.append('    return out.tolist()')
    return '\n'.join(src) + '\n'
