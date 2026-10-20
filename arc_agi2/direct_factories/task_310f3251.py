def build_program(d4, palette):
    dy, dx = -1, -1
    if d4 >= 4:
        dx = -dx
    for _ in range(d4 % 4):
        dy, dx = dx, -dy
    bg = int(palette[0])
    red = int(palette[2])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('SHADOW = %d' % red)
    lines.append('DY = %d' % dy)
    lines.append('DX = %d' % dx)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    motif = g.copy()')
    lines.append('    ys, xs = np.nonzero(g != BG)')
    lines.append('    for y, x in zip(ys.tolist(), xs.tolist()):')
    lines.append('        ty = (y + DY) % h')
    lines.append('        tx = (x + DX) % w')
    lines.append('        if g[ty, tx] == BG:')
    lines.append('            motif[ty, tx] = SHADOW')
    lines.append('    out = np.tile(motif, (3, 3))')
    lines.append('    return out.astype(int).tolist()')
    return '\n'.join(lines) + '\n'
