def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(x) for x in palette]
    # Track where the original +column direction (left cell -> right cell) points in visible coordinates.
    dr, dc = 0, 1
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    along_rows = (dr == 0)
    anchor_low = (dr + dc) > 0
    bg = pal[0]
    a1, a2 = pal[4], pal[7]
    b1, b2 = pal[1], pal[8]
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('PARTNERS = (frozenset((%d, %d)), frozenset((%d, %d)))' % (a1, a2, b1, b2))
    lines.append('ALONG_ROWS = %r' % along_rows)
    lines.append('ANCHOR_LOW = %r' % anchor_low)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int).copy()')
    lines.append('    H, W = g.shape')
    lines.append('    nlines = H if ALONG_ROWS else W')
    lines.append('    length = W if ALONG_ROWS else H')
    lines.append('    def get(i, k):')
    lines.append('        return int(g[i, k]) if ALONG_ROWS else int(g[k, i])')
    lines.append('    def put(i, k, v):')
    lines.append('        if ALONG_ROWS:')
    lines.append('            g[i, k] = v')
    lines.append('        else:')
    lines.append('            g[k, i] = v')
    lines.append('    step = 1 if ANCHOR_LOW else -1')
    lines.append('    for i in range(nlines):')
    lines.append('        ks = [k for k in range(length) if get(i, k) != BG]')
    lines.append('        if not ANCHOR_LOW:')
    lines.append('            ks = ks[::-1]')
    lines.append('        for a, b in zip(ks, ks[1:]):')
    lines.append('            ca, cb = get(i, a), get(i, b)')
    lines.append('            if ca == BG or cb == BG:')
    lines.append('                continue')
    lines.append('            if frozenset((ca, cb)) in PARTNERS and abs(b - a) > 1:')
    lines.append('                put(i, b, BG)')
    lines.append('                put(i, a + step, cb)')
    lines.append('    return g.tolist()')
    return '\n'.join(lines) + '\n'
