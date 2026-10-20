TEMPLATE = """import numpy as np

BG = __BG__


def _runs(n, dset):
    res = []
    start = None
    for i in range(n + 1):
        if i < n and i not in dset:
            if start is None:
                start = i
        elif start is not None:
            res.append((start, i - 1))
            start = None
    return res


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    # Divider lines: full uniform rows/columns whose colour is not the empty-cell colour.
    div_rows = set(y for y in range(H) if np.all(g[y, :] == g[y, 0]) and int(g[y, 0]) != BG)
    div_cols = set(x for x in range(W) if np.all(g[:, x] == g[0, x]) and int(g[0, x]) != BG)
    rr = _runs(H, div_rows)
    cr = _runs(W, div_cols)
    R, C = len(rr), len(cr)
    if R == 0 or C == 0:
        return out.tolist()
    col = np.full((R, C), BG, dtype=int)
    for r, (y0, y1) in enumerate(rr):
        for c, (x0, x1) in enumerate(cr):
            vals = g[y0:y1 + 1, x0:x1 + 1].ravel()
            cnt = np.bincount(vals, minlength=10)
            best = int(cnt.argmax())
            # prefer a non-empty colour on ties
            if best == BG:
                cnt2 = cnt.copy()
                cnt2[BG] = -1
                b2 = int(cnt2.argmax())
                if cnt2[b2] == cnt[BG]:
                    best = b2
            col[r, c] = best
    tokens = [(r, c, int(col[r, c])) for r in range(R) for c in range(C) if col[r, c] != BG]
    new = col.copy()
    for j in range(len(tokens)):
        rj, cj, vj = tokens[j]
        for i in range(j):
            ri, ci, vi = tokens[i]
            if vi != vj:
                continue
            if ri == rj:
                for c in range(min(ci, cj), max(ci, cj) + 1):
                    if col[ri, c] == BG:
                        new[ri, c] = vi
            if ci == cj:
                for r in range(min(ri, rj), max(ri, rj) + 1):
                    if col[r, ci] == BG:
                        new[r, ci] = vi
    for r in range(R):
        for c in range(C):
            if new[r, c] != col[r, c]:
                y0, y1 = rr[r]
                x0, x1 = cr[c]
                out[y0:y1 + 1, x0:x1 + 1] = new[r, c]
    return out.tolist()
"""


def build_program(d4, palette):
    bg = int(palette[0])
    return TEMPLATE.replace('__BG__', str(bg))
