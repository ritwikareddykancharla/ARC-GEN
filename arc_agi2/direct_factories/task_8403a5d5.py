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
    bg = int(palette[0])
    gray = int(palette[5])
    header = (
        'PR = ' + repr(int(pr)) + '\n'
        'PC = ' + repr(int(pc)) + '\n'
        'DR = ' + repr(int(dr)) + '\n'
        'DC = ' + repr(int(dc)) + '\n'
        'BG = ' + repr(bg) + '\n'
        'GRAY = ' + repr(gray) + '\n'
    )
    body = '''
import numpy as np
from collections import Counter

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    bg = BG
    if not np.any(g == bg):
        bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    ys, xs = np.nonzero(g != bg)
    if len(ys) == 0:
        return out.tolist()
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
