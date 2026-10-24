"""Diagonal trails from a corner tile (d13f3404), reviewed for the broader RE-ARC domain.

Rule (native constructor and RE-ARC ``generate_d13f3404``): the input sits in
one corner of a canvas twice its size. At most one pixel lies on each
diagonal, and each pixel extends as a trail away from that corner to the
canvas edge. The corner and the trail direction move with the D4 index.

The earlier factory fixed the background to palette[0]. RE-ARC samples the
background, and pixels are at most one per diagonal, so the background is
read as the strict modal input colour (ties raise an error). It fills the
output canvas, as in both constructors.
"""


def build_program(d4, palette):
    # Track where the original top-left output corner (which holds the input) ends up.
    # The corner is (cr, cc); 1 means the far side (bottom row or right column).
    cr, cc = 0, 0
    if d4 >= 4:
        # reverse each row: horizontal mirror
        cc = 1 - cc
    for _ in range(d4 % 4):
        # clockwise rotation: corner (r, c) -> (c, 1 - r)
        cr, cc = cc, 1 - cr
    # The trail always runs diagonally away from the corner that holds the input.
    dr = 1 - 2 * cr
    dc = 1 - 2 * cc
    lines = [
        'import numpy as np',
        '',
        'CORNER_BOTTOM = %d' % cr,
        'CORNER_RIGHT = %d' % cc,
        'DR = %d' % dr,
        'DC = %d' % dc,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    h, w = g.shape',
        '    values, counts = np.unique(g, return_counts=True)',
        '    order = np.argsort(-counts, kind="stable")',
        '    if len(values) > 1 and counts[order[0]] == counts[order[1]]:',
        '        raise ValueError("Expected a unique modal background")',
        '    BG = int(values[order[0]])',
        '    H, W = 2 * h, 2 * w',
        '    out = np.full((H, W), BG, dtype=int)',
        '    r0 = h if CORNER_BOTTOM else 0',
        '    c0 = w if CORNER_RIGHT else 0',
        '    for y in range(h):',
        '        for x in range(w):',
        '            col = int(g[y, x])',
        '            if col == BG:',
        '                continue',
        '            r = y + r0',
        '            c = x + c0',
        '            while 0 <= r < H and 0 <= c < W:',
        '                out[r, c] = col',
        '                r += DR',
        '                c += DC',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
