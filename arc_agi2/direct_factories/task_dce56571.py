def _axis_map(d4):
    # Track where each ORIGINAL axis (0=rows, 1=cols) lands in VISIBLE coordinates,
    # and whether its direction is reversed.
    # state[orig_axis] = [visible_axis, reversed]
    state = {0: [0, False], 1: [1, False]}
    if d4 >= 4:
        # reverse each row: whichever original axis sits on visible axis 1 is reversed
        for k in state:
            if state[k][0] == 1:
                state[k][1] = not state[k][1]
    for _ in range(d4 % 4):
        # clockwise rotation: (r, c) -> (c, h-1-r)
        # visible axis 1 -> new axis 0 (same direction); visible axis 0 -> new axis 1 (reversed)
        for k in state:
            if state[k][0] == 1:
                state[k][0] = 0
            else:
                state[k][0] = 1
                state[k][1] = not state[k][1]
    return state


def build_program(d4, palette):
    d4 = int(d4) % 8
    st = _axis_map(d4)
    line_axis = st[1][0]          # visible axis the line runs along
    along_rev = bool(st[1][1])    # is the along-line direction reversed
    cross_rev = bool(st[0][1])    # is the cross (middle row) direction reversed
    bg = int(palette[8])
    src = '''import numpy as np

BG = __BG__
# LINE_AXIS == 1: the line is horizontal (runs along a row).
# LINE_AXIS == 0: the line is vertical (runs along a column).
LINE_AXIS = __LA__
ALONG_REV = __AR__
CROSS_REV = __CR__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    mask = g != BG
    n = int(mask.sum())
    out = np.full_like(g, BG)
    if n == 0:
        return out.tolist()
    vals, counts = np.unique(g[mask], return_counts=True)
    hue = int(vals[int(np.argmax(counts))])
    if LINE_AXIS == 1:
        L, C = W, H
    else:
        L, C = H, W
    # middle line across the cross axis
    cross = (C - 1) // 2 if CROSS_REV else C // 2
    m = min(n, L)
    # centred placement along the line axis
    start = (L - m + 1) // 2 if ALONG_REV else (L - m) // 2
    if start < 0:
        start = 0
    if LINE_AXIS == 1:
        out[cross, start:start + m] = hue
    else:
        out[start:start + m, cross] = hue
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg))
    src = src.replace('__LA__', str(int(line_axis)))
    src = src.replace('__AR__', 'True' if along_rev else 'False')
    src = src.replace('__CR__', 'True' if cross_rev else 'False')
    return src
