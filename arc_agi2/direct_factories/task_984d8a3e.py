def build_program(d4, palette):
    d = int(d4) % 8
    # Original rows run left->right from the left-colour edge to the right-colour edge.
    # Flip (d>=4) reverses each row; each clockwise turn maps rows to columns.
    # d=0: rows, start at col 0   d=1: cols, start at row 0
    # d=2: rows, start at col W-1 d=3: cols, start at row H-1
    # d=4: rows, start at col W-1 d=5: cols, start at row H-1
    # d=6: rows, start at col 0   d=7: cols, start at row 0
    lines_are_rows = (d % 2 == 0)
    start_low = d in (0, 1, 6, 7)
    template = '''import numpy as np
from collections import Counter

# Lines are visible rows if True, visible columns if False.
LINES_ARE_ROWS = __ROWS__
# True: the left-colour run touches index 0 of each line (left column / top row).
# False: it touches the last index (right column / bottom row).
START_LOW = __LOW__


def _major(vals):
    return Counter(int(v) for v in vals).most_common(1)[0][0]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    if LINES_ARE_ROWS:
        nl, n = H, W
    else:
        nl, n = W, H
    # Visible indices along each line, walking away from the left-colour edge.
    if START_LOW:
        order = list(range(n))
    else:
        order = list(range(n - 1, -1, -1))
    first, last = order[0], order[-1]
    # Colour roles come from the visible edges. The edge touched by the start
    # run carries the start colour. The opposite edge carries the end colour.
    if LINES_ARE_ROWS:
        lc = _major(g[:, first])
        rc = _major(g[:, last])
    else:
        lc = _major(g[first, :])
        rc = _major(g[last, :])
    others = sorted(set(int(v) for v in g.ravel()) - {lc, rc})
    mc = others[0] if others else _major(g.ravel())

    def at(i, p):
        j = order[p]
        if LINES_ARE_ROWS:
            return (i, j)
        return (j, i)

    info = []
    for i in range(nl):
        L = 0
        while L < n and g[at(i, L)] == lc:
            L += 1
        rs = n
        while rs > 0 and g[at(i, rs - 1)] == rc:
            rs -= 1
        info.append((L, rs))
    m = min(rs for _, rs in info)
    out = g.copy()
    for i, (L, rs) in enumerate(info):
        k = max(0, min(L, rs - m))
        if k == 0:
            continue
        # The middle run slides k cells toward the start edge and keeps its width.
        for p in range(L - k, rs - k):
            out[at(i, p)] = mc
        # The k removed start-colour cells now sit against the end run.
        for p in range(rs - k, rs):
            out[at(i, p)] = lc
    return out.tolist()
'''
    return template.replace('__ROWS__', 'True' if lines_are_rows else 'False').replace('__LOW__', 'True' if start_low else 'False')
