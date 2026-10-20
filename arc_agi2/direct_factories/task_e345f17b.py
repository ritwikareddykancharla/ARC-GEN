def build_program(d4, palette):
    d4 = int(d4)
    bg = int(palette[0])
    mark = int(palette[4])
    # Original panels sit side by side (split along columns). An odd number of
    # clockwise quarter-turns makes them stacked (split along rows).
    # A reflection only reorders or flips both panels together, so cellwise
    # alignment is kept. NOR is symmetric, so panel order does not matter.
    split_rows = (d4 % 4) % 2 == 1
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('MARK = %d' % mark)
    lines.append('SPLIT_ROWS = %s' % ('True' if split_rows else 'False'))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    if SPLIT_ROWS:')
    lines.append('        half = h // 2')
    lines.append('        a = g[:half, :]')
    lines.append('        b = g[half:2 * half, :]')
    lines.append('    else:')
    lines.append('        half = w // 2')
    lines.append('        a = g[:, :half]')
    lines.append('        b = g[:, half:2 * half]')
    lines.append('    out = np.full(a.shape, BG, dtype=int)')
    lines.append('    out[(a == BG) & (b == BG)] = MARK')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
