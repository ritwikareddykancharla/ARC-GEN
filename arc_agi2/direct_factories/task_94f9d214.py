def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[2])
    # Odd rotation counts turn the 8x4 stack into 4x8, so the halves sit side by side.
    horizontal = (d4 % 4) in (1, 3)
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('MARK = %d' % mark)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    if horizontal:
        lines.append('    w = g.shape[1] // 2')
        lines.append('    a = g[:, :w]')
        lines.append('    b = g[:, w:2 * w]')
    else:
        lines.append('    h = g.shape[0] // 2')
        lines.append('    a = g[:h, :]')
        lines.append('    b = g[h:2 * h, :]')
    lines.append('    out = np.full(a.shape, BG, dtype=int)')
    lines.append('    out[(a == BG) & (b == BG)] = MARK')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
