def build_program(d4, palette):
    k = int(d4) % 4
    axis = 1 if (k % 2 == 1) else 0
    bg = int(palette[0])
    ink = int(palette[4])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('SPLIT_AXIS = %d' % axis)
    lines.append('BG = %d' % bg)
    lines.append('INK = %d' % ink)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    if SPLIT_AXIS == 0:')
    lines.append('        h = g.shape[0] // 2')
    lines.append('        first = g[:h, :]')
    lines.append('        second = g[h:2 * h, :]')
    lines.append('    else:')
    lines.append('        w = g.shape[1] // 2')
    lines.append('        first = g[:, :w]')
    lines.append('        second = g[:, w:2 * w]')
    lines.append('    out = np.full(first.shape, BG, dtype=int)')
    lines.append('    out[first != BG] = INK')
    lines.append('    out[second != BG] = INK')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
