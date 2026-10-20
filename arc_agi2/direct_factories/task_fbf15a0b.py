def build_program(d4, palette):
    M = int(palette[5])
    B = int(palette[8])
    src = '''import numpy as np

MARK = %d
BG = %d

def _corner_pairs(g):
    H, W = g.shape
    cands = []
    for r0, dr in ((0, 1), (H - 1, -1)):
        for c0, dc in ((0, 1), (W - 1, -1)):
            if g[r0, c0] != MARK:
                continue
            r2 = r0 + 2 * dr
            if 0 <= r2 < H and g[r2, c0] == MARK:
                cands.append(((r0, c0), (r2, c0)))
            c2 = c0 + 2 * dc
            if 0 <= c2 < W and g[r0, c2] == MARK:
                cands.append(((r0, c0), (r0, c2)))
    uniq = []
    for p in cands:
        if p not in uniq:
            uniq.append(p)
    return uniq

def _find_markers(g):
    pts = [(int(r), int(c)) for r, c in zip(*np.where(g == MARK))]
    if len(pts) == 2 and (pts[0][0] == pts[1][0] or pts[0][1] == pts[1][1]):
        return pts
    cands = _corner_pairs(g)
    if cands:
        # prefer a pair whose middle cell is background (a true two-apart gap)
        for a, b in cands:
            mr, mc = (a[0] + b[0]) // 2, (a[1] + b[1]) // 2
            if g[mr, mc] == BG:
                return [a, b]
        return list(cands[0])
    if len(pts) >= 2:
        return pts[:2]
    return pts

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    pts = _find_markers(g)
    clean = g.copy()
    for r, c in pts:
        clean[r, c] = BG
    if len(pts) < 2:
        return clean.tolist()
    rows = [p[0] for p in pts]
    cols = [p[1] for p in pts]
    if len(set(cols)) == 1:
        h = H // 2
        if min(rows) >= h:
            out = clean[h:, :]
        else:
            out = clean[:h, :]
    else:
        w = W // 2
        if min(cols) >= w:
            out = clean[:, w:]
        else:
            out = clean[:, :w]
    return out.copy().tolist()
''' % (M, B)
    return src
