def build_program(d4, palette):
    border = int(palette[8])
    ink = int(palette[2])
    template = '''import numpy as np
from collections import Counter

BORDER = __BORDER__
INK = __INK__


def _prefix(mask):
    h, w = mask.shape
    p = np.zeros((h + 1, w + 1), dtype=int)
    p[1:, 1:] = mask.astype(int).cumsum(0).cumsum(1)
    return p


def _rs(p, y0, x0, y1, x1):
    if y1 <= y0 or x1 <= x0:
        return 0
    return int(p[y1, x1] - p[y0, x1] - p[y1, x0] + p[y0, x0])


def _candidates(g):
    h, w = g.shape
    twos = _prefix(g == INK)
    bad = _prefix((g != INK) & (g != BORDER))
    non_b = _prefix(g != BORDER)
    out = []
    for k in range(3, min(h, w) + 1):
        for y in range(h - k + 1):
            for x in range(w - k + 1):
                y1 = y + k - 1
                x1 = x + k - 1
                if _rs(twos, y + 1, x + 1, y1, x1) == 0:
                    continue
                if _rs(bad, y + 1, x + 1, y1, x1):
                    continue
                if _rs(non_b, y, x, y + k, x + k) != _rs(non_b, y + 1, x + 1, y1, x1):
                    continue
                key = tuple(tuple(int(v) for v in row) for row in g[y + 1:y1, x + 1:x1])
                out.append((y, x, k, key))
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    cands = _candidates(g)
    if not cands:
        return [list(map(int, row)) for row in g]
    cnt = Counter(c[3] for c in cands)
    uniq = [c for c in cands if cnt[c[3]] == 1]
    if not uniq:
        uniq = list(cands)
    if len(uniq) > 1:
        rep_sides = [c[2] for c in cands if cnt[c[3]] > 1]
        if rep_sides:
            s = max(rep_sides)
            pref = [c for c in uniq if c[2] == s]
            if pref:
                uniq = pref
    uniq.sort(key=lambda c: (c[2], c[0], c[1]))
    y, x, k, _ = uniq[0]
    return [list(map(int, row)) for row in g[y:y + k, x:x + k]]
'''
    return template.replace('__BORDER__', str(border)).replace('__INK__', str(ink))
