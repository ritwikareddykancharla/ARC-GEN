def build_program(d4, palette):
    # Where the original top-left corner (holding colour 7) ends up after the D4 transform.
    H, W = 7, 7
    r, c = 0, 0
    if d4 >= 4:
        c = W - 1 - c
    for _ in range(d4 % 4):
        r, c, H, W = c, H - 1 - r, W, H
    def_r = 0 if r == 0 else 1
    def_c = 0 if c == 0 else 1
    corner_col = int(palette[7])
    mark_col = int(palette[2])
    lines = [
        'import numpy as np',
        '',
        'CORNER = %d' % corner_col,
        'MARK = %d' % mark_col,
        'DEF_R_AT_END = %d' % def_r,
        'DEF_C_AT_END = %d' % def_c,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    cands = [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]',
        '    found = []',
        '    for p in cands:',
        '        if g[p[0], p[1]] == CORNER and p not in found:',
        '            found.append(p)',
        '    if len(found) == 1:',
        '        cr, cc = found[0]',
        '    else:',
        '        cr = H - 1 if DEF_R_AT_END else 0',
        '        cc = W - 1 if DEF_C_AT_END else 0',
        '    # The picture is everything outside the corner row and corner column.',
        '    inner = np.delete(np.delete(g, cr, axis=0), cc, axis=1)',
        '    # A marker in the corner row sets the shift along rows. A marker in the corner column sets the shift along columns.',
        '    row_marks = [x for x in range(W) if x != cc and g[cr, x] == MARK]',
        '    col_marks = [y for y in range(H) if y != cr and g[y, cc] == MARK]',
        '    sh = (min(abs(x - cc) for x in row_marks) - 1) if row_marks else 0',
        '    sv = (min(abs(y - cr) for y in col_marks) - 1) if col_marks else 0',
        '    # The roll always moves away from the corner.',
        '    dir_h = 1 if cc == 0 else -1',
        '    dir_v = 1 if cr == 0 else -1',
        '    out = np.roll(inner, dir_v * sv, axis=0)',
        '    out = np.roll(out, dir_h * sh, axis=1)',
        '    return out.astype(int).tolist()',
        '',
    ]
    return '\n'.join(lines)
