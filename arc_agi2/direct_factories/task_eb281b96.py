def build_program(d4, palette):
    # Native mechanism: the input band is anchored at the top (row 0 side) and the
    # zigzag keeps bouncing downward: append rows h-2..0, then 1..h-1, then h-2..0.
    # Track where the native row axis (the stacking axis) and its row-0 end go
    # under the D4 map. A row-reversal (d4>=4) only flips native columns, so it
    # does not affect the stacking axis. One clockwise turn maps old row r to new
    # column n-1-r (axis becomes columns, direction reversed). It maps old column c
    # to new row c (axis becomes rows, direction kept).
    k = d4 % 4
    if k == 0:
        axis, anchor_start = 0, True    # vertical, input at top, grows downward
    elif k == 1:
        axis, anchor_start = 1, False   # horizontal, input at right, grows leftward
    elif k == 2:
        axis, anchor_start = 0, False   # vertical, input at bottom, grows upward
    else:
        axis, anchor_start = 1, True    # horizontal, input at left, grows rightward
    lines = [
        'import numpy as np',
        '',
        'AXIS = ' + str(axis),
        'ANCHOR_AT_START = ' + str(anchor_start),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    n = g.shape[AXIS]',
        '    if n < 2:',
        '        return g.tolist()',
        '    def take(idx):',
        '        return np.take(g, idx, axis=AXIS)',
        '    canvas = g.copy()',
        '    if ANCHOR_AT_START:',
        '        # band sits at the low-index end; the zigzag keeps bouncing toward higher indices',
        '        back = list(range(n - 2, -1, -1))',
        '        fwd = list(range(1, n))',
        '        for idx in (back, fwd, back):',
        '            canvas = np.concatenate([canvas, take(idx)], axis=AXIS)',
        '    else:',
        '        # band sits at the high-index end; the zigzag keeps bouncing toward lower indices',
        '        back = list(range(n - 1, 0, -1))',
        '        fwd = list(range(0, n - 1))',
        '        for idx in (back, fwd, back):',
        '            canvas = np.concatenate([take(idx), canvas], axis=AXIS)',
        '    return canvas.tolist()',
        '',
    ]
    return '\n'.join(lines)
