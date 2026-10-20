def build_program(d4, palette):
    d4 = int(d4) % 8
    flipped = d4 >= 4
    odd = (d4 % 4) % 2 == 1
    use_sum = (flipped == odd)
    bg = int(palette[0])
    if use_sum:
        key_expr = '(x + y) % 3'
        desc = 'anti-diagonals (x + y constant)'
    else:
        key_expr = '(y - x) % 3'
        desc = 'main diagonals (y - x constant)'
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('# Stripes lie along %s; colours repeat with period 3 across them.' % desc)
    lines.append('')
    lines.append('def _key(y, x):')
    lines.append('    return ' + key_expr)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    colour_of = {}')
    lines.append('    for y in range(h):')
    lines.append('        for x in range(w):')
    lines.append('            c = int(g[y, x])')
    lines.append('            if c != BG:')
    lines.append('                colour_of.setdefault(_key(y, x), c)')
    lines.append('    out = g.copy()')
    lines.append('    for y in range(h):')
    lines.append('        for x in range(w):')
    lines.append('            k = _key(y, x)')
    lines.append('            if k in colour_of:')
    lines.append('                out[y, x] = colour_of[k]')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
