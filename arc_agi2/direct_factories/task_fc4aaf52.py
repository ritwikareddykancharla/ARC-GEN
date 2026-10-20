def build_program(d4, palette):
    # Canonical frame: the moving half is the TOP half (direction up = (-1,0)),
    # and it slides RIGHT (direction (0,+1)) by the width of its row at the cut.
    up = (-1, 0)
    sh = (0, 1)
    if d4 >= 4:
        # reverse each row: column direction flips
        up = (up[0], -up[1])
        sh = (sh[0], -sh[1])
    for _ in range(d4 % 4):
        # clockwise rotation maps a direction (dr, dc) to (dc, -dr)
        up = (up[1], -up[0])
        sh = (sh[1], -sh[0])
    bg = int(palette[8])
    src = '''import numpy as np

BG = __BG__
UR, UC = __UR__, __UC__
SR, SC = __SR__, __SC__

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    mask = g != BG
    out = g.copy()
    if not mask.any():
        return out.tolist()
    # 1. swap the two figure colours
    cols = sorted(set(int(v) for v in g[mask].ravel().tolist()))
    if len(cols) == 2:
        a, b = cols
        out[g == a] = b
        out[g == b] = a
    ys, xs = np.nonzero(mask)
    vertical_axis = (UR != 0)  # True: halves are stacked along rows
    if vertical_axis:
        lo, hi = int(ys.min()), int(ys.max())
    else:
        lo, hi = int(xs.min()), int(xs.max())
    n = hi - lo + 1
    half = n // 2
    if half < 1:
        return out.tolist()
    toward_low = (UR == -1) or (UC == -1)
    if toward_low:
        moving = list(range(lo, lo + half))
        cut = lo + half - 1
    else:
        moving = list(range(hi - half + 1, hi + 1))
        cut = hi - half + 1
    # 2. shift amount = extent of the moving half's line adjacent to the cut
    line = mask[cut, :] if vertical_axis else mask[:, cut]
    idx = np.nonzero(line)[0]
    if len(idx) == 0:
        return out.tolist()
    w = int(idx.max() - idx.min() + 1)
    movmask = np.zeros_like(mask)
    if vertical_axis:
        movmask[moving, :] = mask[moving, :]
    else:
        movmask[:, moving] = mask[:, moving]
    vals = out.copy()
    out[movmask] = BG
    rr, cc = np.nonzero(movmask)
    dr, dc = SR * w, SC * w
    for r, c in zip(rr.tolist(), cc.tolist()):
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W:
            out[nr, nc] = vals[r, c]
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg))
    src = src.replace('__UR__', str(up[0])).replace('__UC__', str(up[1]))
    src = src.replace('__SR__', str(sh[0])).replace('__SC__', str(sh[1]))
    return src
