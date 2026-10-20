def build_program(d4, palette):
    dr, dc = 0, -1
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    bg = int(palette[0])
    fill = int(palette[5])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('DY = %d' % dr)
    lines.append('DX = %d' % dc)
    lines.append('BG = %d' % bg)
    lines.append('FILL = %d' % fill)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    out = np.full((H, W), FILL, dtype=int)')
    lines.append('    ys, xs = np.nonzero(g != BG)')
    lines.append('    ny = ys + DY')
    lines.append('    nx = xs + DX')
    lines.append('    m = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)')
    lines.append('    out[ny[m], nx[m]] = g[ys[m], xs[m]]')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
