def build_program(d4, palette):
    k = int(d4) % 4
    horizontal = (k % 2 == 1)
    fg = int(palette[8])
    sym = int(palette[2])
    asym = int(palette[5])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('FG = %d' % fg)
    lines.append('SYM = %d' % sym)
    lines.append('ASYM = %d' % asym)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    if g.ndim != 2:')
    lines.append('        return [list(r) for r in grid]')
    lines.append('    out = g.copy()')
    if horizontal:
        lines.append('    # mirror partner is the cell in the same row, reflected about the vertical midline')
        lines.append('    mirrored = g[:, ::-1]')
    else:
        lines.append('    # mirror partner is the cell in the same column, reflected about the horizontal midline')
        lines.append('    mirrored = g[::-1, :]')
    lines.append('    is_fg = (g == FG)')
    lines.append('    paired = is_fg & (mirrored == FG)')
    lines.append('    unpaired = is_fg & (mirrored != FG)')
    lines.append('    out[paired] = SYM')
    lines.append('    out[unpaired] = ASYM')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
