def build_program(d4, palette):
    d4 = int(d4)
    bg = int(palette[0])
    wall = int(palette[5])
    fill = int(palette[8])
    # Canonical floor lies in the 'down' direction (1, 0). Map that direction
    # into visible coordinates: a horizontal flip negates dc, and each clockwise
    # rotation sends (dr, dc) to (dc, -dr).
    dr, dc = 1, 0
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    layers_are_rows = (dc == 0)
    # Canonical snake order on the 3x3 output, mapped to visible coordinates.
    order = []
    for r in range(3):
        cols = range(3) if r % 2 == 0 else range(2, -1, -1)
        for c in cols:
            rr, cc = r, c
            if d4 >= 4:
                cc = 2 - cc
            for _ in range(d4 % 4):
                rr, cc = cc, 2 - rr
            order.append((rr, cc))
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('WALL = %d' % wall)
    lines.append('FILL = %d' % fill)
    lines.append('LAYERS_ARE_ROWS = %s' % ('True' if layers_are_rows else 'False'))
    lines.append('ORDER = %r' % (order,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.asarray(grid, dtype=int)')
    lines.append('    out = np.full((3, 3), BG, dtype=int)')
    lines.append('    ys, xs = np.nonzero(g == WALL)')
    lines.append('    if ys.size == 0:')
    lines.append('        return out.tolist()')
    lines.append('    y0, y1 = int(ys.min()), int(ys.max())')
    lines.append('    x0, x1 = int(xs.min()), int(xs.max())')
    lines.append('    empty = 0')
    lines.append('    if LAYERS_ARE_ROWS:')
    lines.append('        # walls are vertical; each row between the walls is one layer')
    lines.append('        for y in range(y0, y1 + 1):')
    lines.append('            seg = g[y, x0 + 1:x1]')
    lines.append('            if seg.size > 0 and np.all(seg == BG):')
    lines.append('                empty += 1')
    lines.append('    else:')
    lines.append('        # walls are horizontal; each column between the walls is one layer')
    lines.append('        for x in range(x0, x1 + 1):')
    lines.append('            seg = g[y0 + 1:y1, x]')
    lines.append('            if seg.size > 0 and np.all(seg == BG):')
    lines.append('                empty += 1')
    lines.append('    for i in range(min(empty, 9)):')
    lines.append('        r, c = ORDER[i]')
    lines.append('        out[r, c] = FILL')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
