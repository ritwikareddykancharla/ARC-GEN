def build_program(d4, palette):
    d4 = int(d4) % 8
    k = d4 % 4
    flip = d4 >= 4
    # In the original frame the control strip is the left column and the picture is rolled
    # down (+row direction) by the marker's distance from the top of the strip.
    # Track the strip side and the roll direction through the transform
    # (optional horizontal flip, then k clockwise rotations).
    if not flip:
        table = [('left', 0, 1), ('top', 1, -1), ('right', 0, -1), ('bottom', 1, 1)]
    else:
        table = [('right', 0, 1), ('bottom', 1, -1), ('left', 0, -1), ('top', 1, 1)]
    side, axis, sign = table[k]
    mark = int(palette[2])
    filler = int(palette[6])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('SIDE = %r' % side)
    lines.append('AXIS = %d' % axis)
    lines.append('SIGN = %d' % sign)
    lines.append('MARK = %d' % mark)
    lines.append('FILLER = %d' % filler)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append("    if SIDE == 'left':")
    lines.append('        strip = g[:, 0]; pic = g[:, 1:]')
    lines.append("    elif SIDE == 'right':")
    lines.append('        strip = g[:, -1]; pic = g[:, :-1]')
    lines.append("    elif SIDE == 'top':")
    lines.append('        strip = g[0, :]; pic = g[1:, :]')
    lines.append('    else:')
    lines.append('        strip = g[-1, :]; pic = g[:-1, :]')
    lines.append('    hits = np.where(strip == MARK)[0]')
    lines.append('    if len(hits) == 0:')
    lines.append('        hits = np.where(strip != FILLER)[0]')
    lines.append('    if len(hits) == 0:')
    lines.append('        vals, cnts = np.unique(strip, return_counts=True)')
    lines.append('        maj = vals[np.argmax(cnts)]')
    lines.append('        hits = np.where(strip != maj)[0]')
    lines.append('    p = int(hits[0]) if len(hits) else 0')
    lines.append('    n = len(strip)')
    lines.append('    # distance of the marker from the strip end the roll direction starts at')
    lines.append('    r = p if SIGN > 0 else (n - 1 - p)')
    lines.append('    out = np.roll(pic, SIGN * r, axis=AXIS)')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
