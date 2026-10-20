_TEMPLATE = '''import numpy as np
from collections import Counter

# Marker line and growth direction in VISIBLE coordinates.
# LINE_IS_ROW: the marker bars lie on a grid row (True) or a grid column (False).
# LINE_AT_END: the marker line is the last row/column (True) or the first (False).
# GROW: step along the stacking axis (row index if LINE_IS_ROW, else column index)
#       that moves away from the marker line.
LINE_IS_ROW = @ROW@
LINE_AT_END = @END@
GROW = @GROW@
MARK_RECOLOUR = @C2@
MARK_EXTEND = @C3@
NEW_COLOUR = @C5@


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    if LINE_IS_ROW:
        n_along, n_across = H, W
    else:
        n_along, n_across = W, H
    L = n_along - 1 if LINE_AT_END else 0

    def yx(p, q):
        # p indexes the stacking axis, q indexes the axis that runs along the marker line
        return (p, q) if LINE_IS_ROW else (q, p)

    cnt = Counter()
    for p in range(n_along):
        if p == L:
            continue
        for q in range(n_across):
            cnt[int(g[yx(p, q)])] += 1
    if not cnt:
        return g.tolist()
    bg = cnt.most_common(1)[0][0]

    line = [int(g[yx(L, q)]) for q in range(n_across)]
    runs = []
    q = 0
    while q < n_across:
        c = line[q]
        if c == bg:
            q += 1
            continue
        q0 = q
        while q < n_across and line[q] == c:
            q += 1
        runs.append((c, q0, q - 1))

    def segments(q0, q1):
        occ = [p for p in range(n_along) if p != L and any(int(g[yx(p, qq)]) != bg for qq in range(q0, q1 + 1))]
        segs = []
        for p in occ:
            if segs and p == segs[-1][1] + 1:
                segs[-1][1] = p
            else:
                segs.append([p, p])
        return segs

    out = g.copy()
    for q in range(n_across):
        out[yx(L, q)] = bg

    total = 0
    for c, q0, q1 in runs:
        if c == MARK_RECOLOUR:
            total += len(segments(q0, q1))
            for p in range(n_along):
                if p == L:
                    continue
                for qq in range(q0, q1 + 1):
                    if int(g[yx(p, qq)]) != bg:
                        out[yx(p, qq)] = NEW_COLOUR

    for c, q0, q1 in runs:
        if c != MARK_EXTEND:
            continue
        segs = segments(q0, q1)
        if not segs:
            continue
        far = segs[0] if GROW < 0 else segs[-1]
        cells = [(p, qq) for p in range(far[0], far[1] + 1) for qq in range(q0, q1 + 1) if int(g[yx(p, qq)]) != bg]
        if not cells:
            continue
        colour = Counter(int(g[yx(p, qq)]) for p, qq in cells).most_common(1)[0][0]
        if len(segs) > 1:
            pitch = abs(segs[1][0] - segs[0][0])
        else:
            pitch = far[1] - far[0] + 2
        for k in range(1, total + 1):
            for p, qq in cells:
                np_ = p + GROW * pitch * k
                if 0 <= np_ < n_along and np_ != L:
                    out[yx(np_, qq)] = colour
    return out.tolist()
'''


def build_program(d4, palette):
    r = int(d4) % 4
    # The canonical marker row is the bottom row and stacks grow upward.
    # A row reversal leaves both unchanged. Each clockwise turn moves the
    # edge bottom -> left -> top -> right.
    cfg = {
        0: (True, True, -1),
        1: (False, False, 1),
        2: (True, False, 1),
        3: (False, True, -1),
    }[r]
    row, end, grow = cfg
    src = _TEMPLATE
    src = src.replace('@ROW@', repr(bool(row)))
    src = src.replace('@END@', repr(bool(end)))
    src = src.replace('@GROW@', repr(int(grow)))
    src = src.replace('@C2@', repr(int(palette[2])))
    src = src.replace('@C3@', repr(int(palette[3])))
    src = src.replace('@C5@', repr(int(palette[5])))
    return src
