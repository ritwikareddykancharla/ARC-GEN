def build_program(d4, palette):
    d4 = int(d4) % 8
    k = d4 % 4
    flip = d4 >= 4
    # Track where the original left-to-right column order ends up in visible coordinates.
    # Original: line axis = column, ascending. Horizontal flip: ascending becomes descending.
    # Clockwise rotation maps (r,c)->(c,H-1-r): column order becomes row order (same
    # direction), and row order becomes column order (reversed direction).
    axis = 'col'
    asc = not flip
    for _ in range(k):
        if axis == 'col':
            axis = 'row'
        else:
            axis = 'col'
            asc = not asc
    bg = int(palette[5])
    mark = int(palette[0])
    ranks = [int(palette[i]) for i in range(1, 10)]
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('AXIS = %r' % axis)
    lines.append('ASCENDING = %r' % asc)
    lines.append('BG = %d' % bg)
    lines.append('MARK = %d' % mark)
    lines.append('RANK_COLOURS = %r' % ranks)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = g.copy()')
    lines.append('    mask = (g != BG)')
    lines.append('    if not mask.any():')
    lines.append('        return out.tolist()')
    lines.append('    if AXIS == "col":')
    lines.append('        idx = sorted(set(np.nonzero(mask)[1].tolist()), reverse=not ASCENDING)')
    lines.append('    else:')
    lines.append('        idx = sorted(set(np.nonzero(mask)[0].tolist()), reverse=not ASCENDING)')
    lines.append('    for rank, line in enumerate(idx):')
    lines.append('        colour = RANK_COLOURS[min(rank, len(RANK_COLOURS) - 1)]')
    lines.append('        if AXIS == "col":')
    lines.append('            ys = np.nonzero(mask[:, line])[0]')
    lines.append('            out[ys, line] = colour')
    lines.append('        else:')
    lines.append('            xs = np.nonzero(mask[line, :])[0]')
    lines.append('            out[line, xs] = colour')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
