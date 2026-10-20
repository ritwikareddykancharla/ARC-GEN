def build_program(d4, palette):
    k = int(d4) % 4
    # Original gravity is 'down' (toward the last row). A horizontal row-reversal keeps the
    # vertical vector, and each clockwise rotation maps a vector (dr, dc) to (dc, -dr).
    # So the visible fall direction is: k=0 down, k=1 left, k=2 up, k=3 right.
    direction = ['down', 'left', 'up', 'right'][k]
    mark = int(palette[1])
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('MARK = %d' % mark)
    lines.append('BG = %d' % bg)
    lines.append('DIRECTION = %r' % direction)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int).copy()')
    lines.append('    h, w = g.shape')
    lines.append('    marks = [(y, x) for y in range(h) for x in range(w) if g[y, x] == MARK]')
    lines.append('    # Erase: each marker leaves background behind.')
    lines.append('    for y, x in marks:')
    lines.append('        g[y, x] = BG')
    lines.append('    # Stamp: each marker lands on the floor edge of its own line, in the fall direction.')
    lines.append('    for y, x in marks:')
    lines.append("        if DIRECTION == 'down':")
    lines.append('            g[h - 1, x] = MARK')
    lines.append("        elif DIRECTION == 'up':")
    lines.append('            g[0, x] = MARK')
    lines.append("        elif DIRECTION == 'left':")
    lines.append('            g[y, 0] = MARK')
    lines.append('        else:')
    lines.append('            g[y, w - 1] = MARK')
    lines.append('    return g.tolist()')
    lines.append('')
    return '\n'.join(lines)
