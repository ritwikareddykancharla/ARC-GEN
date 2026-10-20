def build_program(d4, palette):
    bg = int(palette[0])
    axis = 1 if (int(d4) % 2 == 1) else 0
    src = '''import numpy as np

BG = __BG__
# AXIS 0: the band is a block of full-width rows and is tiled vertically.
# AXIS 1: the band is a block of full-height columns and is tiled horizontally.
AXIS = __AXIS__


def _count(g):
    return g.shape[0] if AXIS == 0 else g.shape[1]


def _line(g, i):
    return g[i, :] if AXIS == 0 else g[:, i]


def _band(g):
    n = _count(g)
    occ = [i for i in range(n) if (_line(g, i) != BG).any()]
    if not occ:
        return None
    return min(occ), max(occ)


def _stamp(out, band, start, n):
    h = len(band)
    for i in range(h):
        y = start + i
        if 0 <= y < n:
            src = band[i]
            mask = src != BG
            if AXIS == 0:
                row = out[y, :]
                row[mask] = src[mask]
                out[y, :] = row
            else:
                col = out[:, y]
                col[mask] = src[mask]
                out[:, y] = col


def _tile(g, p=None):
    g = np.array(g, dtype=int)
    b = _band(g)
    if b is None:
        return g.copy()
    y0, y1 = b
    h = y1 - y0 + 1
    if p is None or p < 1:
        p = h
    n = _count(g)
    band = [_line(g, y0 + i).copy() for i in range(h)]
    out = g.copy()
    s = y0 - p
    while s + h > 0:
        _stamp(out, band, s, n)
        s -= p
    s = y0 + p
    while s < n:
        _stamp(out, band, s, n)
        s += p
    return out


def _choose_period(demonstrations):
    pairs = []
    for d in demonstrations or []:
        try:
            a = np.array(d['input'], dtype=int)
            b = np.array(d['output'], dtype=int)
        except Exception:
            continue
        if a.ndim != 2 or a.shape != b.shape:
            continue
        pairs.append((a, b))
    if not pairs:
        return None
    if all(np.array_equal(_tile(a), b) for a, b in pairs):
        return None
    limit = max(_count(a) for a, _ in pairs)
    for p in range(1, limit + 1):
        if all(np.array_equal(_tile(a, p), b) for a, b in pairs):
            return p
    return None


def solve(demonstrations, grid):
    p = _choose_period(demonstrations)
    out = _tile(grid, p)
    return out.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__AXIS__', str(axis))
