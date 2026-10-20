def build_program(d4, palette):
    k = int(d4) % 8
    mask = int(palette[7])

    def fwd(y, x, n):
        # forward D4 action on an n x n grid: optional row reversal, then k%4 clockwise turns
        if k >= 4:
            x = n - 1 - x
        for _ in range(k % 4):
            y, x = x, n - 1 - y
        return (y, x)

    def analyse(n):
        inv = {}
        for y in range(-8, n + 8):
            for x in range(-8, n + 8):
                inv[fwd(y, x, n)] = (y, x)
        s = n + 1
        pi, pj = 5, 8
        y, x = inv[(pi, pj)]
        rsum = None
        csum = None
        for q in (fwd(s - y, x, n), fwd(y, s - x, n)):
            if q[1] == pj and q[0] != pi:
                rsum = pi + q[0]
            elif q[0] == pi and q[1] != pj:
                csum = pj + q[1]
        if rsum is None or csum is None:
            raise ValueError('could not derive mirror sums')
        t = fwd(x, y, n)
        if t == (pj, pi):
            anti = False
        elif t == (n - 1 - pj, n - 1 - pi):
            anti = True
        else:
            raise ValueError('unexpected diagonal cue')
        return (rsum - n, csum - n, anti)

    first = analyse(30)
    second = analyse(20)
    if first != second:
        raise ValueError('mirror geometry is not size-uniform')
    roff, coff, anti = first

    lines = [
        'import numpy as np',
        'from collections import Counter',
        '',
        'MASK = %d' % mask,
        'ROW_OFF = %d' % roff,
        'COL_OFF = %d' % coff,
        'ANTI = %s' % ('True' if anti else 'False'),
        '',
        'def _pick(counter):',
        '    best = None',
        '    for colour, cnt in counter.items():',
        '        if best is None or cnt > best[1] or (cnt == best[1] and colour < best[0]):',
        '            best = (colour, cnt)',
        '    return best[0]',
        '',
        'def solve(demonstrations, grid):',
        '    a = np.asarray(grid, dtype=int)',
        '    if a.ndim != 2 or a.size == 0:',
        '        return [list(r) for r in grid]',
        '    h, w = a.shape',
        '    rs = h + ROW_OFF',
        '    cs = w + COL_OFF',
        '    def key(i, j):',
        '        return (min(i, rs - i), min(j, cs - j))',
        '    def diag(i, j):',
        '        if ANTI:',
        '            return (w - 1 - j, h - 1 - i)',
        '        return (j, i)',
        '    hidden = (a == MASK)',
        '    ys, xs = np.nonzero(hidden)',
        '    if len(ys) == 0:',
        '        return a.tolist()',
        '    r0, r1 = int(ys.min()), int(ys.max())',
        '    c0, c1 = int(xs.min()), int(xs.max())',
        '    votes = {}',
        '    total = Counter()',
        '    for i in range(h):',
        '        for j in range(w):',
        '            if hidden[i, j]:',
        '                continue',
        '            v = int(a[i, j])',
        '            votes.setdefault(key(i, j), Counter())[v] += 1',
        '            total[v] += 1',
        '    default = _pick(total) if total else MASK',
        '    out = []',
        '    for i in range(r0, r1 + 1):',
        '        row = []',
        '        for j in range(c0, c1 + 1):',
        '            if not hidden[i, j]:',
        '                row.append(int(a[i, j]))',
        '                continue',
        '            k1 = key(i, j)',
        '            if k1 in votes:',
        '                row.append(_pick(votes[k1]))',
        '                continue',
        '            k2 = key(*diag(i, j))',
        '            if k2 in votes:',
        '                row.append(_pick(votes[k2]))',
        '                continue',
        '            row.append(default)',
        '        out.append(row)',
        '    return out',
    ]
    return '\n'.join(lines) + '\n'
