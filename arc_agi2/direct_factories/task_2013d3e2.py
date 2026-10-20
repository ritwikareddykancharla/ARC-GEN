def build_program(d4, palette):
    k = d4 % 4
    if d4 < 4:
        corner = ['TL', 'TR', 'BR', 'BL'][k]
    else:
        corner = ['TR', 'BR', 'BL', 'TL'][k]
    bg = int(palette[0])
    top = corner in ('TL', 'TR')
    left = corner in ('TL', 'BL')
    src = '''import numpy as np

BG = %d
TAKE_TOP = %s
TAKE_LEFT = %s

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    ys, xs = np.where(g != BG)
    if len(ys) == 0:
        return g.tolist()
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    fig = g[y0:y1 + 1, x0:x1 + 1]
    H, W = fig.shape
    h = (H + 1) // 2
    w = (W + 1) // 2
    if TAKE_TOP:
        rs = slice(0, h)
    else:
        rs = slice(H - h, H)
    if TAKE_LEFT:
        cs = slice(0, w)
    else:
        cs = slice(W - w, W)
    return fig[rs, cs].copy().tolist()
''' % (bg, 'True' if top else 'False', 'True' if left else 'False')
    return src
