TEMPLATE = """import numpy as np

# Tracks run along visible rows (True) or visible columns (False).
ROWS = __ROWS__
# +1: the 'lower' track of a ladder path has the larger visible line index; -1: the smaller.
LOWER = __LOWER__
BG = __BG__
TRACK = __TRACK__
MARK = __MARK__
RUNG = __RUNG__
CONN = __CONN__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    if ROWS:
        NT, L = H, W
    else:
        NT, L = W, H

    def ix(t, p):
        # t = index of the line that tracks run along, p = position along that line
        if ROWS:
            return (t, p)
        return (p, t)

    def val(t, p):
        return int(g[ix(t, p)])

    tracks = [t for t in range(NT) if sum(1 for p in range(L) if val(t, p) == TRACK) > L // 2]

    rungs = {}
    for t in range(NT):
        p = 0
        while p < L:
            if val(t, p) != RUNG:
                p += 1
                continue
            s = p
            while p < L and val(t, p) == RUNG:
                p += 1
            mid = (s + p - 1) // 2
            for q in range(s, p):
                out[ix(t, q)] = TRACK
            for tt in range(max(t - 1, 0), min(t + 2, NT)):
                out[ix(tt, mid)] = CONN
            if 0 < t < NT - 1:
                rungs.setdefault(t - 1, []).append((mid, t + 1))
                rungs.setdefault(t + 1, []).append((mid, t - 1))
    out[out == MARK] = TRACK

    def bounds(t, p):
        lo = p
        hi = p
        while lo > 0 and val(t, lo - 1) != BG:
            lo -= 1
        while hi + 1 < L and val(t, hi + 1) != BG:
            hi += 1
        return lo, hi

    endpoints = set()
    for t in tracks:
        for p in range(L):
            if val(t, p) == BG:
                continue
            lo, hi = bounds(t, p)
            if p == lo or p == hi:
                endpoints.add((t, p))

    paths = set()
    for st, sp in sorted(endpoints):
        lo, hi = bounds(st, sp)
        d = 1 if sp == lo else -1
        t, p = st, sp
        first = True
        seen = set()
        while True:
            state = (t, p, d, first)
            if state in seen:
                break
            seen.add(state)
            lo, hi = bounds(t, p)
            cands = [(x, o) for x, o in rungs.get(t, []) if lo <= x <= hi and ((x - p) * d > 0 or (first and x == p))]
            if not cands:
                p = hi if d > 0 else lo
                break
            best = min(cands, key=lambda it: abs(it[0] - p))
            p, t = best
            d = -d
            first = False
        paths.add(tuple(sorted(((st, sp), (t, p)))))

    for a, b in sorted(paths):
        count = int(val(a[0], a[1]) == MARK) + int(val(b[0], b[1]) == MARK)
        if not count:
            continue
        if a[0] == b[0]:
            for e in (a, b):
                if val(e[0], e[1]) == MARK:
                    out[ix(e[0], e[1])] = MARK
        else:
            low = b if (b[0] - a[0]) * LOWER > 0 else a
            t, p = low
            lo, hi = bounds(t, p)
            d = 1 if p == lo else -1
            for k in range(count):
                x = p + d * k
                if 0 <= x < L:
                    out[ix(t, x)] = MARK
    return out.tolist()
"""


def build_program(d4, palette):
    k = int(d4) % 4
    rows = (k % 2 == 0)
    if k == 0 or k == 3:
        lower = 1
    else:
        lower = -1
    code = TEMPLATE
    subs = [
        ('__ROWS__', 'True' if rows else 'False'),
        ('__LOWER__', str(lower)),
        ('__BG__', str(int(palette[0]))),
        ('__TRACK__', str(int(palette[8]))),
        ('__MARK__', str(int(palette[3]))),
        ('__RUNG__', str(int(palette[7]))),
        ('__CONN__', str(int(palette[6]))),
    ]
    for key, v in subs:
        code = code.replace(key, v)
    return code
