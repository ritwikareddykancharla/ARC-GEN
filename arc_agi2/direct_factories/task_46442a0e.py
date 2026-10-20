def build_program(d4, palette):
    k = d4 % 4
    base = 1 if d4 >= 4 else 0
    q = (base + k) % 4
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('# Quadrants in clockwise order: 0=top-left, 1=top-right, 2=bottom-right, 3=bottom-left.')
    lines.append('# The visible input appears unrotated in quadrant ANCHOR.')
    lines.append('# Each further quadrant clockwise holds the input turned one more quarter turn clockwise.')
    lines.append('ANCHOR = %d' % q)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    if h != w:')
    lines.append('        n = min(h, w)')
    lines.append('        g = g[:n, :n]')
    lines.append('    n = g.shape[0]')
    lines.append('    out = np.zeros((2 * n, 2 * n), dtype=int)')
    lines.append('    origins = [(0, 0), (0, n), (n, n), (n, 0)]')
    lines.append('    for j in range(4):')
    lines.append('        r, c = origins[(ANCHOR + j) % 4]')
    lines.append('        out[r:r + n, c:c + n] = np.rot90(g, -j)')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
