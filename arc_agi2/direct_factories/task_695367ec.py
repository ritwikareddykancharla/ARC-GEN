def build_program(d4, palette):
    d4 = int(d4) % 8
    k = d4 % 4
    # Each entry says whether the visible row axis / column axis is reversed
    # compared with the original lattice coordinates on the 15x15 canvas.
    # For d4 >= 4, each row is first reversed: (r, c) -> (r, 14 - c).
    # Each clockwise rotation then maps (r, c) -> (c, 14 - r).
    # The lattice is symmetric under swapping axes, so only the per-axis
    # reversal flags matter.
    table = {
        0: (False, False),
        1: (False, True),
        2: (True, True),
        3: (True, False),
        4: (False, True),
        5: (True, True),
        6: (True, False),
        7: (False, False),
    }
    rev_r, rev_c = table[d4]
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('from collections import Counter')
    lines.append('')
    lines.append('REV_R = %r' % (rev_r,))
    lines.append('REV_C = %r' % (rev_c,))
    lines.append('BG = %d' % bg)
    lines.append('SIZE = 15')
    lines.append('')
    lines.append('def _is_line(i, n, rev):')
    lines.append('    j = (SIZE - 1 - i) if rev else i')
    lines.append('    return j % (n + 1) == n')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    n = int(min(h, w))')
    lines.append('    cnt = Counter(g.ravel().tolist())')
    lines.append('    col = int(cnt.most_common(1)[0][0])')
    lines.append('    out = np.full((SIZE, SIZE), BG, dtype=int)')
    lines.append('    for y in range(SIZE):')
    lines.append('        if _is_line(y, n, REV_R):')
    lines.append('            out[y, :] = col')
    lines.append('    for x in range(SIZE):')
    lines.append('        if _is_line(x, n, REV_C):')
    lines.append('            out[:, x] = col')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
