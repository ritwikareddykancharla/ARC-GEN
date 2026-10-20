def build_program(d4, palette):
    d4 = int(d4)
    # canonical direction vectors (dr, dc): 'down' toward the anchored bottom line, 'right' as the shift axis
    down = (1, 0)
    right = (0, 1)
    def refl(v):
        return (v[0], -v[1])
    def rot(v):
        # clockwise rotation: (r, c) -> (c, H-1-r), so vector (dr, dc) -> (dc, -dr)
        return (v[1], -v[0])
    if d4 >= 4:
        down = refl(down)
        right = refl(right)
    for _ in range(d4 % 4):
        down = rot(down)
        right = rot(right)
    bg = int(palette[0])
    src = '''import numpy as np

BG = %d
DOWN = (%d, %d)
RIGHT = (%d, %d)

def _shift(arr, s, bg):
    n = arr.shape[0]
    new = np.full(n, bg, dtype=arr.dtype)
    if s > 0:
        if s < n:
            new[s:] = arr[:n - s]
    elif s < 0:
        t = -s
        if t < n:
            new[:n - t] = arr[t:]
    else:
        new[:] = arr
    return new

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    mask = g != BG
    if not mask.any():
        return out.tolist()
    if DOWN[0] != 0:
        # scan lines are rows; anchored line is the extreme occupied row in DOWN direction
        occ = np.where(mask.any(axis=1))[0]
        base = int(occ.max()) if DOWN[0] > 0 else int(occ.min())
        unit = RIGHT[1]
        for y in range(H):
            k = (base - y) * DOWN[0]
            if k < 0:
                continue
            m = k %% 4
            if m == 1:
                s = -unit
            elif m == 3:
                s = unit
            else:
                continue
            out[y, :] = _shift(g[y, :], s, BG)
    else:
        # scan lines are columns
        occ = np.where(mask.any(axis=0))[0]
        base = int(occ.max()) if DOWN[1] > 0 else int(occ.min())
        unit = RIGHT[0]
        for x in range(W):
            k = (base - x) * DOWN[1]
            if k < 0:
                continue
            m = k %% 4
            if m == 1:
                s = -unit
            elif m == 3:
                s = unit
            else:
                continue
            out[:, x] = _shift(g[:, x], s, BG)
    return out.tolist()
''' % (bg, down[0], down[1], right[0], right[1])
    return src
