def build_program(d4, palette):
    d4 = int(d4) % 8

    def tf(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (dr, dc)

    # In the original frame the vertical line moves left and the horizontal line moves down.
    moves = [tf((0, -1)), tf((1, 0))]
    sh = 0
    sv = 0
    for dr, dc in moves:
        if dr == 0:
            sh = dc
        else:
            sv = dr
    bg = int(palette[0])
    gray = int(palette[5])

    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = ' + repr(bg))
    lines.append('GRAY = ' + repr(gray))
    lines.append('SH = ' + repr(int(sh)))
    lines.append('SV = ' + repr(int(sv)))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    rows = [y for y in range(H) if g[y, 0] != BG and g[y, 0] != GRAY and np.all(g[y] == g[y, 0])]')
    lines.append('    cols = [x for x in range(W) if g[0, x] != BG and g[0, x] != GRAY and np.all(g[:, x] == g[0, x])]')
    lines.append('    r = c = color = None')
    lines.append('    for yy in rows:')
    lines.append('        for xx in cols:')
    lines.append('            if g[yy, 0] == g[0, xx]:')
    lines.append('                r, c, color = yy, xx, int(g[yy, 0])')
    lines.append('                break')
    lines.append('        if color is not None:')
    lines.append('            break')
    lines.append('    if color is None:')
    lines.append('        return g.tolist()')
    lines.append('    n = int(np.sum((g != BG) & (g != color)))')
    lines.append('    nc = min(max(c + SH * n, 0), W - 1)')
    lines.append('    nr = min(max(r + SV * n, 0), H - 1)')
    lines.append('    out = np.full_like(g, BG)')
    lines.append('    out[:, nc] = color')
    lines.append('    out[nr, :] = color')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
