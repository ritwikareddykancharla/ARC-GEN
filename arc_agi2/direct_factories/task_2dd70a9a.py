def build_program(d4, palette):
    def _rot_cw(d):
        return (d[1], -d[0])

    def _map_dir(d):
        if d4 >= 4:
            d = (d[0], -d[1])
        for _ in range(d4 % 4):
            d = _rot_cw(d)
        return d

    a = [_map_dir(d) for d in [(0, 1), (0, -1)]]
    b = [_map_dir(d) for d in [(1, 0), (-1, 0)]]
    if a[0][0] == 0:
        hord, vord = a, b
    else:
        hord, vord = b, a
    green = int(palette[3])
    red = int(palette[2])
    lines = [
        'import numpy as np',
        'from collections import Counter, deque',
        '',
        'GREEN = %d' % green,
        'RED = %d' % red,
        'HORD = %r' % (hord,),
        'VORD = %r' % (vord,),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])',
        '    out = g.copy()',
        '    green = [(int(y), int(x)) for y, x in zip(*np.where(g == GREEN))]',
        '    red = set((int(y), int(x)) for y, x in zip(*np.where(g == RED)))',
        '    if not green:',
        '        return out.tolist()',
        '    ghoriz = len({c[0] for c in green}) == 1',
        '    rhoriz = len({c[0] for c in red}) == 1',
        '    gaxis = list(HORD) if ghoriz else list(VORD)',
        '    raxis = set(HORD) if rhoriz else set(VORD)',
        '',
        '    def ok(y, x):',
        '        return 0 <= y < H and 0 <= x < W and g[y, x] == bg',
        '',
        '    def slide(p, d):',
        '        cells = [p]',
        '        while ok(p[0] + d[0], p[1] + d[1]):',
        '            p = (p[0] + d[0], p[1] + d[1])',
        '            cells.append(p)',
        '        return cells',
        '',
        '    q = deque()',
        '    seen = set()',
        '    for d in gaxis:',
        '        end = max(green, key=lambda c: c[0] * d[0] + c[1] * d[1])',
        '        s = (end[0] + d[0], end[1] + d[1])',
        '        if ok(*s):',
        '            q.append((s, d, []))',
        '    found = None',
        '    while q:',
        '        s, d, legs = q.popleft()',
        '        if (s, d) in seen:',
        '            continue',
        '        seen.add((s, d))',
        '        cells = slide(s, d)',
        '        legs2 = legs + [(d, cells)]',
        '        last = cells[-1]',
        '        if d in raxis and (last[0] + d[0], last[1] + d[1]) in red:',
        '            found = legs2',
        '            break',
        '        turns = VORD if d[0] == 0 else HORD',
        '        for nd in turns:',
        '            n = (last[0] + nd[0], last[1] + nd[1])',
        '            if ok(*n):',
        '                q.append((n, nd, legs2))',
        '    if found is None:',
        '        return out.tolist()',
        '    for d, cells in found:',
        '        for p in cells:',
        '            out[p] = GREEN',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
