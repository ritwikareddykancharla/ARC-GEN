def build_program(d4, palette):
    d4 = int(d4) % 8
    # Original mechanism: the anchor is the extreme row in the +row (down) direction.
    # Every cell moves in the -col (left) direction by its distance from that anchor row.
    ar, ac = 1, 0
    sr, sc = 0, -1
    if d4 >= 4:
        # A horizontal reflection negates column components.
        ac = -ac
        sc = -sc
    for _ in range(d4 % 4):
        # A clockwise rotation maps direction (dr, dc) to (dc, -dr).
        ar, ac = ac, -ar
        sr, sc = sc, -sr
    bg = int(palette[0])
    lines = [
        'import numpy as np',
        '',
        '# Anchor direction: the shape line that is extreme along this direction stays fixed.',
        'AR = %d' % ar,
        'AC = %d' % ac,
        '# Shear direction: each cell slides this way by its distance from the anchor line.',
        'SR = %d' % sr,
        'SC = %d' % sc,
        'BG = %d' % bg,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    out = np.full_like(g, BG)',
        '    rs, cs = np.nonzero(g != BG)',
        '    if len(rs) == 0:',
        '        return out.tolist()',
        '    proj = rs * AR + cs * AC',
        '    amax = int(proj.max())',
        '    for r, c, p in zip(rs.tolist(), cs.tolist(), proj.tolist()):',
        '        d = amax - int(p)',
        '        nr = r + d * SR',
        '        nc = c + d * SC',
        '        if 0 <= nr < H and 0 <= nc < W:',
        '            out[nr, nc] = g[r, c]',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
