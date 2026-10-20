def build_program(d4, palette):
    d4 = int(d4) % 8
    bg = int(palette[0])
    fill = int(palette[2])
    # Find which visible direction the original top and left edges map to.
    # Use a small non-square index grid of the original cells.
    H0, W0 = 2, 3
    A = [[r * W0 + c for c in range(W0)] for r in range(H0)]
    if d4 >= 4:
        A = [row[::-1] for row in A]
    for _ in range(d4 % 4):
        h = len(A)
        w = len(A[0])
        A = [[A[h - 1 - j][i] for j in range(h)] for i in range(w)]
    pos = {}
    for i, row in enumerate(A):
        for j, v in enumerate(row):
            pos[v] = (i, j)
    p00 = pos[0]
    p10 = pos[W0]
    p01 = pos[1]
    row_anchor_max = False
    col_anchor_max = False
    for (q, _name) in ((p10, 'r'), (p01, 'c')):
        dr = q[0] - p00[0]
        dc = q[1] - p00[1]
        if dr != 0:
            row_anchor_max = dr < 0
        else:
            col_anchor_max = dc < 0
    lines = []
    lines.append('import numpy as np')
    lines.append('BG = %d' % bg)
    lines.append('FILL = %d' % fill)
    lines.append('ROW_ANCHOR_MAX = %s' % ('True' if row_anchor_max else 'False'))
    lines.append('COL_ANCHOR_MAX = %s' % ('True' if col_anchor_max else 'False'))
    lines.append('S = 4')
    lines.append('')
    lines.append('def _paint(g, out, tiles):')
    lines.append('    for (y, x) in tiles:')
    lines.append('        tile = g[y:y + S, x:x + S]')
    lines.append('        block = out[y:y + S, x:x + S]')
    lines.append('        block[tile == BG] = FILL')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    out = g.copy()')
    lines.append('    mask = g != BG')
    lines.append('    ys, xs = np.nonzero(mask)')
    lines.append('    if len(ys) == 0:')
    lines.append('        return out.tolist()')
    lines.append('    if ROW_ANCHOR_MAX:')
    lines.append('        pr = (int(ys.max()) - (S - 1)) % S')
    lines.append('    else:')
    lines.append('        pr = int(ys.min()) % S')
    lines.append('    if COL_ANCHOR_MAX:')
    lines.append('        pc = (int(xs.max()) - (S - 1)) % S')
    lines.append('    else:')
    lines.append('        pc = int(xs.min()) % S')
    lines.append('    best = None')
    lines.append('    for r0 in range(S):')
    lines.append('        for c0 in range(S):')
    lines.append('            covered = np.zeros_like(mask)')
    lines.append('            tiles = []')
    lines.append('            for y in range(r0, H - S + 1, S):')
    lines.append('                for x in range(c0, W - S + 1, S):')
    lines.append('                    covered[y:y + S, x:x + S] = True')
    lines.append('                    if mask[y:y + S, x:x + S].any():')
    lines.append('                        tiles.append((y, x))')
    lines.append('            if (mask & ~covered).any():')
    lines.append('                continue')
    lines.append('            inexact = int(not (r0 == 0 and H % S == 0)) + int(not (c0 == 0 and W % S == 0))')
    lines.append('            anchor_miss = int(r0 != pr) + int(c0 != pc)')
    lines.append('            key = (inexact, len(tiles), anchor_miss, r0, c0)')
    lines.append('            if best is None or key < best[0]:')
    lines.append('                best = (key, tiles)')
    lines.append('    if best is not None:')
    lines.append('        _paint(g, out, best[1])')
    lines.append('        return out.tolist()')
    lines.append('    tiles = []')
    lines.append('    for y in range(pr, H, S):')
    lines.append('        for x in range(pc, W, S):')
    lines.append('            if mask[y:y + S, x:x + S].any():')
    lines.append('                tiles.append((y, x))')
    lines.append('    _paint(g, out, tiles)')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
