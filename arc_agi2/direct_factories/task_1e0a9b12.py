def build_program(d4, palette):
    k = d4 % 4
    # Original gravity is straight down, direction (dr, dc) = (1, 0).
    # Reversing each row does not change a vertical direction.
    # One clockwise rotation maps a direction (dr, dc) to (dc, -dr):
    # down -> left -> up -> right.
    direction = ['down', 'left', 'up', 'right'][k]
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('DIRECTION = %r' % direction)
    lines.append('')
    lines.append('def _pack_end(line):')
    lines.append('    cells = [int(v) for v in line if int(v) != BG]')
    lines.append('    return [BG] * (len(line) - len(cells)) + cells')
    lines.append('')
    lines.append('def _pack_start(line):')
    lines.append('    cells = [int(v) for v in line if int(v) != BG]')
    lines.append('    return cells + [BG] * (len(line) - len(cells))')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    out = g.copy()')
    lines.append("    if DIRECTION == 'down':")
    lines.append('        for x in range(w):')
    lines.append('            out[:, x] = _pack_end(g[:, x])')
    lines.append("    elif DIRECTION == 'up':")
    lines.append('        for x in range(w):')
    lines.append('            out[:, x] = _pack_start(g[:, x])')
    lines.append("    elif DIRECTION == 'right':")
    lines.append('        for y in range(h):')
    lines.append('            out[y, :] = _pack_end(g[y, :])')
    lines.append('    else:')
    lines.append('        for y in range(h):')
    lines.append('            out[y, :] = _pack_start(g[y, :])')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
