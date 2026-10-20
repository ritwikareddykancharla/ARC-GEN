def build_program(d4, palette):
    d4 = int(d4) % 8
    # The native output [g | fliplr g] is symmetric under fliplr. Pushing it through each D4 element gives:
    #   axis 'h' = the two halves sit side by side; axis 'v' = the halves are stacked.
    #   first 'orig' = the unchanged input comes first (left or top).
    #   first 'mirror' = the mirrored copy comes first.
    table = {
        0: ('h', 'orig'),
        1: ('v', 'orig'),
        2: ('h', 'mirror'),
        3: ('v', 'mirror'),
        4: ('h', 'mirror'),
        5: ('v', 'mirror'),
        6: ('h', 'orig'),
        7: ('v', 'orig'),
    }
    axis, first = table[d4]
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('AXIS = %r' % axis)
    lines.append('FIRST = %r' % first)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    if AXIS == "h":')
    lines.append('        # Canvas twice as wide. Put the input and its left-right mirror side by side.')
    lines.append('        out = np.zeros((h, 2 * w), dtype=int)')
    lines.append('        mir = g[:, ::-1]')
    lines.append('        if FIRST == "orig":')
    lines.append('            out[:, :w] = g')
    lines.append('            out[:, w:] = mir')
    lines.append('        else:')
    lines.append('            out[:, :w] = mir')
    lines.append('            out[:, w:] = g')
    lines.append('    else:')
    lines.append('        # Canvas twice as tall. Stack the input and its top-bottom mirror.')
    lines.append('        out = np.zeros((2 * h, w), dtype=int)')
    lines.append('        mir = g[::-1, :]')
    lines.append('        if FIRST == "orig":')
    lines.append('            out[:h, :] = g')
    lines.append('            out[h:, :] = mir')
    lines.append('        else:')
    lines.append('            out[:h, :] = mir')
    lines.append('            out[h:, :] = g')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
