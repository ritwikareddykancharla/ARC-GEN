def build_program(d4, palette):
    bg = int(palette[0])
    rows_axis = (d4 % 4) in (0, 2)
    if rows_axis:
        n_expr = 'g.shape[0]'
        line_expr = 'g[i, :]'
        assign = 'out[k, :] = g[a + b - k, :]'
        axis_note = 'Bands are horizontal row blocks; each is mirrored top-to-bottom.'
    else:
        n_expr = 'g.shape[1]'
        line_expr = 'g[:, i]'
        assign = 'out[:, k] = g[:, a + b - k]'
        axis_note = 'Bands are vertical column blocks; each is mirrored left-to-right.'
    src = '''import numpy as np

# AXIS_NOTE
BG = BG_VALUE


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    n = N_EXPR
    keys = []
    for i in range(n):
        line = LINE_EXPR
        keys.append(frozenset(int(v) for v in np.unique(line) if int(v) != BG))
    a = 0
    while a < n:
        if not keys[a]:
            a += 1
            continue
        b = a
        while b + 1 < n and keys[b + 1] == keys[a]:
            b += 1
        for k in range(a, b + 1):
            ASSIGN
        a = b + 1
    return out.tolist()
'''
    src = src.replace('AXIS_NOTE', axis_note)
    src = src.replace('BG_VALUE', str(bg))
    src = src.replace('N_EXPR', n_expr)
    src = src.replace('LINE_EXPR', line_expr)
    src = src.replace('ASSIGN', assign)
    return src
