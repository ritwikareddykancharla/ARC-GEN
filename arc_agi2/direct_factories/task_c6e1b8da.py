"""c6e1b8da: boxes with a one-cell stick slide along the stick by its length.

Direct visible-coordinate program. Every non-background colour is one solid
rectangle, optionally carrying a one-cell-wide stick from the interior of one
side. The stick's side and length are read from the visible grid, so no D4
constant is needed; only the background colour palette[0] is specialised.

Hidden latent: the stacking order of still (stick-less) boxes. The program
enumerates every stacking that re-renders the visible input, keeps those whose
output is a valid constructor scene (all boxes show >= 3 corners) and answers
only if every surviving hypothesis yields the same full output grid. Otherwise
it raises ValueError. There is no tie-break, fallback order or clipping.
"""

PROGRAM = r'''
import numpy as np
from itertools import permutations

BG = __BG__
MAX_STILL = 6


def _trim(m, y0, y1, x0, x1):
    # Trim bounding-box edge lines that hold exactly one cell of the colour,
    # strictly inside the perpendicular extent (a stick, never a corner).
    dy = dx = 0
    while x1 > x0:
        idx = np.nonzero(m[y0:y1 + 1, x1])[0]
        if len(idx) == 1 and 0 < idx[0] < y1 - y0:
            x1 -= 1; dx += 1
        else:
            break
    while x1 > x0:
        idx = np.nonzero(m[y0:y1 + 1, x0])[0]
        if len(idx) == 1 and 0 < idx[0] < y1 - y0:
            x0 += 1; dx -= 1
        else:
            break
    while y1 > y0:
        idx = np.nonzero(m[y1, x0:x1 + 1])[0]
        if len(idx) == 1 and 0 < idx[0] < x1 - x0:
            y1 -= 1; dy += 1
        else:
            break
    while y1 > y0:
        idx = np.nonzero(m[y0, x0:x1 + 1])[0]
        if len(idx) == 1 and 0 < idx[0] < x1 - x0:
            y0 += 1; dy -= 1
        else:
            break
    return y0, y1, x0, x1, dy, dx


def _corners(a, c, y0, y1, x0, x1):
    H, W = a.shape
    n = 0
    for r, q in ((y0, x0), (y0, x1), (y1, x0), (y1, x1)):
        if 0 <= r < H and 0 <= q < W and a[r, q] == c:
            n += 1
    return n


def _analyse(g):
    still, moving = [], []
    for c in sorted(set(g.ravel().tolist()) - {BG}):
        m = g == c
        ys, xs = np.nonzero(m)
        y0, y1, x0, x1, dy, dx = _trim(m, int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max()))
        if y1 - y0 < 2 or x1 - x0 < 2:
            raise ValueError('colour is not a box of side >= 3')
        if dy and dx:
            raise ValueError('stick on two sides')
        if dy or dx:
            # A pulled box is never covered: solid rectangle plus exact stick.
            if not m[y0:y1 + 1, x0:x1 + 1].all():
                raise ValueError('pulled box is covered')
            if int(m.sum()) != (y1 - y0 + 1) * (x1 - x0 + 1) + abs(dy) + abs(dx):
                raise ValueError('stray cells of a pulled colour')
            moving.append((c, y0, y1, x0, x1, dy, dx))
        else:
            if _corners(g, c, y0, y1, x0, x1) < 3:
                raise ValueError('still box shows fewer than 3 corners')
            still.append((c, y0, y1, x0, x1, 0, 0))
    return still, moving


def _paint(canvas, boxes):
    for (c, y0, y1, x0, x1, dy, dx) in boxes:
        canvas[y0 + dy:y1 + dy + 1, x0 + dx:x1 + dx + 1] = c


def _candidates(g):
    H, W = g.shape
    still, moving = _analyse(g)
    if len(still) > MAX_STILL:
        raise ValueError('too many still boxes to enumerate')
    for (c, y0, y1, x0, x1, dy, dx) in moving:
        if y0 + dy < 0 or x0 + dx < 0 or y1 + dy >= H or x1 + dx >= W:
            raise ValueError('moved box leaves the grid')
    occ = np.zeros(g.shape, dtype=int)
    for (c, y0, y1, x0, x1, dy, dx) in moving:
        occ[y0 + dy:y1 + dy + 1, x0 + dx:x1 + dx + 1] += 1
    if (occ > 1).any():
        raise ValueError('moved boxes overlap')
    pulled = np.isin(g, [b[0] for b in moving])
    outs = {}
    for perm in permutations(range(len(still))):
        order = [still[k] for k in perm]
        cv = np.full(g.shape, BG, dtype=int)
        _paint(cv, order)
        cv[pulled] = g[pulled]
        if not np.array_equal(cv, g):
            continue
        out = np.full(g.shape, BG, dtype=int)
        _paint(out, order)
        _paint(out, moving)
        if all(_corners(out, c, y0 + dy, y1 + dy, x0 + dx, x1 + dx) >= 3
               for (c, y0, y1, x0, x1, dy, dx) in still + moving):
            outs[out.tobytes()] = out
    return list(outs.values())


def _recover(grid):
    outs = _candidates(np.array(grid, dtype=int))
    if len(outs) != 1:
        raise ValueError('%d valid stackings give different outputs' % len(outs) if outs else 'no valid stacking reproduces the input')
    return outs[0].tolist()


def solve(demonstrations, grid):
    for p in demonstrations:
        if not any(np.array_equal(o, np.array(p['output'], dtype=int)) for o in _candidates(np.array(p['input'], dtype=int))):
            raise ValueError('demonstration contradicts the slide mechanism')
    return _recover(grid)
'''


def build_program(d4, palette):
    return PROGRAM.replace('__BG__', str(int(palette[0])))
