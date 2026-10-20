def build_program(d4, palette):
    pal = [int(palette[c]) for c in range(10)]
    MARK = pal[4]
    A0 = pal[0]
    A8 = pal[8]
    B6 = pal[6]
    B7 = pal[7]
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('MARK = %d' % MARK)
    lines.append('TOGGLE = {%d: %d, %d: %d, %d: %d, %d: %d}' % (A0, A8, A8, A0, B6, B7, B7, B6))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    src = g.copy()')
    lines.append('    H, W = g.shape')
    lines.append('    out = g.copy()')
    lines.append('    cells = []')
    lines.append('    # top-bottom facing marker pairs in the same column')
    lines.append('    if H >= 2:')
    lines.append('        for x in range(W):')
    lines.append('            if src[0, x] == MARK and src[H - 1, x] == MARK:')
    lines.append('                for y in range(1, H - 1):')
    lines.append('                    cells.append((y, x))')
    lines.append('    # left-right facing marker pairs in the same row')
    lines.append('    if W >= 2:')
    lines.append('        for y in range(H):')
    lines.append('            if src[y, 0] == MARK and src[y, W - 1] == MARK:')
    lines.append('                for x in range(1, W - 1):')
    lines.append('                    cells.append((y, x))')
    lines.append('    for (y, x) in cells:')
    lines.append('        v = int(out[y, x])')
    lines.append('        if v in TOGGLE:')
    lines.append('            out[y, x] = TOGGLE[v]')
    lines.append('    return out.astype(int).tolist()')
    return '\n'.join(lines) + '\n'
