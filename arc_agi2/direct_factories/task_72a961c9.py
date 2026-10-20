def build_program(d4, palette):
    # Original mechanism: a full-width horizontal line (colour 1) on background 0,
    # with markers 8 (stalk of 2 line-cells + 8 cap) and 2 (stalk of 3 line-cells + 2 cap)
    # growing toward decreasing row index (upward).
    # D4: reflection (reverse each row) leaves 'up' unchanged; each clockwise rotation
    # maps direction (dr, dc) -> (dc, -dr): up -> right -> down -> left.
    dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    dr, dc = dirs[d4 % 4]
    bg = int(palette[0])
    line = int(palette[1])
    c8 = int(palette[8])
    c2 = int(palette[2])
    lengths = {c8: 2, c2: 3}
    src = []
    src.append('import numpy as np')
    src.append('')
    src.append('BG = ' + repr(bg))
    src.append('LINE = ' + repr(line))
    src.append('LENGTHS = ' + repr(lengths))
    src.append('DR = ' + repr(dr))
    src.append('DC = ' + repr(dc))
    src.append('')
    src.append('def solve(demonstrations, grid):')
    src.append('    g = np.array(grid, dtype=int)')
    src.append('    H, W = g.shape')
    src.append('    out = g.copy()')
    src.append('    if DR != 0:')
    src.append('        # stalks move vertically, so the line is a row')
    src.append('        counts = (g != BG).sum(axis=1)')
    src.append('        r = int(np.argmax(counts))')
    src.append('        cells = [(r, x) for x in range(W)]')
    src.append('    else:')
    src.append('        # stalks move horizontally, so the line is a column')
    src.append('        counts = (g != BG).sum(axis=0)')
    src.append('        c = int(np.argmax(counts))')
    src.append('        cells = [(y, c) for y in range(H)]')
    src.append('    for (y, x) in cells:')
    src.append('        v = int(g[y, x])')
    src.append('        if v == BG or v == LINE or v not in LENGTHS:')
    src.append('            continue')
    src.append('        L = LENGTHS[v]')
    src.append('        for k in range(1, L + 1):')
    src.append('            yy = y + DR * k')
    src.append('            xx = x + DC * k')
    src.append('            if 0 <= yy < H and 0 <= xx < W:')
    src.append('                out[yy, xx] = LINE')
    src.append('        yy = y + DR * (L + 1)')
    src.append('        xx = x + DC * (L + 1)')
    src.append('        if 0 <= yy < H and 0 <= xx < W:')
    src.append('            out[yy, xx] = v')
    src.append('    return out.tolist()')
    return '\n'.join(src) + '\n'
