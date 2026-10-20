TEMPLATE = '''import numpy as np

BG = __BG__
FRAME = __FR__


def _pick(i, n, sn, sparse):
    if i == 0:
        return 0
    if i == n - 1:
        return sn - 1
    return sparse


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    fy, fx = np.nonzero(g == FRAME)
    seed_mask = (g != BG) & (g != FRAME)
    sy, sx = np.nonzero(seed_mask)
    if len(sy) == 0 or len(fy) == 0:
        return out.tolist()
    vals, counts = np.unique(g[seed_mask], return_counts=True)
    col = int(vals[int(np.argmax(counts))])
    out[seed_mask] = BG
    y0, y1 = int(sy.min()), int(sy.max())
    x0, x1 = int(sx.min()), int(sx.max())
    s = (g[y0:y1 + 1, x0:x1 + 1] == col).astype(int)
    sh, sw = s.shape
    sparse_r = int(np.argmin(s.sum(axis=1)))
    sparse_c = int(np.argmin(s.sum(axis=0)))
    iy0, iy1 = int(fy.min()) + 1, int(fy.max()) - 1
    ix0, ix1 = int(fx.min()) + 1, int(fx.max()) - 1
    H, W = iy1 - iy0 + 1, ix1 - ix0 + 1
    if H <= 0 or W <= 0:
        return out.tolist()
    for r in range(H):
        sr = _pick(r, H, sh, sparse_r)
        for c in range(W):
            sc = _pick(c, W, sw, sparse_c)
            if s[sr, sc]:
                out[iy0 + r, ix0 + c] = col
    return out.tolist()
'''


def build_program(d4, palette):
    bg = int(palette[7])
    fr = int(palette[6])
    return TEMPLATE.replace('__BG__', str(bg)).replace('__FR__', str(fr))
