def build_program(d4, palette):
    dr, dc = 0, 1
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    horizontal = (dr == 0)
    step = dc if horizontal else dr
    header = (
        'ONE = ' + repr(int(palette[1])) + '\n'
        'EIGHT = ' + repr(int(palette[8])) + '\n'
        'FILL = ' + repr(int(palette[0])) + '\n'
        'AXIS_H = ' + repr(bool(horizontal)) + '\n'
        'STEP = ' + repr(int(step)) + '\n'
    )
    body = '''

def _pad(seg, w):
    extra = [FILL] * (w - len(seg))
    # padding goes on the side toward the 8 (end of the original segment)
    if STEP > 0:
        return list(seg) + extra
    return extra + list(seg)


def solve(demonstrations, grid):
    g = [list(r) for r in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    segs = []
    if AXIS_H:
        # 1 -> 8 runs along a row; rows scanned top to bottom
        for y in range(H):
            xs = range(W) if STEP > 0 else range(W - 1, -1, -1)
            for x in xs:
                if g[y][x] == ONE:
                    t = x + STEP
                    while 0 <= t < W and g[y][t] != EIGHT:
                        t += STEP
                    if 0 <= t < W:
                        lo, hi = min(x, t), max(x, t)
                        segs.append(g[y][lo + 1:hi])
        if not segs:
            return [[FILL]]
        w = max(len(s) for s in segs)
        if w == 0:
            return [[FILL]]
        return [_pad(s, w) for s in segs]
    else:
        # 1 -> 8 runs along a column; columns scanned left to right
        for x in range(W):
            ys = range(H) if STEP > 0 else range(H - 1, -1, -1)
            for y in ys:
                if g[y][x] == ONE:
                    t = y + STEP
                    while 0 <= t < H and g[t][x] != EIGHT:
                        t += STEP
                    if 0 <= t < H:
                        lo, hi = min(y, t), max(y, t)
                        segs.append([g[k][x] for k in range(lo + 1, hi)])
        if not segs:
            return [[FILL]]
        h = max(len(s) for s in segs)
        if h == 0:
            return [[FILL]]
        cols = [_pad(s, h) for s in segs]
        return [[cols[i][r] for i in range(len(cols))] for r in range(h)]
'''
    return header + body
