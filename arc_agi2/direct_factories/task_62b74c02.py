def build_program(d4, palette):
    bg = int(palette[0])
    k = d4 % 4
    if d4 < 4:
        side = ['L', 'T', 'R', 'B'][k]
    else:
        side = ['R', 'B', 'L', 'T'][k]
    header = (
        'import numpy as np\n'
        'BG = %d\n'
        'def solve(demonstrations, grid):\n'
        '    g = np.array(grid, dtype=int)\n'
        '    h, w = g.shape\n'
        '    out = g.copy()\n'
    ) % bg
    if side == 'L':
        body = (
            '    cols = [x for x in range(w) if np.any(g[:, x] != BG)]\n'
            '    if not cols:\n'
            '        return out.tolist()\n'
            '    p = max(cols) + 1\n'
            '    edge = g[:, p - 1].copy()\n'
            '    for x in range(p, w - p):\n'
            '        out[:, x] = edge\n'
            '    for j in range(p):\n'
            '        if 0 <= w - p + j < w:\n'
            '            out[:, w - p + j] = g[:, j]\n'
            '    return out.tolist()\n'
        )
    elif side == 'R':
        body = (
            '    cols = [x for x in range(w) if np.any(g[:, x] != BG)]\n'
            '    if not cols:\n'
            '        return out.tolist()\n'
            '    s = min(cols)\n'
            '    p = w - s\n'
            '    edge = g[:, s].copy()\n'
            '    for x in range(p, w - p):\n'
            '        out[:, x] = edge\n'
            '    for j in range(p):\n'
            '        out[:, j] = g[:, s + j]\n'
            '    return out.tolist()\n'
        )
    elif side == 'T':
        body = (
            '    rows = [y for y in range(h) if np.any(g[y, :] != BG)]\n'
            '    if not rows:\n'
            '        return out.tolist()\n'
            '    p = max(rows) + 1\n'
            '    edge = g[p - 1, :].copy()\n'
            '    for y in range(p, h - p):\n'
            '        out[y, :] = edge\n'
            '    for j in range(p):\n'
            '        if 0 <= h - p + j < h:\n'
            '            out[h - p + j, :] = g[j, :]\n'
            '    return out.tolist()\n'
        )
    else:
        body = (
            '    rows = [y for y in range(h) if np.any(g[y, :] != BG)]\n'
            '    if not rows:\n'
            '        return out.tolist()\n'
            '    s = min(rows)\n'
            '    p = h - s\n'
            '    edge = g[s, :].copy()\n'
            '    for y in range(p, h - p):\n'
            '        out[y, :] = edge\n'
            '    for j in range(p):\n'
            '        out[j, :] = g[s + j, :]\n'
            '    return out.tolist()\n'
        )
    return header + body
