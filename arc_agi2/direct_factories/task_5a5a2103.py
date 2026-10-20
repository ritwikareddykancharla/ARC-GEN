def build_program(d4, palette):
    d4 = int(d4) % 8
    k = d4 % 4
    start = 2 if d4 >= 4 else 0
    side = ['L', 'T', 'R', 'B'][(start + k) % 4]
    bg = int(palette[0])
    src = '''import numpy as np
from collections import Counter

SIDE = %r
BG = %d

def _spans(cuts, n):
    edges = [-1] + sorted(cuts) + [n]
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        if b - a > 1:
            out.append((a + 1, b - 1))
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = BG
    rcuts = [y for y in range(H) if g[y, 0] != bg and (g[y] == g[y, 0]).all()]
    ccuts = [x for x in range(W) if g[0, x] != bg and (g[:, x] == g[0, x]).all()]
    ys = _spans(rcuts, H)
    xs = _spans(ccuts, W)
    if not ys or not xs:
        return g.tolist()
    groups = []
    if SIDE in ('L', 'R'):
        kx = xs[0] if SIDE == 'L' else xs[-1]
        for yspan in ys:
            groups.append(((yspan, kx), [(yspan, xsp) for xsp in xs]))
    else:
        ky = ys[0] if SIDE == 'T' else ys[-1]
        for xspan in xs:
            groups.append(((ky, xspan), [(ysp, xspan) for ysp in ys]))
    keyset = set(kp for kp, _ in groups)
    colours = []
    for kp, _ in groups:
        (y0, y1), (x0, x1) = kp
        sub = g[y0:y1 + 1, x0:x1 + 1]
        vals = [int(v) for v in sub.ravel() if v != bg]
        colours.append(Counter(vals).most_common(1)[0][0] if vals else bg)
    mask = None
    for yspan in ys:
        for xspan in xs:
            if (yspan, xspan) in keyset:
                continue
            (y0, y1), (x0, x1) = yspan, xspan
            sub = g[y0:y1 + 1, x0:x1 + 1]
            if np.any(sub != bg):
                mask = sub != bg
                break
        if mask is not None:
            break
    out = g.copy()
    for yspan in ys:
        for xspan in xs:
            out[yspan[0]:yspan[1] + 1, xspan[0]:xspan[1] + 1] = bg
    if mask is None:
        return out.tolist()
    for (kp, members), c in zip(groups, colours):
        for (y0, y1), (x0, x1) in members:
            h = min(mask.shape[0], y1 - y0 + 1)
            w = min(mask.shape[1], x1 - x0 + 1)
            reg = out[y0:y0 + h, x0:x0 + w]
            reg[mask[:h, :w]] = c
    return out.tolist()
''' % (side, bg)
    return src
