TEMPLATE = '''import numpy as np
from collections import Counter

BG = __BG__
PAT = __PAT__
DIV = __DIV__


def _spans(cuts, n):
    out = []
    prev = -1
    for c in sorted(cuts) + [n]:
        if c - prev > 1:
            out.append((prev + 1, c - 1))
        prev = c
    return out


def _key_of(panel):
    cnt = Counter(v for v in panel.ravel().tolist() if v not in (BG, PAT, DIV))
    if not cnt:
        return None
    best = max(cnt.values())
    tops = [v for v, k in cnt.items() if k == best]
    if len(tops) != 1:
        return None
    return tops[0]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    drows = [y for y in range(H) if (g[y, :] == DIV).all()]
    dcols = [x for x in range(W) if (g[:, x] == DIV).all()]
    ys = _spans(drows, H)
    xs = _spans(dcols, W)
    out = g.copy()
    keys = {}
    pats = []
    for i, (y0, y1) in enumerate(ys):
        for j, (x0, x1) in enumerate(xs):
            p = g[y0:y1 + 1, x0:x1 + 1]
            k = _key_of(p)
            if k is not None:
                keys[(i, j)] = k
            elif (p == PAT).any():
                pats.append((i, j))
    krows = set(a for a, b in keys)
    kcols = set(b for a, b in keys)
    for (i, j) in pats:
        colour = None
        if len(krows) == 1 and len(kcols) >= 2:
            colour = keys.get((next(iter(krows)), j))
        elif len(kcols) == 1 and len(krows) >= 2:
            colour = keys.get((i, next(iter(kcols))))
        if colour is None:
            cands = set(keys[(i, jj)] for jj in range(len(xs)) if (i, jj) in keys)
            cands |= set(keys[(ii, j)] for ii in range(len(ys)) if (ii, j) in keys)
            if len(cands) == 1:
                colour = cands.pop()
        if colour is None:
            continue
        y0, y1 = ys[i]
        x0, x1 = xs[j]
        sub = out[y0:y1 + 1, x0:x1 + 1]
        sub[g[y0:y1 + 1, x0:x1 + 1] == PAT] = colour
    return out.tolist()
'''


def build_program(d4, palette):
    pal = [int(c) for c in palette]
    if len(pal) < 10:
        raise ValueError('palette must map all 10 colours')
    if int(d4) < 0 or int(d4) > 7:
        raise ValueError('d4 must be in 0..7')
    src = TEMPLATE
    src = src.replace('__BG__', str(pal[0]))
    src = src.replace('__PAT__', str(pal[1]))
    src = src.replace('__DIV__', str(pal[4]))
    return src
