def build_program(d4, palette):
    red = int(palette[2])
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('RED = %d' % red)
    lines.append('BG = %d' % bg)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    out = np.full((h * h, w * w), BG, dtype=int)')
    lines.append('    for i in range(h):')
    lines.append('        for j in range(w):')
    lines.append('            if g[i, j] == RED:')
    lines.append('                out[i * h:(i + 1) * h, j * w:(j + 1) * w] = g')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
