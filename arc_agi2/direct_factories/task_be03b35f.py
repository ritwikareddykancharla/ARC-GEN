def build_program(d4, palette):
    d4 = int(d4) % 8
    mark = int(palette[2])
    # Corner bands of the original source block: bottom-left = (row band 1, col band 0)
    r, c = 1, 0
    if d4 >= 4:
        c = 1 - c  # reverse each row
    for _ in range(d4 % 4):
        r, c = c, 1 - r  # rotate clockwise
    # Clockwise turn stays clockwise under rotations; reflections make it counter-clockwise
    k = -1 if d4 < 4 else 1
    lines = [
        'import numpy as np',
        '',
        'MARK = %d' % mark,
        'SRC_ROW_BAND = %d' % r,
        'SRC_COL_BAND = %d' % c,
        'ROT_K = %d' % k,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    ys, xs = np.where(g == MARK)',
        '    if len(ys) == 0:',
        '        h, w = 2, 2',
        '    else:',
        '        h = int(ys.max() - ys.min() + 1)',
        '        w = int(xs.max() - xs.min() + 1)',
        '    r0 = 0 if SRC_ROW_BAND == 0 else H - h',
        '    c0 = 0 if SRC_COL_BAND == 0 else W - w',
        '    blk = g[r0:r0 + h, c0:c0 + w]',
        '    return np.rot90(blk, k=ROT_K).astype(int).tolist()',
        '',
    ]
    return '\n'.join(lines)
