def build_program(d4, palette):
    div_colour = int(palette[0])
    noise_colour = int(palette[5])
    template = '''import numpy as np
from collections import Counter

DIV = __DIV__
NOISE = __NOISE__


def _is_divider(line):
    return bool(np.all((line == DIV) | (line == NOISE)) and np.any(line == DIV))


def _spans(divs, n):
    out = []
    s = 0
    for d in list(divs) + [n]:
        if d > s:
            out.append((s, d - 1))
        s = d + 1
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    divr = [y for y in range(H) if _is_divider(g[y, :])]
    divc = [x for x in range(W) if _is_divider(g[:, x])]
    rs = _spans(divr, H)
    cs = _spans(divc, W)
    panels = [(r, c) for r in rs for c in cs]
    cnt = Counter()
    for (r0, r1), (c0, c1) in panels:
        p = g[r0:r1 + 1, c0:c1 + 1]
        if p.size == 0:
            continue
        if not np.any(p == NOISE) and len(np.unique(p)) > 1:
            cnt[tuple(map(tuple, p.tolist()))] += 1
    out = np.full_like(g, DIV)
    if not cnt:
        res = g.copy()
        res[res == NOISE] = DIV
        return res.tolist()
    best = max(cnt.values())
    motif_key = sorted(k for k, v in cnt.items() if v == best)[0]
    motif = np.array(motif_key, dtype=int)
    vals, counts = np.unique(motif, return_counts=True)
    major = int(vals[int(np.argmax(counts))])
    for (r0, r1), (c0, c1) in panels:
        p = g[r0:r1 + 1, c0:c1 + 1]
        if p.shape != motif.shape:
            out[r0:r1 + 1, c0:c1 + 1] = major
            continue
        known = p != NOISE
        is_pattern = bool(np.all(p[known] == motif[known]))
        if is_pattern:
            out[r0:r1 + 1, c0:c1 + 1] = major
        else:
            out[r0:r1 + 1, c0:c1 + 1] = motif
    return out.tolist()
'''
    return template.replace('__DIV__', str(div_colour)).replace('__NOISE__', str(noise_colour))
