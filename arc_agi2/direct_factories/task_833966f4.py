def build_program(d4, palette):
    rot = int(d4) % 4
    axis = 0 if rot % 2 == 0 else 1
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('AXIS = %d' % axis)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int).copy()')
    lines.append('    if AXIS == 0:')
    lines.append('        n = g.shape[0]')
    lines.append('        if n >= 2:')
    lines.append('            g[[0, 1], :] = g[[1, 0], :]')
    lines.append('        if n >= 4:')
    lines.append('            g[[n - 2, n - 1], :] = g[[n - 1, n - 2], :]')
    lines.append('    else:')
    lines.append('        n = g.shape[1]')
    lines.append('        if n >= 2:')
    lines.append('            g[:, [0, 1]] = g[:, [1, 0]]')
    lines.append('        if n >= 4:')
    lines.append('            g[:, [n - 2, n - 1]] = g[:, [n - 1, n - 2]]')
    lines.append('    return g.tolist()')
    return '\n'.join(lines) + '\n'
