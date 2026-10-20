TEMPLATE = '''import numpy as np
from collections import Counter

BG = __BG__
REV_ROWS = __RR__
REV_COLS = __RC__


def _axis_candidates(n_cells, rev):
    out = []
    seen = set()
    for o in (1, 2):
        for t in (4, 5, 6):
            for s in (1, 2):
                n = (n_cells - 2) // (t + s)
                if n < 1:
                    continue
                bands = []
                ok = True
                for i in range(n):
                    a = o + i * (t + s)
                    b = a + t - 1
                    if b >= n_cells:
                        ok = False
                        break
                    if rev:
                        a, b = n_cells - 1 - b, n_cells - 1 - a
                    bands.append((a, b))
                if not ok:
                    continue
                bands.sort()
                key = tuple(bands)
                if key in seen:
                    continue
                seen.add(key)
                out.append(key)
    return out


def _idx(bands):
    r = []
    for a, b in bands:
        r.extend(range(a, b + 1))
    return r


def _prototype(g, rb, cb):
    h = min(b - a + 1 for a, b in rb)
    w = min(b - a + 1 for a, b in cb)
    proto = np.full((h, w), BG, dtype=int)
    tie = False
    for y in range(h):
        for x in range(w):
            cnt = Counter()
            for r0, _r1 in rb:
                for c0, _c1 in cb:
                    cnt[int(g[r0 + y, c0 + x])] += 1
            ranked = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))
            if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
                tie = True
            proto[y, x] = ranked[0][0]
    return proto, tie


def _density_bands(prof):
    if len(prof) == 0 or prof.max() <= 0:
        return []
    th = prof.max() / 2.0
    runs = []
    start = None
    for i, v in enumerate(prof):
        if v > th and start is None:
            start = i
        if v <= th and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(prof) - 1))
    return runs


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    if g.ndim != 2 or g.size == 0:
        return [list(map(int, row)) for row in grid]
    H, W = g.shape
    nz = g != BG
    best = None
    best_score = None
    rcands = _axis_candidates(H, REV_ROWS)
    ccands = _axis_candidates(W, REV_COLS)
    for rb in rcands:
        ri = _idx(rb)
        colok = nz[ri, :].all(axis=0)
        for cb in ccands:
            ci = _idx(cb)
            if not colok[ci].all():
                continue
            proto, tie = _prototype(g, rb, cb)
            score = (0 if tie else 1, len(ri) * len(ci))
            if best_score is None or score > best_score:
                best_score = score
                best = (rb, cb, proto)
    if best is None:
        rb = _density_bands(nz.sum(axis=1))
        cb = _density_bands(nz.sum(axis=0))
        if not rb or not cb:
            return np.full((H, W), BG, dtype=int).tolist()
        proto, _tie = _prototype(g, rb, cb)
        best = (rb, cb, proto)
    rb, cb, proto = best
    out = np.full((H, W), BG, dtype=int)
    h, w = proto.shape
    for r0, _r1 in rb:
        for c0, _c1 in cb:
            out[r0:r0 + h, c0:c0 + w] = proto
    return out.tolist()
'''


def build_program(d4, palette):
    d4 = int(d4)
    rev_rows = False
    rev_cols = False
    if d4 >= 4:
        rev_cols = True
    for _ in range(d4 % 4):
        rev_rows, rev_cols = rev_cols, (not rev_rows)
    bg = int(palette[0])
    code = TEMPLATE.replace('__BG__', str(bg))
    code = code.replace('__RR__', 'True' if rev_rows else 'False')
    code = code.replace('__RC__', 'True' if rev_cols else 'False')
    return code
