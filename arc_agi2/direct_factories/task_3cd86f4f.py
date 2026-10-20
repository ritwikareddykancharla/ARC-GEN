def build_program(d4, palette):
    d4 = int(d4) % 8
    fill = int(palette[0])
    if d4 in (0, 2):
        axis = 'rows'
        rev = True
    elif d4 in (4, 6):
        axis = 'rows'
        rev = False
    elif d4 in (1, 3):
        axis = 'cols'
        rev = False
    else:
        axis = 'cols'
        rev = True
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('FILL = %d' % fill)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    if axis == 'rows':
        lines.append('    out = np.full((h, w + h - 1), FILL, dtype=int)')
        lines.append('    for y in range(h):')
        if rev:
            lines.append('        s = h - 1 - y')
        else:
            lines.append('        s = y')
        lines.append('        out[y, s:s + w] = g[y, :]')
    else:
        lines.append('    out = np.full((h + w - 1, w), FILL, dtype=int)')
        lines.append('    for x in range(w):')
        if rev:
            lines.append('        s = w - 1 - x')
        else:
            lines.append('        s = x')
        lines.append('        out[s:s + h, x] = g[:, x]')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
