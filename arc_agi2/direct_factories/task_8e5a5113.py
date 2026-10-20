def build_program(d4, palette):
    d4 = int(d4) % 8
    gray = int(palette[5])
    # Direction from the source panel toward the other panels.
    # Before the transform it points right; a reflection makes it point left.
    if d4 < 4:
        dr, dc = 0, 1
    else:
        dr, dc = 0, -1
    # Each clockwise turn maps right->down, down->left, left->up, up->right.
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    horizontal = (dr == 0)
    forward = ((dc if horizontal else dr) > 0)
    # The base rule turns panel k clockwise k times. Rotations commute with
    # rotations; a reflection reverses the turning sense. np.rot90(P, -1) turns clockwise.
    rot = -1 if d4 < 4 else 1
    src = '''import numpy as np

GRAY = __GRAY__
HORIZONTAL = __HORIZONTAL__
FORWARD = __FORWARD__
ROT = __ROT__


def _segments(n, divs):
    segs = []
    start = 0
    for x in list(divs) + [n]:
        if x > start:
            segs.append((start, x - 1))
        start = x + 1
    return segs


def _fallback_segments(n, s):
    # Expected layout along the panel axis: s cells, divider, s cells, divider, s cells.
    if n == 3 * s + 2:
        return [(0, s - 1), (s + 1, 2 * s), (2 * s + 2, 3 * s + 1)]
    return []


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    if HORIZONTAL:
        # Panels sit side by side; the dividers are full grey columns.
        divs = [x for x in range(W) if np.all(g[:, x] == GRAY)]
        segs = _segments(W, divs)
        if len(segs) < 2:
            segs = _fallback_segments(W, H)
        if len(segs) < 2:
            return out.tolist()
        if not FORWARD:
            segs = segs[::-1]
        a0, b0 = segs[0]
        P = g[:, a0:b0 + 1]
        for k, (a, b) in enumerate(segs[1:], start=1):
            R = np.rot90(P, ROT * k)
            if R.shape == (H, b - a + 1):
                out[:, a:b + 1] = R
    else:
        # Panels are stacked; the dividers are full grey rows.
        divs = [y for y in range(H) if np.all(g[y, :] == GRAY)]
        segs = _segments(H, divs)
        if len(segs) < 2:
            segs = _fallback_segments(H, W)
        if len(segs) < 2:
            return out.tolist()
        if not FORWARD:
            segs = segs[::-1]
        a0, b0 = segs[0]
        P = g[a0:b0 + 1, :]
        for k, (a, b) in enumerate(segs[1:], start=1):
            R = np.rot90(P, ROT * k)
            if R.shape == (b - a + 1, W):
                out[a:b + 1, :] = R
    return out.tolist()
'''
    src = src.replace('__GRAY__', str(gray))
    src = src.replace('__HORIZONTAL__', 'True' if horizontal else 'False')
    src = src.replace('__FORWARD__', 'True' if forward else 'False')
    src = src.replace('__ROT__', str(rot))
    return src
