def build_program(d4, palette):
    bg = int(palette[0])
    k = int(d4) % 4
    # The original mirror reverses columns. Rotating by 90 or 270 degrees turns that into a row reversal.
    # Conjugating by the row reflection (d4>=4) leaves a left-right mirror unchanged.
    flip_rows = (k % 2 == 1)
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('FLIP_ROWS = %s' % ('True' if flip_rows else 'False'))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    ys, xs = np.nonzero(g != BG)')
    lines.append('    if ys.size == 0:')
    lines.append('        return g.tolist()')
    lines.append('    y0, y1 = int(ys.min()), int(ys.max())')
    lines.append('    x0, x1 = int(xs.min()), int(xs.max())')
    lines.append('    c = g[y0:y1 + 1, x0:x1 + 1].copy()')
    lines.append('    if FLIP_ROWS:')
    lines.append('        out = c[::-1, :].copy()')
    lines.append('    else:')
    lines.append('        out = c[:, ::-1].copy()')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
