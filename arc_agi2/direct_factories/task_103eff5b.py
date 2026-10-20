def build_program(d4, palette):
    bg = int(palette[0])
    st = int(palette[8])
    reflected = 1 if int(d4) >= 4 else 0
    src = '''import numpy as np

BG = __BG__
ST = __ST__
REFLECTED = __REF__

# Orientation mappings from a structure block (i, j) to a legend cell.
# The legend has lh rows and lw columns.
# Without reflection the block grid is the legend rotated clockwise.
# With reflection it is the legend rotated counter-clockwise.
def _maps(lh, lw):
    cw = ((lw, lh), lambda i, j: (lh - 1 - j, i))
    ccw = ((lw, lh), lambda i, j: (j, lw - 1 - i))
    ident = ((lh, lw), lambda i, j: (i, j))
    r180 = ((lh, lw), lambda i, j: (lh - 1 - i, lw - 1 - j))
    fv = ((lh, lw), lambda i, j: (lh - 1 - i, j))
    fh = ((lh, lw), lambda i, j: (i, lw - 1 - j))
    tr = ((lw, lh), lambda i, j: (j, i))
    atr = ((lw, lh), lambda i, j: (lh - 1 - j, lw - 1 - i))
    if REFLECTED:
        return [ccw, cw, ident, r180, fv, fh, tr, atr]
    return [cw, ccw, ident, r180, fv, fh, tr, atr]

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    leg = (g != BG) & (g != ST)
    stm = (g == ST)
    if not leg.any() or not stm.any():
        return out.tolist()
    ys, xs = np.where(leg)
    ly0, ly1, lx0, lx1 = ys.min(), ys.max(), xs.min(), xs.max()
    L = g[ly0:ly1 + 1, lx0:lx1 + 1]
    Lm = leg[ly0:ly1 + 1, lx0:lx1 + 1]
    lh, lw = L.shape
    ys8, xs8 = np.where(stm)
    sy0, sy1, sx0, sx1 = ys8.min(), ys8.max(), xs8.min(), xs8.max()
    sh, sw = sy1 - sy0 + 1, sx1 - sx0 + 1
    chosen = None
    for (ch, cw), f in _maps(lh, lw):
        if sh % ch or sw % cw:
            continue
        s = sh // ch
        if s != sw // cw or s < 1:
            continue
        ok = True
        for i in range(ch):
            for j in range(cw):
                blk = stm[sy0 + i * s:sy0 + (i + 1) * s, sx0 + j * s:sx0 + (j + 1) * s]
                li, lj = f(i, j)
                if bool(blk.all()) != bool(Lm[li, lj]):
                    ok = False
                    break
            if not ok:
                break
        if ok:
            chosen = (ch, cw, s, f)
            break
    if chosen is None:
        (ch, cw), f = _maps(lh, lw)[0]
        s = max(1, sh // ch)
        chosen = (ch, cw, s, f)
    ch, cw, s, f = chosen
    for i in range(ch):
        for j in range(cw):
            li, lj = f(i, j)
            if li < 0 or lj < 0 or li >= lh or lj >= lw:
                continue
            if not Lm[li, lj]:
                continue
            r0, c0 = sy0 + i * s, sx0 + j * s
            region = out[r0:r0 + s, c0:c0 + s]
            m = stm[r0:r0 + s, c0:c0 + s]
            region[m] = int(L[li, lj])
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg)).replace('__ST__', str(st)).replace('__REF__', str(reflected))
    return src
