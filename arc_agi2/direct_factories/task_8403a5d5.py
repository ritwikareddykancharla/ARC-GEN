"""Seed-to-stripes expansion (8403a5d5), reviewed for the broader RE-ARC domain.

Rule (native constructor and RE-ARC ``generate_8403a5d5``): one seed pixel on
the near edge starts stripes on every second line towards one side.
Grey markers alternate between the far and near ends of the lines in
between. Grey is fixed by both constructors (palette[5]), and the stripe
direction moves with the D4 index.

The earlier factory assumed the palette[0] background, falling back to the modal
colour only when palette[0] was absent. RE-ARC samples the background and seed
colours, so a seed coloured palette[0] was treated as background. The
background is now the colour of every cell except the single seed; any
other input is rejected.
"""


def build_program(d4, palette):
    def tf(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc
    pr, pc = tf((0, 1))
    dr, dc = tf((1, 0))
    gray = int(palette[5])
    header = (
        'PR = ' + repr(int(pr)) + '\n'
        'PC = ' + repr(int(pc)) + '\n'
        'DR = ' + repr(int(dr)) + '\n'
        'DC = ' + repr(int(dc)) + '\n'
        'GRAY = ' + repr(gray) + '\n'
    )
    body = '''
import numpy as np
from collections import Counter

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    # RE-ARC samples the background, so it is read as the modal colour; the
    # input has exactly one seed cell on a canvas of at least 3x3.
    values, counts = np.unique(g, return_counts=True)
    if len(values) != 2 or min(counts) != 1:
        raise ValueError("Expected one seed cell on a uniform background")
    bg = int(values[int(np.argmax(counts))])
    ys, xs = np.nonzero(g != bg)
    sr, sc = int(ys[0]), int(xs[0])
    color = int(g[sr, sc])
    # stripes run along the seed-edge/far-edge axis; progress steps along PR,PC
    if DR == 1:
        far_r, near_r = 0, h - 1
    elif DR == -1:
        far_r, near_r = h - 1, 0
    else:
        far_r = near_r = None
    if DC == 1:
        far_c, near_c = 0, w - 1
    elif DC == -1:
        far_c, near_c = w - 1, 0
    else:
        far_c = near_c = None
    k = 0
    r, c = sr, sc
    while 0 <= r < h and 0 <= c < w:
        if k % 2 == 0:
            if DR != 0:
                out[:, c] = color
            else:
                out[r, :] = color
        else:
            gi = k // 2
            if DR != 0:
                rr = far_r if gi % 2 == 0 else near_r
                out[rr, c] = GRAY
            else:
                cc = far_c if gi % 2 == 0 else near_c
                out[r, cc] = GRAY
        k += 1
        r += PR
        c += PC
    return out.tolist()
'''
    return header + body
