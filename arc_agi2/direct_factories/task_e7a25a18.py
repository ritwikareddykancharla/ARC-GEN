def build_program(d4, palette):
    bg = int(palette[0])
    fc = int(palette[2])
    src = '''import numpy as np

BG = %d
FC = %d


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    ys, xs = np.where(g == FC)
    if ys.size == 0:
        return g.tolist()
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    out = g[y0:y1 + 1, x0:x1 + 1].copy()
    H, W = out.shape
    if H < 3 or W < 3:
        return out.tolist()
    inner = out[1:-1, 1:-1].copy()
    mask = (inner != BG) & (inner != FC)
    my, mx = np.where(mask)
    out[1:-1, 1:-1] = BG
    if my.size == 0:
        return out.tolist()
    block = inner[my.min():my.max() + 1, mx.min():mx.max() + 1]
    bh, bw = block.shape
    # the block is a 2x2 logical pattern; each quadrant is a uniform square
    hr = bh // 2 if bh >= 2 else 0
    hc = bw // 2 if bw >= 2 else 0
    pat = np.array([[block[0, 0], block[0, hc]],
                    [block[hr, 0], block[hr, hc]]], dtype=int)
    ih, iw = H - 2, W - 2
    rsplit = [0, ih // 2, ih]
    csplit = [0, iw // 2, iw]
    for i in range(2):
        for j in range(2):
            out[1 + rsplit[i]:1 + rsplit[i + 1], 1 + csplit[j]:1 + csplit[j + 1]] = pat[i, j]
    return out.tolist()
''' % (bg, fc)
    return src
