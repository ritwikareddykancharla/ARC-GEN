TEMPLATE = """import numpy as np
from collections import deque

# Specialised by the factory from d4. Colours are inferred from pixels.
PANELS_SIDE_BY_SIDE = __HORIZ__
DESIGN_AT_LOW_SIDE = __LOW__


def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out


def _bbox(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return min(ys), min(xs), max(ys), max(xs)


def _place(lo, hi, ilo, ihi, jlo, jhi):
    n = hi - lo + 1
    if lo == ilo and hi == ihi:
        return jlo, jhi, True
    if lo == ilo:
        return jlo, jlo + n - 1, False
    if hi == ihi:
        return jhi - n + 1, jhi, False
    s = jlo + (lo - ilo)
    return s, s + n - 1, False


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    frame = int(g[0, 0])
    comps = sorted(_components(g != frame), key=len, reverse=True)[:2]
    if len(comps) < 2:
        return out.tolist()
    boxes = [_bbox(c) for c in comps]

    def ncol(b):
        y0, x0, y1, x1 = b
        return len(np.unique(g[y0:y1 + 1, x0:x1 + 1]))

    k0, k1 = ncol(boxes[0]), ncol(boxes[1])
    if k0 != k1:
        di = 0 if k0 > k1 else 1
    else:
        if PANELS_SIDE_BY_SIDE:
            lowi = 0 if boxes[0][1] < boxes[1][1] else 1
        else:
            lowi = 0 if boxes[0][0] < boxes[1][0] else 1
        di = lowi if DESIGN_AT_LOW_SIDE else 1 - lowi
    dy0, dx0, dy1, dx1 = boxes[di]
    cy0, cx0, cy1, cx1 = boxes[1 - di]
    pc = int(g[dy0, dx0])
    sub = g[dy0:dy1 + 1, dx0:dx1 + 1]
    for colour in sorted(set(sub.ravel().tolist()) - {pc}):
        for cells in _components(sub == colour):
            cells = [(y + dy0, x + dx0) for y, x in cells]
            sy0, sx0, sy1, sx1 = _bbox(cells)
            if PANELS_SIDE_BY_SIDE:
                a, b, stretch = _place(sx0, sx1, dx0 + 1, dx1 - 1, cx0 + 1, cx1 - 1)
                if stretch:
                    out[sy0:sy1 + 1, a:b + 1] = colour
                else:
                    for y, x in cells:
                        nx = a + (x - sx0)
                        if 0 <= nx < W:
                            out[y, nx] = colour
            else:
                a, b, stretch = _place(sy0, sy1, dy0 + 1, dy1 - 1, cy0 + 1, cy1 - 1)
                if stretch:
                    out[a:b + 1, sx0:sx1 + 1] = colour
                else:
                    for y, x in cells:
                        ny = a + (y - sy0)
                        if 0 <= ny < H:
                            out[ny, x] = colour
    return out.tolist()
"""


def build_program(d4, palette):
    side = {0: 'left', 1: 'top', 2: 'right', 3: 'bottom',
            4: 'right', 5: 'bottom', 6: 'left', 7: 'top'}[int(d4) % 8]
    horizontal = side in ('left', 'right')
    design_low = side in ('left', 'top')
    return TEMPLATE.replace('__HORIZ__', repr(horizontal)).replace('__LOW__', repr(design_low))
