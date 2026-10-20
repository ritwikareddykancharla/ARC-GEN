def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np

BG = __BG__


def _bar_candidate(g):
    H, W = g.shape
    best = None
    vals = [int(v) for v in np.unique(g) if int(v) != BG]
    for v in vals:
        m = (g == v)
        cnt = int(m.sum())
        for horiz in (True, False):
            n_lines = W if horiz else H
            runs = []
            ok = True
            for k in range(n_lines):
                line = m[:, k] if horiz else m[k, :]
                idx = np.flatnonzero(line)
                if idx.size == 0:
                    runs.append(None)
                    continue
                lo, hi = int(idx[0]), int(idx[-1])
                if hi - lo + 1 != idx.size:
                    ok = False
                    break
                runs.append((lo, hi))
            if not ok:
                continue
            present = [k for k in range(n_lines) if runs[k] is not None]
            if len(present) < max(1, n_lines - 1):
                continue
            if present[-1] - present[0] + 1 != len(present):
                continue
            blo = min(runs[k][0] for k in present)
            bhi = max(runs[k][1] for k in present)
            if bhi - blo > 2:
                continue
            conn = True
            for a, b in zip(present, present[1:]):
                l1, h1 = runs[a]
                l2, h2 = runs[b]
                if max(l1, l2) > min(h1, h2) + 1:
                    conn = False
                    break
            if not conn:
                continue
            key = (len(present), cnt)
            if best is None or key > best[0]:
                best = (key, v, horiz)
    return best


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    mask = g != BG
    if not mask.any():
        return out.tolist()
    cand = _bar_candidate(g)
    if cand is not None:
        bar = cand[1]
        horiz = cand[2]
    else:
        vals, counts = np.unique(g[mask], return_counts=True)
        bar = int(vals[int(np.argmax(counts))])
        ys, xs = np.where(g == bar)
        horiz = (xs.max() - xs.min()) >= (ys.max() - ys.min())
    if horiz:
        lines = [[(r, c) for r in range(H)] for c in range(W)]
    else:
        lines = [[(r, c) for c in range(W)] for r in range(H)]
    for cells in lines:
        n = len(cells)
        idx = [k for k in range(n) if g[cells[k]] == bar]
        if not idx:
            continue
        lo, hi = min(idx), max(idx)
        before = [k for k in range(lo) if g[cells[k]] != BG]
        after = [k for k in range(hi + 1, n) if g[cells[k]] != BG]
        if len(before) == 1 and len(after) == 1 and lo - 1 >= 0 and hi + 1 < n:
            b = before[0]
            a = after[0]
            cb = int(g[cells[b]])
            ca = int(g[cells[a]])
            out[cells[b]] = BG
            out[cells[a]] = BG
            out[cells[lo - 1]] = ca
            out[cells[hi + 1]] = cb
    return out.tolist()
'''
    return src.replace('__BG__', str(bg))
