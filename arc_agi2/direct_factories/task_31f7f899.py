def build_program(d4, palette):
    bg = int(palette[8])
    line = int(palette[6])
    d4 = int(d4) % 8
    rev_h = d4 in (1, 2, 4, 5)
    rev_v = d4 in (2, 3, 5, 6)
    src = '''import numpy as np

BG = __BG__
LINE = __LINE__
REV_H = __REVH__
REV_V = __REVV__


def _runs(seq):
    groups = []
    n = len(seq)
    i = 0
    while i < n:
        if seq[i] != LINE:
            c = seq[i]
            i0 = i
            while i < n and seq[i] == c:
                i += 1
            groups.append((i0, i - 1, c))
        else:
            i += 1
    return groups


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    rows = [y for y in range(H) if np.all(g[y, :] != BG)]
    if rows:
        # horizontal divider: vertical bars, ordered along columns
        ly = rows[0]
        groups = _runs(g[ly, :].tolist())
        exts = []
        for x0, x1, c in groups:
            t = ly
            while t - 1 >= 0 and g[t - 1, x0] == c:
                t -= 1
            b = ly
            while b + 1 < H and g[b + 1, x0] == c:
                b += 1
            exts.append((t, b))
            for y in range(t, b + 1):
                if y != ly:
                    out[y, x0:x1 + 1] = BG
        order = sorted(exts, key=lambda e: e[1] - e[0])
        targets = list(reversed(groups)) if REV_H else list(groups)
        for (x0, x1, c), (t, b) in zip(targets, order):
            out[t:b + 1, x0:x1 + 1] = c
        return out.tolist()
    cols = [x for x in range(W) if np.all(g[:, x] != BG)]
    if not cols:
        return g.tolist()
    # vertical divider: horizontal bars, ordered along rows
    lx = cols[0]
    groups = _runs(g[:, lx].tolist())
    exts = []
    for y0, y1, c in groups:
        l = lx
        while l - 1 >= 0 and g[y0, l - 1] == c:
            l -= 1
        r = lx
        while r + 1 < W and g[y0, r + 1] == c:
            r += 1
        exts.append((l, r))
        for x in range(l, r + 1):
            if x != lx:
                out[y0:y1 + 1, x] = BG
    order = sorted(exts, key=lambda e: e[1] - e[0])
    targets = list(reversed(groups)) if REV_V else list(groups)
    for (y0, y1, c), (l, r) in zip(targets, order):
        out[y0:y1 + 1, l:r + 1] = c
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg)).replace('__LINE__', str(line))
    src = src.replace('__REVH__', 'True' if rev_h else 'False').replace('__REVV__', 'True' if rev_v else 'False')
    return src
