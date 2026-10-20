TEMPLATE = """import numpy as np
from collections import Counter

BG = __BG__
MK = __MK__
NR = __NR__
SIGN = (__S0__, __S1__)
P = 15


def _runs(v):
    out = []
    s = None
    for i, b in enumerate(v):
        if b and s is None:
            s = i
        if not b and s is not None:
            out.append((s, i - 1))
            s = None
    if s is not None:
        out.append((s, len(v) - 1))
    return out


def _best_period(s):
    n = len(s)
    best = None
    for p in range(1, n):
        f = {}
        inv = {}
        r = 0
        for i in range(n - 1, p - 1, -1):
            a, b = s[i - p], s[i]
            if (a == BG) != (b == BG):
                break
            if f.get(a, b) != b or inv.get(b, a) != a:
                break
            f[a] = b
            inv[b] = a
            r += 1
        if r < p:
            continue
        sc = r - p
        if best is None or sc > best[0]:
            best = (sc, p, f)
    return best


def _extend_end(s, k):
    s = list(s)
    if k <= 0:
        return s[:len(s) + k] if k < 0 else s
    bp = _best_period(s)
    p, f = (1, {}) if bp is None else (bp[1], bp[2])
    for _ in range(k):
        a = s[-p]
        s.append(f.get(a, a))
    return s


def _pred(hist):
    if len(hist) == 1:
        return hist[-1]
    if len(hist) == 2:
        d = [hist[-1][i] - hist[-2][i] for i in range(len(hist[-1]))]
    else:
        d = [hist[-2][i] - hist[-3][i] for i in range(len(hist[-1]))]
    return tuple(hist[-1][i] + d[i] for i in range(len(d)))


def _extent(line):
    nz = np.nonzero(line != BG)[0]
    return None if len(nz) == 0 else (int(nz.min()), int(nz.max()))


def _expand(line, s, c):
    if s == 0:
        return line.copy()
    out = np.full_like(line, BG)
    for i in np.nonzero(line != BG)[0]:
        j = i - s if i < c else (i + s if i > c else i)
        if 0 <= j < len(out):
            out[j] = line[i]
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    work = g.copy()
    work[g == MK] = BG
    occ = work != BG
    R = (len(_runs(occ.any(1))), len(_runs(occ.any(0))))
    NC = 1 - NR
    ga = NC if R[NC] > R[NR] else NR
    la = 1 - ga
    LL = (H, W)[la]
    pts = np.argwhere(g == MK)
    wmin = [int(v) for v in pts.min(0)]
    wmax = [int(v) for v in pts.max(0)]
    proj = occ.any(1) if ga == 0 else occ.any(0)
    grp = _runs(proj)
    if SIGN[ga] > 0:
        F = wmin[ga] < grp[0][0]
    else:
        F = wmax[ga] > grp[-1][1]
    D = -SIGN[ga] if F else SIGN[ga]
    XS = SIGN[la]
    WW = LL + 2 * P

    def line_of(pos):
        arr = np.full(WW, BG)
        arr[P:P + LL] = work[pos, :] if ga == 0 else work[:, pos]
        return arr

    if D > 0:
        groups = [{'start': s, 'lines': [line_of(q) for q in range(s, e + 1)]} for s, e in grp]
    else:
        groups = [{'start': e, 'lines': [line_of(q) for q in range(e, s - 1, -1)]} for s, e in reversed(grp)]

    cnt = Counter()
    for a, b in zip(groups, groups[1:]):
        for xa, xb in zip(a['lines'], b['lines']):
            m = (xa != BG) & (xb != BG)
            idx = list(np.nonzero(m)[0])
            if XS < 0:
                idx = idx[::-1]
            for i in idx:
                cnt[int(xa[i]), int(xb[i])] += 1
    step = {}
    for (u, v), c in cnt.most_common():
        if u not in step:
            step[u] = v

    def ap(line, use):
        if not use:
            return line.copy()
        return np.array([step.get(int(v), int(v)) if v != BG else BG for v in line])

    def center(lines):
        nz = [i for ln in lines for i in np.nonzero(ln != BG)[0]]
        if nz:
            return (min(nz) + max(nz)) / 2
        return WW / 2 if XS > 0 else (WW - 1) - WW / 2

    rule = (1, 0, False)
    if len(groups) >= 2 and len(groups[-1]['lines']) > len(groups[-2]['lines']):
        Lg = groups[-1]['lines']
        c = center(Lg)
        n0 = len(groups[-2]['lines'])
        done = False
        for q in range(1, n0 + 1):
            for s in range(0, 4):
                for use in (False, True):
                    if all(l - q >= 0 and np.array_equal(Lg[l], _expand(ap(Lg[l - q], use), s, c)) for l in range(n0, len(Lg))):
                        rule = (q, s, use)
                        done = True
                        break
                if done:
                    break
            if done:
                break

    far = wmax[ga] if D > 0 else wmin[ga]
    new_groups = []
    while True:
        lens = [len(gr['lines']) for gr in groups]
        nl = max(1, _pred([(x,) for x in lens])[0])
        if len(groups) >= 2:
            gap = D * (groups[-1]['start'] - groups[-2]['start']) - lens[-2]
        else:
            gap = 1
        start = groups[-1]['start'] + D * (lens[-1] + gap)
        prev = groups[-1]['lines']
        new = []
        for l in range(nl):
            if l < len(prev):
                src = ap(prev[l], True)
                hist = [_extent(gr['lines'][l]) for gr in groups if l < len(gr['lines']) and _extent(gr['lines'][l]) is not None]
                ex = _extent(src)
                if not hist or ex is None:
                    new.append(np.full(WW, BG))
                    continue
                lo, hi = ex
                nlo, nhi = _pred(hist)
                seg = [int(v) for v in src[lo:hi + 1]]
                out = np.full(WW, BG)
                if XS > 0:
                    seg = _extend_end(seg, nhi - hi)
                    seg = _extend_end(seg[::-1], lo - nlo)[::-1]
                    for k, v in enumerate(seg):
                        j = nlo + k
                        if 0 <= j < WW:
                            out[j] = v
                else:
                    seg = _extend_end(seg[::-1], lo - nlo)[::-1]
                    seg = _extend_end(seg, nhi - hi)
                    m = len(seg)
                    for i in range(m):
                        j = nhi - i
                        if 0 <= j < WW:
                            out[j] = seg[m - 1 - i]
                new.append(out)
            else:
                q, s, use = rule
                c = center(new[:len(prev)])
                new.append(_expand(ap(new[l - q], use), s, c))
        gr = {'start': start, 'lines': new}
        groups.append(gr)
        new_groups.append(gr)
        if D * start + nl - 1 >= D * far or len(new_groups) > 10:
            break

    placed = {}
    for ng in new_groups:
        for k, ln in enumerate(ng['lines']):
            placed[int(ng['start'] + D * k)] = ln
    res = []
    for r in range(wmin[0], wmax[0] + 1):
        row = []
        for c in range(wmin[1], wmax[1] + 1):
            if ga == 0:
                gpos, x = r, c
            else:
                gpos, x = c, r
            if gpos in placed:
                row.append(int(placed[gpos][x + P]))
            else:
                row.append(int(work[r, c]))
        res.append(row)
    return res
"""


def _vec(d4, v):
    dr, dc = v
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    return dr, dc


def build_program(d4, palette):
    d4 = int(d4) % 8
    vr = _vec(d4, (0, 1))
    vd = _vec(d4, (1, 0))
    sign = [1, 1]
    for v in (vr, vd):
        for a in (0, 1):
            if v[a] != 0:
                sign[a] = v[a]
    nr = 0 if vd[0] != 0 else 1
    bg = int(palette[0])
    mk = int(palette[5])
    prog = TEMPLATE.replace('__BG__', str(bg)).replace('__MK__', str(mk))
    prog = prog.replace('__NR__', str(nr)).replace('__S0__', str(sign[0])).replace('__S1__', str(sign[1]))
    return prog
