def build_program(d4, palette):
    t = int(d4) % 8
    rot = t % 4
    flip = t >= 4
    # Original seed line runs along a row (horizontal), starting at column 0 and growing in +x.
    # Rotations by 1 or 3 quarter turns make the line vertical.
    axis = 'row' if rot in (0, 2) else 'col'
    # Rot 0 and 1 keep the start at index 0. Rot 2 and 3 move it to the far end.
    # A horizontal pre-flip reverses this.
    forward = rot in (0, 1)
    if flip:
        forward = not forward
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('AXIS = %r' % axis)
    lines.append('FORWARD = %r' % forward)
    lines.append('BG = %d' % bg)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int).copy()')
    lines.append('    mask = g != BG')
    lines.append('    if not mask.any():')
    lines.append('        return g.tolist()')
    lines.append('    if AXIS == "row":')
    lines.append('        line = int(np.argmax(mask.sum(axis=1)))')
    lines.append('        vec = g[line, :].copy()')
    lines.append('    else:')
    lines.append('        line = int(np.argmax(mask.sum(axis=0)))')
    lines.append('        vec = g[:, line].copy()')
    lines.append('    L = len(vec)')
    lines.append('    order = range(L) if FORWARD else range(L - 1, -1, -1)')
    lines.append('    colours = [int(vec[i]) for i in order if int(vec[i]) != BG]')
    lines.append('    n = len(colours)')
    lines.append('    k = 0')
    lines.append('    while k * (k + 1) // 2 < L:')
    lines.append('        tri = k * (k + 1) // 2')
    lines.append('        p = tri if FORWARD else L - 1 - tri')
    lines.append('        vec[p] = colours[k % n]')
    lines.append('        k += 1')
    lines.append('    if AXIS == "row":')
    lines.append('        g[line, :] = vec')
    lines.append('    else:')
    lines.append('        g[:, line] = vec')
    lines.append('    return g.tolist()')
    return '\n'.join(lines) + '\n'
