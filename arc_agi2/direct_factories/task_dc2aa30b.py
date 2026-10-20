def build_program(d4, palette):
    d4 = int(d4) % 8
    slots = []
    for i in range(9):
        R, C = 2 - i // 3, i % 3
        if d4 >= 4:
            C = 2 - C
        for _ in range(d4 % 4):
            R, C = C, 2 - R
        slots.append((R, C))
    div = int(palette[0])
    blue = int(palette[1])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('SLOTS = ' + repr(slots))
    lines.append('DIV = ' + repr(div))
    lines.append('COUNT_COLOUR = ' + repr(blue))
    lines.append('')
    lines.append('def _spans(cuts, n):')
    lines.append('    edges = [-1] + sorted(cuts) + [n]')
    lines.append('    out = []')
    lines.append('    for a, b in zip(edges[:-1], edges[1:]):')
    lines.append('        if b - a > 1:')
    lines.append('            out.append((a + 1, b - 1))')
    lines.append('    return out')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    rows = [y for y in range(H) if (g[y, :] == DIV).all()]')
    lines.append('    cols = [x for x in range(W) if (g[:, x] == DIV).all()]')
    lines.append('    ys = _spans(rows, H)')
    lines.append('    xs = _spans(cols, W)')
    lines.append('    if len(ys) != 3 or len(xs) != 3:')
    lines.append('        return g.tolist()')
    lines.append('    reading = [(R, C) for R in range(3) for C in range(3)]')
    lines.append('    pans = []')
    lines.append('    for R, C in reading:')
    lines.append('        (y0, y1), (x0, x1) = ys[R], xs[C]')
    lines.append('        pans.append(g[y0:y1 + 1, x0:x1 + 1].copy())')
    lines.append('    counts = [int((p == COUNT_COLOUR).sum()) for p in pans]')
    lines.append('    order = sorted(range(9), key=lambda k: counts[k])')
    lines.append('    out = g.copy()')
    lines.append('    for i, k in enumerate(order):')
    lines.append('        R, C = SLOTS[i]')
    lines.append('        (y0, y1), (x0, x1) = ys[R], xs[C]')
    lines.append('        p = pans[k]')
    lines.append('        if p.shape != (y1 - y0 + 1, x1 - x0 + 1):')
    lines.append('            return g.tolist()')
    lines.append('        out[y0:y1 + 1, x0:x1 + 1] = p')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
