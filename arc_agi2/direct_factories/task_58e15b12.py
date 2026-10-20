def build_program(d4, palette):
    bg = int(palette[0])
    mix = int(palette[6])
    prefer_vertical = (int(d4) % 2 == 0)
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('MIX = %d' % mix)
    lines.append('PREFER_VERTICAL = %s' % ('True' if prefer_vertical else 'False'))
    lines.append('')
    lines.append('''
def _fit(cells, vertical):
    # vertical=True : two parallel vertical segments side by side (separated along columns)
    # vertical=False: two parallel horizontal segments stacked (separated along rows)
    if vertical:
        along = [y for y, x in cells]
        across = [x for y, x in cells]
    else:
        along = [x for y, x in cells]
        across = [y for y, x in cells]
    ac = sorted(set(across))
    al = sorted(set(along))
    if len(ac) != 2 or ac[1] - ac[0] < 2:
        return None
    if al[-1] - al[0] + 1 != len(al):
        return None
    if len(cells) != 2 * len(al):
        return None
    return ac[0], ac[1], al[0], len(al)


def _band_vertical(H, W, cl, cr, y0, L):
    # blocks of L rows anchored at the segment top; lines spread one column per block
    m = np.zeros((H, W), dtype=bool)
    for y in range(H):
        k = abs((y - y0) // L)
        for x in (cl - k, cr + k):
            if 0 <= x < W:
                m[y, x] = True
    return m


def _band_horizontal(H, W, rt, rb, x0, L):
    # blocks of L columns anchored at the segment start; lines spread one row per block
    m = np.zeros((H, W), dtype=bool)
    for x in range(W):
        k = abs((x - x0) // L)
        for y in (rt - k, rb + k):
            if 0 <= y < H:
                m[y, x] = True
    return m


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    colours = sorted(set(int(v) for v in np.unique(g)) - {BG})
    out = np.full((H, W), BG, dtype=int)
    total = np.zeros((H, W), dtype=int)
    for c in colours:
        ys, xs = np.nonzero(g == c)
        cells = [(int(y), int(x)) for y, x in zip(ys, xs)]
        mask = None
        for vertical in (PREFER_VERTICAL, not PREFER_VERTICAL):
            f = _fit(cells, vertical)
            if f is None:
                continue
            a, b, s, L = f
            if vertical:
                mask = _band_vertical(H, W, a, b, s, L)
            else:
                mask = _band_horizontal(H, W, a, b, s, L)
            break
        if mask is None:
            mask = (g == c)
        out[mask] = c
        total += mask.astype(int)
    out[total >= 2] = MIX
    return out.tolist()
''')
    return '\n'.join(lines)
