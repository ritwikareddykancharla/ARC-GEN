def build_program(d4, palette):
    vr, hc = 0, 0
    if d4 >= 4:
        hc = 1 - hc
    for _ in range(d4 % 4):
        vr, hc = hc, 1 - vr
    div = int(palette[5])
    c1 = int(palette[1])
    c2 = int(palette[2])
    c3 = int(palette[3])
    lines = [
        'import numpy as np',
        'DIV = ' + str(div),
        'C_FIRST = ' + str(c1),
        'C_MID = ' + str(c2),
        'C_LAST = ' + str(c3),
        'VR = ' + str(vr),
        'HC = ' + str(hc),
        '',
        'def _bands(n, divs):',
        '    res = []',
        '    cur = []',
        '    for i in range(n):',
        '        if i in divs:',
        '            if cur:',
        '                res.append(cur)',
        '            cur = []',
        '        else:',
        '            cur.append(i)',
        '    if cur:',
        '        res.append(cur)',
        '    return res',
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    out = g.copy()',
        '    H, W = g.shape',
        '    drows = set(y for y in range(H) if np.all(g[y, :] == DIV))',
        '    dcols = set(x for x in range(W) if np.all(g[:, x] == DIV))',
        '    rb = _bands(H, drows)',
        '    cb = _bands(W, dcols)',
        '    if not rb or not cb:',
        '        return out.tolist()',
        '    ra = rb[-1] if VR else rb[0]',
        '    rz = rb[0] if VR else rb[-1]',
        '    ca = cb[-1] if HC else cb[0]',
        '    cz = cb[0] if HC else cb[-1]',
        '    rm = rb[len(rb) // 2]',
        '    cm = cb[len(cb) // 2]',
        '    for rows, cols, col in ((ra, ca, C_FIRST), (rm, cm, C_MID), (rz, cz, C_LAST)):',
        '        for y in rows:',
        '            for x in cols:',
        '                out[y, x] = col',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
