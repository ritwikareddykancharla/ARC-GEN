def build_program(d4, palette):
    div = int(palette[0])
    src = '''import numpy as np
from collections import Counter

DIV = %d

def _spans(n, cuts):
    out = []
    prev = -1
    for c in sorted(cuts) + [n]:
        if c - prev > 1:
            out.append((prev + 1, c - 1))
        prev = c
    return out

def _lattice(g):
    H, W = g.shape
    if H >= 6 and W >= 6 and (H - 1) %% 5 == 0 and (W - 1) %% 5 == 0:
        ys = [(5 * k + 1, 5 * k + 4) for k in range((H - 1) // 5)]
        xs = [(5 * k + 1, 5 * k + 4) for k in range((W - 1) // 5)]
        return ys, xs
    rc = [y for y in range(H) if (g[y] == DIV).all()]
    cc = [x for x in range(W) if (g[:, x] == DIV).all()]
    return _spans(H, rc), _spans(W, cc)

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    ys, xs = _lattice(g)
    if not ys or not xs:
        return out.tolist()
    th = ys[0][1] - ys[0][0] + 1
    tw = xs[0][1] - xs[0][0] + 1
    ys = [s for s in ys if s[1] - s[0] + 1 == th]
    xs = [s for s in xs if s[1] - s[0] + 1 == tw]
    if th < 3 or tw < 3:
        return out.tolist()
    frame = Counter()
    inner = Counter()
    for (y0, y1) in ys:
        for (x0, x1) in xs:
            for i in range(th):
                for j in range(tw):
                    v = int(g[y0 + i, x0 + j])
                    if i == 0 or j == 0 or i == th - 1 or j == tw - 1:
                        frame[v] += 1
                    else:
                        inner[v] += 1
    bg = frame.most_common(1)[0][0]
    cand = [(n, v) for v, n in inner.items() if v != bg]
    if not cand:
        return out.tolist()
    cand.sort(key=lambda t: (-t[0], t[1]))
    fg = cand[0][1]
    groups = {}
    for tr, (y0, y1) in enumerate(ys):
        for tc, (x0, x1) in enumerate(xs):
            for i in range(1, th - 1):
                for j in range(1, tw - 1):
                    v = int(g[y0 + i, x0 + j])
                    if v != bg and v != fg:
                        groups.setdefault((v, i, j), []).append((tr, tc))
    for (v, i, j), tiles in groups.items():
        n = len(tiles)
        for a in range(n):
            for b in range(a + 1, n):
                r1, c1 = tiles[a]
                r2, c2 = tiles[b]
                if r1 == r2:
                    for tc in range(min(c1, c2), max(c1, c2) + 1):
                        out[ys[r1][0] + i, xs[tc][0] + j] = v
                elif c1 == c2:
                    for tr in range(min(r1, r2), max(r1, r2) + 1):
                        out[ys[tr][0] + i, xs[c1][0] + j] = v
    return out.tolist()
''' % div
    return src
