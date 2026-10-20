def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[2])
    along_columns = (int(d4) % 4) % 2 == 1
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('FILL = %d' % fill)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = g.copy()')
    lines.append('    H, W = g.shape')
    if along_columns:
        lines.append('    # zigzag strokes run horizontally; fill vertically between consecutive line cells in each column')
        lines.append('    for x in range(W):')
        lines.append('        ys = [y for y in range(H) if g[y, x] != BG]')
        lines.append('        for a, b in zip(ys, ys[1:]):')
        lines.append('            for y in range(a + 1, b):')
        lines.append('                if out[y, x] == BG:')
        lines.append('                    out[y, x] = FILL')
    else:
        lines.append('    # zigzag strokes run vertically; fill horizontally between consecutive line cells in each row')
        lines.append('    for y in range(H):')
        lines.append('        xs = [x for x in range(W) if g[y, x] != BG]')
        lines.append('        for a, b in zip(xs, xs[1:]):')
        lines.append('            for x in range(a + 1, b):')
        lines.append('                if out[y, x] == BG:')
        lines.append('                    out[y, x] = FILL')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
