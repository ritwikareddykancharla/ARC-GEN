def build_program(d4, palette):
    k = d4 % 4
    # Original mechanism: the cells in the lower half (larger row index) of the figure's
    # bounding box are recoloured. A horizontal flip does not change 'down'. Each clockwise
    # rotation moves it: down -> left -> up -> right.
    direction = ['down', 'left', 'up', 'right'][k]
    bg = int(palette[0])
    fg = int(palette[1])
    tgt = int(palette[2])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('FG = %d' % fg)
    lines.append('TARGET = %d' % tgt)
    lines.append('DIRECTION = %r' % direction)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = g.copy()')
    lines.append('    mask = g != BG')
    lines.append('    ys, xs = np.nonzero(mask)')
    lines.append('    if len(ys) == 0:')
    lines.append('        return out.tolist()')
    lines.append('    y0, y1 = int(ys.min()), int(ys.max())')
    lines.append('    x0, x1 = int(xs.min()), int(xs.max())')
    lines.append('    h = y1 - y0 + 1')
    lines.append('    w = x1 - x0 + 1')
    lines.append('    sel = np.zeros_like(mask)')
    lines.append('    if DIRECTION == "down":')
    lines.append('        sel[y0 + h // 2:, :] = True')
    lines.append('    elif DIRECTION == "up":')
    lines.append('        sel[:y1 - h // 2 + 1, :] = True')
    lines.append('    elif DIRECTION == "right":')
    lines.append('        sel[:, x0 + w // 2:] = True')
    lines.append('    else:')
    lines.append('        sel[:, :x1 - w // 2 + 1] = True')
    lines.append('    out[mask & sel] = TARGET')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
