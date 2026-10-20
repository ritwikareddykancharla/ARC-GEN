def build_program(d4, palette):
    # Original mechanism: every non-background cell shifts one step 'down' (dr=+1, dc=0)
    # and is recoloured red (2). Background is 0, object colour is 8.
    dr, dc = 1, 0
    if d4 >= 4:
        # reversing each row negates the column component
        dc = -dc
    for _ in range(d4 % 4):
        # clockwise rotation maps (r, c) -> (c, H-1-r), so a direction (dr, dc) -> (dc, -dr)
        dr, dc = dc, -dr
    bg = int(palette[0])
    new = int(palette[2])
    lines = [
        'import numpy as np',
        '',
        'BG = ' + repr(bg),
        'NEW = ' + repr(new),
        'DR = ' + repr(dr),
        'DC = ' + repr(dc),
        '',
        'def solve(demonstrations, grid):',
        '    g = np.asarray(grid, dtype=int)',
        '    h, w = g.shape',
        '    out = np.full((h, w), BG, dtype=int)',
        '    ys, xs = np.nonzero(g != BG)',
        '    for y, x in zip(ys.tolist(), xs.tolist()):',
        '        ny, nx = y + DR, x + DC',
        '        if 0 <= ny < h and 0 <= nx < w:',
        '            out[ny, nx] = NEW',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
