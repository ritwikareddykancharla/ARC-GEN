def build_program(d4, palette):
    H, W = 5, 9
    k = d4 % 4
    flip = d4 >= 4

    def mp(r, c):
        h, w = H, W
        if flip:
            c = w - 1 - c
        for _ in range(k):
            r, c = c, h - 1 - r
            h, w = w, h
        return r, c

    key_orig = [(r, c) for r in range(1, 4) for c in range(1, 4)]
    pat_orig = [(r, c) for r in range(1, 4) for c in range(5, 8)]
    kv = [mp(r, c) for r, c in key_orig]
    pv = [mp(r, c) for r, c in pat_orig]
    kr0 = min(p[0] for p in kv)
    kc0 = min(p[1] for p in kv)
    pr0 = min(p[0] for p in pv)
    pc0 = min(p[1] for p in pv)

    stem = [(1, 2), (2, 2), (3, 2)]
    extras = {1: [(1, 1), (1, 3)], 2: [(1, 1), (3, 3)], 3: [(3, 1), (1, 3)]}
    table = {}
    for col, ex in extras.items():
        cells = []
        for (r, c) in stem + ex:
            vr, vc = mp(r, c)
            cells.append((vr - kr0, vc - kc0))
        table[tuple(sorted(cells))] = int(palette[col])

    bg = int(palette[0])
    fallback = int(palette[1])

    src = []
    src.append('BG = %r' % bg)
    src.append('KR, KC = %r, %r' % (kr0, kc0))
    src.append('PR, PC = %r, %r' % (pr0, pc0))
    src.append('TABLE = %r' % table)
    src.append('FALLBACK = %r' % fallback)
    src.append('')
    src.append('def _shape(g, r0, c0):')
    src.append('    cells = []')
    src.append('    for i in range(3):')
    src.append('        for j in range(3):')
    src.append('            if g[r0 + i][c0 + j] != BG:')
    src.append('                cells.append((i, j))')
    src.append('    return tuple(sorted(cells))')
    src.append('')
    src.append('def _pair(d):')
    src.append('    if isinstance(d, dict):')
    src.append('        return d.get("input"), d.get("output")')
    src.append('    return d[0], d[1]')
    src.append('')
    src.append('def solve(demonstrations, grid):')
    src.append('    g = [list(row) for row in grid]')
    src.append('    ks = _shape(g, KR, KC)')
    src.append('    col = TABLE.get(ks)')
    src.append('    if col is None:')
    src.append('        for d in demonstrations or []:')
    src.append('            try:')
    src.append('                di, do = _pair(d)')
    src.append('                if _shape([list(r) for r in di], KR, KC) != ks:')
    src.append('                    continue')
    src.append('                found = None')
    src.append('                for row in do:')
    src.append('                    for v in row:')
    src.append('                        if v != BG:')
    src.append('                            found = v')
    src.append('                            break')
    src.append('                    if found is not None:')
    src.append('                        break')
    src.append('                if found is not None:')
    src.append('                    col = found')
    src.append('                    break')
    src.append('            except Exception:')
    src.append('                continue')
    src.append('    if col is None:')
    src.append('        col = FALLBACK')
    src.append('    out = []')
    src.append('    for i in range(3):')
    src.append('        row = []')
    src.append('        for j in range(3):')
    src.append('            row.append(col if g[PR + i][PC + j] != BG else BG)')
    src.append('        out.append(row)')
    src.append('    return out')
    return '\n'.join(src) + '\n'
