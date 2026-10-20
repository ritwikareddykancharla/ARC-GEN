def build_program(d4, palette):
    order = ['TL', 'TR', 'BR', 'BL']
    start = 1 if d4 >= 4 else 0
    corner = order[(start + (d4 % 4)) % 4]
    from_bottom = corner in ('BL', 'BR')
    from_right = corner in ('TR', 'BR')
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('FROM_BOTTOM = ' + repr(bool(from_bottom)))
    lines.append('FROM_RIGHT = ' + repr(bool(from_right)))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    r0 = max(h - 2, 0) if FROM_BOTTOM else 0')
    lines.append('    c0 = max(w - 2, 0) if FROM_RIGHT else 0')
    lines.append('    out = g[r0:r0 + 2, c0:c0 + 2]')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
