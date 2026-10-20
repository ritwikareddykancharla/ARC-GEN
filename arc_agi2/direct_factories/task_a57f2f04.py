def build_program(d4, palette):
    bg = int(palette[8])
    zero = int(palette[0])
    src = '''import numpy as np

BG = __BG__
ZERO = __ZERO__

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                stack = [(y, x)]
                seen[y, x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                out.append(cells)
    return out

def _period(total, need):
    need = max(1, need)
    for p in range(need, total + 1):
        if total % p == 0 and total // p >= 2:
            return p
    for p in range(need, total + 1):
        if total % p == 0:
            return p
    return total

def _axis(lo, hi, mlo, mhi):
    # returns (anchor_at_low_side, needed_extent)
    touch_lo = (mlo == lo)
    touch_hi = (mhi == hi)
    if touch_lo and not touch_hi:
        low = True
    elif touch_hi and not touch_lo:
        low = False
    else:
        low = (mlo - lo) <= (hi - mhi)
    if low:
        return True, mhi - lo + 1
    return False, hi - mlo + 1

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    for cells in _components(g != BG):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        motif = [(y, x) for (y, x) in cells if g[y, x] != ZERO]
        if not motif:
            continue
        my0 = min(c[0] for c in motif); my1 = max(c[0] for c in motif)
        mx0 = min(c[1] for c in motif); mx1 = max(c[1] for c in motif)
        H = y1 - y0 + 1
        W = x1 - x0 + 1
        top, needh = _axis(y0, y1, my0, my1)
        left, needw = _axis(x0, x1, mx0, mx1)
        h = _period(H, needh)
        w = _period(W, needw)
        ty0 = y0 if top else y1 - h + 1
        tx0 = x0 if left else x1 - w + 1
        tile = g[ty0:ty0 + h, tx0:tx0 + w].copy()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                out[y, x] = tile[(y - ty0) % h, (x - tx0) % w]
    return out.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__ZERO__', str(zero))
