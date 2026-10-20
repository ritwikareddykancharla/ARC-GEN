def build_program(d4, palette):
    bg = int(palette[8])
    fg = int(palette[1])
    mk = int(palette[4])
    src = '''import numpy as np

BG = %d
FG = %d
MARK = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    for y in range(H):
        for x in range(W):
            if g[y, x] != BG:
                continue
            ok = True
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                for k in (2, 3):
                    yy = y + dy * k
                    xx = x + dx * k
                    if not (0 <= yy < H and 0 <= xx < W) or g[yy, xx] != FG:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                out[y, x] = MARK
    return out.tolist()
''' % (bg, fg, mk)
    return src
