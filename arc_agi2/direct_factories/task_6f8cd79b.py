def build_program(d4, palette):
    frame = int(palette[8])
    lines = [
        'import numpy as np',
        '',
        'FRAME = %d' % frame,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int).copy()',
        '    if g.ndim != 2 or g.size == 0:',
        '        return [list(r) for r in grid]',
        '    g[0, :] = FRAME',
        '    g[-1, :] = FRAME',
        '    g[:, 0] = FRAME',
        '    g[:, -1] = FRAME',
        '    return g.tolist()',
        '',
    ]
    return '\n'.join(lines)
