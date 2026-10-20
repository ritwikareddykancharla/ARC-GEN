def build_program(d4, palette):
    H = 10
    W = 10
    r, c = 2, 2
    if d4 >= 4:
        c = W - 1 - c
    h, w = H, W
    for _ in range(d4 % 4):
        r, c = c, h - 1 - r
        h, w = w, h
    top = r < h // 2
    left = c < w // 2
    bg = int(palette[0])
    src = '''import numpy as np

BG = __BG__
BLOCK_TOP = __TOP__
BLOCK_LEFT = __LEFT__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    hr = H // 2
    hc = W // 2

    def src_row(r):
        in_top = r < hr
        return r if in_top == BLOCK_TOP else H - 1 - r

    def src_col(c):
        in_left = c < hc
        return c if in_left == BLOCK_LEFT else W - 1 - c

    out = g.copy()
    for rt in (True, False):
        for ct in (True, False):
            if rt == BLOCK_TOP and ct == BLOCK_LEFT:
                continue
            rows = list(range(1, hr)) if rt else list(range(hr, H - 1))
            cols = list(range(1, hc)) if ct else list(range(hc, W - 1))
            mapping = {}
            for rr in rows:
                for cc in cols:
                    v = int(g[rr, cc])
                    if v != BG:
                        mapping[int(g[src_row(rr), src_col(cc)])] = v
            for rr in rows:
                for cc in cols:
                    t = int(g[src_row(rr), src_col(cc)])
                    out[rr, cc] = mapping.get(t, BG)
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg))
    src = src.replace('__TOP__', 'True' if top else 'False')
    src = src.replace('__LEFT__', 'True' if left else 'False')
    return src
