def build_program(d4, palette):
    k = int(d4) % 4
    flip = int(d4) >= 4
    side = ['L', 'T', 'R', 'B'][((2 if flip else 0) + k) % 4]
    bg = int(palette[0])
    div = int(palette[5])
    lines = []
    lines.append('BG = %d' % bg)
    lines.append('DIV = %d' % div)
    lines.append('')
    if side in ('L', 'R'):
        rng = '0, d' if side == 'L' else 'd + 1, w'
        lines += [
            'def _divider(g, h, w):',
            '    cands = [x for x in range(w) if all(g[y][x] == DIV for y in range(h))]',
            '    if not cands:',
            '        return w // 2',
            '    return min(cands, key=lambda x: (abs(2 * x - (w - 1)), x))',
            '',
            'def solve(demonstrations, grid):',
            '    g = [[int(v) for v in row] for row in grid]',
            '    h = len(g)',
            '    w = len(g[0])',
            '    d = _divider(g, h, w)',
            '    out = []',
            '    for y in range(h):',
            '        row = []',
            '        for x in range(' + rng + '):',
            '            v = g[y][x]',
            '            xm = 2 * d - x',
            '            if 0 <= xm < w and g[y][xm] != BG:',
            '                v = g[y][xm]',
            '            row.append(v)',
            '        out.append(row)',
            '    return out',
        ]
    else:
        rng = '0, d' if side == 'T' else 'd + 1, h'
        lines += [
            'def _divider(g, h, w):',
            '    cands = [y for y in range(h) if all(v == DIV for v in g[y])]',
            '    if not cands:',
            '        return h // 2',
            '    return min(cands, key=lambda y: (abs(2 * y - (h - 1)), y))',
            '',
            'def solve(demonstrations, grid):',
            '    g = [[int(v) for v in row] for row in grid]',
            '    h = len(g)',
            '    w = len(g[0])',
            '    d = _divider(g, h, w)',
            '    out = []',
            '    for y in range(' + rng + '):',
            '        ym = 2 * d - y',
            '        row = []',
            '        for x in range(w):',
            '            v = g[y][x]',
            '            if 0 <= ym < h and g[ym][x] != BG:',
            '                v = g[ym][x]',
            '            row.append(v)',
            '        out.append(row)',
            '    return out',
        ]
    return '\n'.join(lines) + '\n'
