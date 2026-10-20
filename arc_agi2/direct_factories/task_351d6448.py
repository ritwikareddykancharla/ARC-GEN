def build_program(d4, palette):
    d4 = int(d4)
    k = d4 % 4
    flip = d4 >= 4
    sep = int(palette[5])
    # Original geometry: separators are full rows, panels are read top->bottom,
    # and motion runs along the column axis.
    # Rotating clockwise k times: for odd k the separators become columns and
    # motion runs along visible rows.
    sep_cols = (k % 2 == 1)
    # Panel reading order is reversed for k = 1 (read right->left) and for
    # k = 2 (read bottom->top).
    panel_rev = k in (1, 2)
    # The motion axis is reversed for k in {2, 3}. A row flip reverses it again.
    axis_rev = (k in (2, 3)) != flip
    if axis_rev:
        scan = 'range(W - 1, -W, -1)'
    else:
        scan = 'range(-W + 1, W)'
    if not sep_cols:
        body = '''
    Hg, Wg = g.shape
    seps = [y for y in range(Hg) if (g[y] == SEP).all()]
    bounds = []
    start = 0
    for r in seps + [Hg]:
        if r > start:
            bounds.append((start, r))
        start = r + 1
    P = [g[a:b, :].copy() for a, b in bounds]
    REVLINE
    H, W = P[0].shape

    def changed(a, b):
        return set(int(x) for x in np.where((a != b).any(axis=0))[0])

    def cell(p, y, x):
        return int(p[y, x])

    def setcell(p, y, x, v):
        p[y, x] = v
'''
    else:
        body = '''
    Hg, Wg = g.shape
    seps = [x for x in range(Wg) if (g[:, x] == SEP).all()]
    bounds = []
    start = 0
    for c in seps + [Wg]:
        if c > start:
            bounds.append((start, c))
        start = c + 1
    P = [g[:, a:b].copy() for a, b in bounds]
    REVLINE
    W, H = P[0].shape

    def changed(a, b):
        return set(int(x) for x in np.where((a != b).any(axis=1))[0])

    def cell(p, y, x):
        return int(p[x, y])

    def setcell(p, y, x, v):
        p[x, y] = v
'''
    if panel_rev:
        body = body.replace('REVLINE', 'P = P[::-1]')
    else:
        body = body.replace('REVLINE', 'pass')
    tail = '''
    C = [changed(P[i], P[i + 1]) for i in range(len(P) - 1)]
    d = 0
    for cand in SCAN:
        if all(set(x + cand for x in C[i]) == C[i + 1] for i in range(len(C) - 1)):
            d = cand
            break

    def left(p, y, x):
        xx = x - d
        return cell(p, y, xx) if 0 <= xx < W else -1

    table = {}
    for i in range(len(P) - 1):
        for x in C[i]:
            for y in range(H):
                table[(cell(P[i], y, x), left(P[i], y, x))] = cell(P[i + 1], y, x)
    last = P[-1]
    out = last.copy()
    newC = [x + d for x in C[-1] if 0 <= x + d < W]
    for x in newC:
        for y in range(H):
            key = (cell(last, y, x), left(last, y, x))
            if key in table:
                setcell(out, y, x, table[key])
    return out.tolist()
'''.replace('SCAN', scan)
    prog = 'import numpy as np\n\nSEP = ' + str(sep) + '\n\n\ndef solve(demonstrations, grid):\n    g = np.array(grid, dtype=int)\n' + body + tail
    return prog
