def build_program(d4, palette):
    legend = {(0, 1): 2, (1, 0): 4, (1, 1): 6, (1, 2): 3, (2, 1): 1}
    vis = {}
    for (ri, ci), col in legend.items():
        r, c = ri, ci
        if d4 >= 4:
            c = 2 - c
        for _ in range(d4 % 4):
            r, c = c, 2 - r
        vis[(r, c)] = int(palette[col])
    div = int(palette[8])
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('DIV = %d' % div)
    lines.append('BG = %d' % bg)
    lines.append('FILL = %r' % (vis,))
    lines.append('')
    lines.append('def _find(g, colour):')
    lines.append('    H, W = g.shape')
    lines.append('    rows = [y for y in range(H) if (g[y] == colour).all()]')
    lines.append('    cols = [x for x in range(W) if (g[:, x] == colour).all()]')
    lines.append('    return rows, cols')
    lines.append('')
    lines.append('def _spans(lines_, n):')
    lines.append('    edges = [-1] + list(lines_) + [n]')
    lines.append('    return [(edges[i] + 1, edges[i + 1] - 1) for i in range(len(edges) - 1)]')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = g.copy()')
    lines.append('    H, W = g.shape')
    lines.append('    rows, cols = _find(g, DIV)')
    lines.append('    if len(rows) != 2 or len(cols) != 2:')
    lines.append('        for colour in sorted(set(g.ravel().tolist())):')
    lines.append('            if colour == BG:')
    lines.append('                continue')
    lines.append('            r2, c2 = _find(g, colour)')
    lines.append('            if len(r2) == 2 and len(c2) == 2:')
    lines.append('                rows, cols = r2, c2')
    lines.append('                break')
    lines.append('    if len(rows) != 2 or len(cols) != 2:')
    lines.append('        return out.tolist()')
    lines.append('    rs = _spans(sorted(rows), H)')
    lines.append('    cs = _spans(sorted(cols), W)')
    lines.append('    for (ri, ci), colour in FILL.items():')
    lines.append('        y0, y1 = rs[ri]')
    lines.append('        x0, x1 = cs[ci]')
    lines.append('        if y0 > y1 or x0 > x1:')
    lines.append('            continue')
    lines.append('        out[y0:y1 + 1, x0:x1 + 1] = colour')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
