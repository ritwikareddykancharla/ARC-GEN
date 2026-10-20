_TEMPLATE = '''import numpy as np
from collections import Counter, deque

# BAND_AXIS 0: bands are full-width rows (end colour in first/last column), parts move vertically.
# BAND_AXIS 1: bands are full-height columns (end colour in first/last row), parts move horizontally.
BAND_AXIS = __AXIS__
# TOWARD_MAX True: a part's far edge (max index) touches the band's max line.
# TOWARD_MAX False: a part's near edge (min index) touches the band's min line.
TOWARD_MAX = __TMAX__


def _band_lines(g):
    H, W = g.shape
    lines = {}
    if BAND_AXIS == 0:
        if W < 3:
            return lines
        for y in range(H):
            inner = g[y, 1:W - 1]
            f = int(inner[0])
            e = int(g[y, 0])
            if (inner == f).all() and int(g[y, W - 1]) == e and e != f:
                lines[y] = (f, e)
    else:
        if H < 3:
            return lines
        for x in range(W):
            inner = g[1:H - 1, x]
            f = int(inner[0])
            e = int(g[0, x])
            if (inner == f).all() and int(g[H - 1, x]) == e and e != f:
                lines[x] = (f, e)
    return lines


def _group(lines):
    bands = {}
    for i in sorted(lines):
        f, e = lines[i]
        if f in bands and bands[f][1] == i - 1 and bands[f][2] == e:
            lo, _, _ = bands[f]
            bands[f] = (lo, i, e)
        else:
            bands[f] = (i, i, e)
    return bands


def _components(mask):
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                comps.append(sorted(cells))
    return comps


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    lines = _band_lines(g)
    bands = _group(lines)
    band_mask = np.zeros((H, W), dtype=bool)
    for i in lines:
        if BAND_AXIS == 0:
            band_mask[i, :] = True
        else:
            band_mask[:, i] = True
    free = ~band_mask
    shape_mask = free & (g != bg)
    out = g.copy()
    out[shape_mask] = bg
    for comp in _components(shape_mask):
        by_col = {}
        for y, x in comp:
            by_col.setdefault(int(g[y, x]), []).append((y, x))
        for c in sorted(by_col):
            if c not in bands:
                continue
            lo, hi, e = bands[c]
            cells = by_col[c]
            if BAND_AXIS == 0:
                ys = [y for y, _ in cells]
                shift = (hi - max(ys)) if TOWARD_MAX else (lo - min(ys))
                for y, x in cells:
                    ny = y + shift
                    if lo <= ny <= hi:
                        out[ny, x] = e
            else:
                xs = [x for _, x in cells]
                shift = (hi - max(xs)) if TOWARD_MAX else (lo - min(xs))
                for y, x in cells:
                    nx = x + shift
                    if lo <= nx <= hi:
                        out[y, nx] = e
    return out.tolist()
'''


def build_program(d4, palette):
    k = int(d4) % 4
    # Original drop direction is +row (down). Clockwise rotations map it to:
    # k=0 down (rows, toward max), k=1 left (cols, toward min),
    # k=2 up (rows, toward min), k=3 right (cols, toward max).
    # The row reversal applied for d4>=4 does not change the drop direction.
    axis = 0 if k % 2 == 0 else 1
    toward_max = k in (0, 3)
    return _TEMPLATE.replace('__AXIS__', str(axis)).replace('__TMAX__', 'True' if toward_max else 'False')
