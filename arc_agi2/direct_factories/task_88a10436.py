import numpy as np

def _axis_reversed(d4):
    # Label every original cell, then apply the episode transform to the labels.
    lab = np.arange(6).reshape(2, 3)
    a = lab
    if d4 >= 4:
        a = a[:, ::-1]
    a = np.rot90(a, -(d4 % 4))
    def rc(v):
        v = int(v)
        return (v // 3, v % 3)
    o00 = rc(a[0, 0])
    o10 = rc(a[1, 0])
    o01 = rc(a[0, 1])
    dr = (o10[0] - o00[0]) + (o10[1] - o00[1])
    dc = (o01[0] - o00[0]) + (o01[1] - o00[1])
    return dr < 0, dc < 0

def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[5])
    rev_r, rev_c = _axis_reversed(int(d4))
    src = '''import numpy as np

BG = %d
MARK = %d
REV_R = %s
REV_C = %s

def _centre(n, rev):
    # Anchor offset inside the pattern box along one visible axis.
    # For odd extents this is the exact middle.
    return (n - 1) // 2 if rev else n // 2

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    marks = np.argwhere(g == MARK)
    if len(marks) == 0:
        return out.tolist()
    my, mx = int(marks[0][0]), int(marks[0][1])
    out[my, mx] = BG
    mask = (g != BG) & (g != MARK)
    if not mask.any():
        return out.tolist()
    ys, xs = np.where(mask)
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    pat = g[y0:y1 + 1, x0:x1 + 1]
    h, w = pat.shape
    oy = my - _centre(h, REV_R)
    ox = mx - _centre(w, REV_C)
    for dy in range(h):
        for dx in range(w):
            v = int(pat[dy, dx])
            if v == BG or v == MARK:
                continue
            yy, xx = oy + dy, ox + dx
            if 0 <= yy < H and 0 <= xx < W:
                out[yy, xx] = v
    return out.tolist()
''' % (bg, mark, 'True' if rev_r else 'False', 'True' if rev_c else 'False')
    return src
