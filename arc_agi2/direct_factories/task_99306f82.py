def build_program(d4, palette):
    d4 = int(d4)
    bg = int(palette[0])
    frame_c = int(palette[1])
    # Track which visible corner the original top-left corner (start of the seed diagonal) maps to.
    top, left = True, True
    if d4 >= 4:
        left = not left  # reverse each row
    for _ in range(d4 % 4):
        # clockwise rotation: (r, c) -> (c, h-1-r)
        top, left = left, (not top)
    src = '''import numpy as np

BG = %d
FRAME = %d
CORNER_TOP = %r
CORNER_LEFT = %r


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    ys, xs = np.nonzero(g == FRAME)
    if len(ys) == 0:
        return out.tolist()
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    iy0, iy1, ix0, ix1 = y0 + 1, y1 - 1, x0 + 1, x1 - 1
    # Seed diagonal starts at the visible image of the original top-left grid corner.
    r0 = 0 if CORNER_TOP else H - 1
    c0 = 0 if CORNER_LEFT else W - 1
    seeds = []
    for y in range(H):
        for x in range(W):
            v = int(g[y, x])
            if v == BG or v == FRAME:
                continue
            if iy0 <= y <= iy1 and ix0 <= x <= ix1:
                continue
            dist = max(abs(y - r0), abs(x - c0))
            seeds.append((dist, y, x, v))
    seeds.sort()
    cols = [s[3] for s in seeds]
    if not cols or iy0 > iy1 or ix0 > ix1:
        return out.tolist()
    n = len(cols)
    # Paint rings from the frame inward; depth = distance to nearest interior edge.
    for y in range(iy0, iy1 + 1):
        for x in range(ix0, ix1 + 1):
            d = min(y - iy0, iy1 - y, x - ix0, ix1 - x)
            out[y, x] = cols[min(d, n - 1)]
    return out.tolist()
''' % (bg, frame_c, top, left)
    return src
