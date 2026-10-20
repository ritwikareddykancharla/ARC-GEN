def build_program(d4, palette):
    k = int(d4) % 8
    # Doubling axis: 1 means the mirrored pair sits side by side along columns; 0 means stacked along rows.
    # mirror_first: True means the mirrored copy comes first (low index) and the unmirrored copy comes last.
    table = {
        0: (1, True),
        1: (0, True),
        2: (1, False),
        3: (0, False),
        4: (1, False),
        5: (0, False),
        6: (1, True),
        7: (0, True),
    }
    axis, mirror_first = table[k]
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('DOUBLE_AXIS = %d' % axis)
    lines.append('MIRROR_FIRST = %s' % ('True' if mirror_first else 'False'))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    if DOUBLE_AXIS == 1:')
    lines.append('        m = g[:, ::-1]')
    lines.append('        block = np.hstack([m, g]) if MIRROR_FIRST else np.hstack([g, m])')
    lines.append('        f = block[::-1, :]')
    lines.append('        out = np.vstack([f, block, f])')
    lines.append('    else:')
    lines.append('        m = g[::-1, :]')
    lines.append('        block = np.vstack([m, g]) if MIRROR_FIRST else np.vstack([g, m])')
    lines.append('        f = block[:, ::-1]')
    lines.append('        out = np.hstack([f, block, f])')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
