def build_program(d4, palette):
    d4 = int(d4) % 8
    bg = int(palette[0])
    fg = int(palette[5])
    mark = int(palette[1])
    # In the original task the mirror is left-right, so columns are reversed.
    # A reflection keeps that axis. An odd number of quarter turns swaps rows and
    # columns, so the mirror becomes top-bottom and rows are reversed.
    axis = 'rows' if (d4 % 4) % 2 == 1 else 'cols'
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('FG = %d' % fg)
    lines.append('MARK = %d' % mark)
    lines.append('AXIS = %r' % axis)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    if g.ndim != 2 or g.size == 0:')
    lines.append('        return [list(r) for r in grid]')
    lines.append('    if AXIS == "cols":')
    lines.append('        partner = g[:, ::-1]')
    lines.append('    else:')
    lines.append('        partner = g[::-1, :]')
    lines.append('    sym = (g == FG) & (partner == FG)')
    lines.append('    out = g.copy()')
    lines.append('    out[sym] = MARK')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
