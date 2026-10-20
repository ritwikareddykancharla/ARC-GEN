def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np

BG = __BG__

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    others = [int(c) for c in np.unique(g) if int(c) != BG]
    if len(others) < 2:
        return out.tolist()
    bgm = (g == BG)
    nb = np.zeros_like(bgm)
    nb[1:, :] |= bgm[:-1, :]
    nb[:-1, :] |= bgm[1:, :]
    nb[:, 1:] |= bgm[:, :-1]
    nb[:, :-1] |= bgm[:, 1:]
    touch = {c: int(np.sum((g == c) & nb)) for c in others}
    cnt = {c: int(np.sum(g == c)) for c in others}
    # Frame colour A touches the background; inner colour B is enclosed.
    A = max(others, key=lambda c: (touch[c], cnt[c], -c))
    rest = [c for c in others if c != A]
    B = max(rest, key=lambda c: (-touch[c], cnt[c], -c))
    ys, xs = np.nonzero(~bgm)
    if ys.size == 0:
        return out.tolist()
    R0, R1 = int(ys.min()), int(ys.max())
    C0, C1 = int(xs.min()), int(xs.max())
    Bm = (g == B)
    rb = np.nonzero(Bm.any(axis=1))[0]
    cb = np.nonzero(Bm.any(axis=0))[0]
    if rb.size == 0 or cb.size == 0:
        return out.tolist()
    # Frame thickness: bumps can only shrink a side's apparent offset,
    # and at least one side is bump-free, so the max offset is the thickness.
    t = max(int(rb[0]) - R0, R1 - int(rb[-1]), int(cb[0]) - C0, C1 - int(cb[-1]))
    r0, r1, c0, c1 = R0 + t, R1 - t, C0 + t, C1 - t
    if r0 > r1 or c0 > c1:
        return out.tolist()
    # Bumps: B cells outside the clean inner rectangle.
    line_rows = [r for r in range(r0, r1 + 1)
                 if Bm[r, :c0].any() or Bm[r, c1 + 1:].any()]
    line_cols = [c for c in range(c0, c1 + 1)
                 if Bm[:r0, c].any() or Bm[r1 + 1:, c].any()]
    for r in line_rows:
        s = g[r, :]
        out[r, s == B] = A
        out[r, s == BG] = B
    for c in line_cols:
        s = g[:, c]
        out[s == B, c] = A
        out[s == BG, c] = B
    return out.tolist()
'''
    return src.replace('__BG__', str(bg))
