def build_program(d4, palette):
    # Original mechanism: output = input followed by an identical copy placed
    # immediately after it along the horizontal axis (columns 0..W-1 and W..2W-1).
    # Horizontal reflection (d4>=4) keeps the duplication horizontal, and the two
    # copies are identical, so their order does not matter. A clockwise quarter
    # turn maps horizontal adjacency to vertical adjacency. So odd rotation counts
    # stack the copy below; even counts place it to the right.
    vertical = (d4 % 4) % 2 == 1
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('VERTICAL = %s' % ('True' if vertical else 'False'))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.asarray(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    if VERTICAL:')
    lines.append('        # canvas of twice the height; original in the top half, copy in the bottom half')
    lines.append('        out = np.zeros((2 * h, w), dtype=int)')
    lines.append('        out[:h, :] = g')
    lines.append('        out[h:, :] = g')
    lines.append('    else:')
    lines.append('        # canvas of twice the width; original in the left half, copy in the right half')
    lines.append('        out = np.zeros((h, 2 * w), dtype=int)')
    lines.append('        out[:, :w] = g')
    lines.append('        out[:, w:] = g')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
