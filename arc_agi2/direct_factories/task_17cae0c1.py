def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(palette[c]) for c in range(10)]

    def tf(m):
        m = [list(r) for r in m]
        if d4 >= 4:
            m = [r[::-1] for r in m]
        for _ in range(d4 % 4):
            m = [list(r) for r in zip(*m[::-1])]
        return tuple(tuple(int(v) for v in r) for r in m)

    base = {
        6: [[1, 1, 1], [0, 0, 0], [0, 0, 0]],
        1: [[0, 0, 0], [0, 0, 0], [1, 1, 1]],
        3: [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
        9: [[0, 0, 1], [0, 1, 0], [1, 0, 0]],
        4: [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
    }
    table = {}
    for col, m in base.items():
        table[tf(m)] = pal[col]

    vertical = (d4 % 4) % 2 == 1
    fg = pal[5]

    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('TABLE = ' + repr(table))
    lines.append('FG = ' + repr(fg))
    lines.append('VERTICAL = ' + repr(vertical))
    lines.append('')
    lines.append('def _panels(H, W):')
    lines.append('    res = []')
    lines.append('    if VERTICAL:')
    lines.append('        p = W')
    lines.append('        for i in range(H // p):')
    lines.append('            res.append((i * p, 0, p))')
    lines.append('    else:')
    lines.append('        p = H')
    lines.append('        for i in range(W // p):')
    lines.append('            res.append((0, i * p, p))')
    lines.append('    return res')
    lines.append('')
    lines.append('def _key(g, r0, c0, p):')
    lines.append('    sub = g[r0:r0 + p, c0:c0 + p]')
    lines.append('    return tuple(tuple(int(v) for v in row) for row in (sub == FG).astype(int))')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    table = dict(TABLE)')
    lines.append('    try:')
    lines.append('        for d in demonstrations or []:')
    lines.append('            gi = np.array(d["input"], dtype=int)')
    lines.append('            go = np.array(d["output"], dtype=int)')
    lines.append('            if gi.shape != go.shape:')
    lines.append('                continue')
    lines.append('            for (r0, c0, p) in _panels(*gi.shape):')
    lines.append('                k = _key(gi, r0, c0, p)')
    lines.append('                if k not in table:')
    lines.append('                    table[k] = int(go[r0, c0])')
    lines.append('    except Exception:')
    lines.append('        pass')
    lines.append('    out = g.copy()')
    lines.append('    for (r0, c0, p) in _panels(H, W):')
    lines.append('        k = _key(g, r0, c0, p)')
    lines.append('        if k in table:')
    lines.append('            col = table[k]')
    lines.append('        else:')
    lines.append('            best = None')
    lines.append('            col = None')
    lines.append('            a = np.array(k)')
    lines.append('            for kk, cc in table.items():')
    lines.append('                b = np.array(kk)')
    lines.append('                if b.shape != a.shape:')
    lines.append('                    continue')
    lines.append('                dist = int(np.sum(a != b))')
    lines.append('                if best is None or dist < best:')
    lines.append('                    best = dist')
    lines.append('                    col = cc')
    lines.append('            if col is None:')
    lines.append('                continue')
    lines.append('        out[r0:r0 + p, c0:c0 + p] = col')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
