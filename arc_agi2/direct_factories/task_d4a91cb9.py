def build_program(d4, palette):
    pal = [int(palette[i]) for i in range(10)]
    c8 = pal[8]
    c2 = pal[2]
    c4 = pal[4]
    bg = pal[0]
    k = int(d4) % 4
    # A horizontal flip keeps the axes. Each clockwise quarter turn swaps them.
    # The original first leg is vertical, so it stays vertical when k is even
    # and becomes horizontal when k is odd.
    first_vertical = (k % 2 == 0)
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('ANCHOR = %d   # path starts here (original colour 8)' % c8)
    lines.append('TARGET = %d   # path ends here (original colour 2)' % c2)
    lines.append('PATH = %d     # path colour (original colour 4)' % c4)
    lines.append('BG = %d       # background (original colour 0)' % bg)
    lines.append('FIRST_LEG_VERTICAL = %s' % ('True' if first_vertical else 'False'))
    lines.append('')
    lines.append('def _paint_segment(g, r0, c0, r1, c1):')
    lines.append('    # Paint the straight segment from (r0,c0) to (r1,c1), both ends included.')
    lines.append('    # Only background cells are painted, so neither endpoint pixel is overwritten.')
    lines.append('    dr = (r1 > r0) - (r1 < r0)')
    lines.append('    dc = (c1 > c0) - (c1 < c0)')
    lines.append('    r, c = r0, c0')
    lines.append('    while True:')
    lines.append('        if g[r, c] == BG:')
    lines.append('            g[r, c] = PATH')
    lines.append('        if r == r1 and c == c1:')
    lines.append('            break')
    lines.append('        r += dr')
    lines.append('        c += dc')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int).copy()')
    lines.append('    pa = np.argwhere(g == ANCHOR)')
    lines.append('    pt = np.argwhere(g == TARGET)')
    lines.append('    if len(pa) == 0 or len(pt) == 0:')
    lines.append('        return g.tolist()')
    lines.append('    ra, ca = int(pa[0][0]), int(pa[0][1])')
    lines.append('    rt, ct = int(pt[0][0]), int(pt[0][1])')
    lines.append('    if FIRST_LEG_VERTICAL:')
    lines.append('        # Leave the anchor along its column until reaching the target row.')
    lines.append('        cr, cc = rt, ca')
    lines.append('    else:')
    lines.append('        # Leave the anchor along its row until reaching the target column.')
    lines.append('        cr, cc = ra, ct')
    lines.append('    _paint_segment(g, ra, ca, cr, cc)   # first leg: anchor to corner')
    lines.append('    _paint_segment(g, cr, cc, rt, ct)   # second leg: corner to target')
    lines.append('    return g.tolist()')
    return '\n'.join(lines) + '\n'
