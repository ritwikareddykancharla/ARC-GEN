def build_program(d4, palette):
    bg = int(palette[0])
    tile = int(palette[2])
    band = int(palette[3])
    mark = int(palette[8])
    src = '''import numpy as np

BG = __BG__
TILE = __TILE__
BAND = __BAND__
MARK = __MARK__


def _tile_size(n):
    k = 1
    while k * k + k - 1 < n:
        k += 1
    return k


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    k = _tile_size(max(h, w))
    step = k + 1

    def region(r, c):
        return g[r * step:r * step + k, c * step:c * step + k]

    # read the motif from a slot untouched by the occluding band
    motif = None
    for r in range(k):
        for c in range(k):
            t = region(r, c)
            if t.shape != (k, k):
                continue
            if (t == BAND).any():
                continue
            if not (t == TILE).any():
                continue
            motif = (t == TILE)
            break
        if motif is not None:
            break

    if motif is None:
        # fallback: combine partial tile evidence and the visible slot layout
        motif = np.zeros((k, k), dtype=bool)
        for r in range(k):
            for c in range(k):
                t = region(r, c)
                if (t == TILE).any():
                    motif[r, c] = True
                    hh, ww = t.shape
                    motif[:hh, :ww] |= (t == TILE)

    out = g.copy()
    out[out == BAND] = BG

    # stamp the motif into every slot whose meta-cell is part of the motif
    for r in range(k):
        for c in range(k):
            if not motif[r, c]:
                continue
            for a in range(k):
                for b in range(k):
                    y = r * step + a
                    x = c * step + b
                    if 0 <= y < h and 0 <= x < w:
                        out[y, x] = TILE if motif[a, b] else BG

    # each tile gets a marker at its own slot position
    for r in range(k):
        for c in range(k):
            if motif[r, c]:
                y = r * step + r
                x = c * step + c
                if 0 <= y < h and 0 <= x < w:
                    out[y, x] = MARK
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg)).replace('__TILE__', str(tile))
    src = src.replace('__BAND__', str(band)).replace('__MARK__', str(mark))
    return src
