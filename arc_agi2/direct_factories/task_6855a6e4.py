def build_program(d4, palette):
    bg = int(palette[0])
    red = int(palette[2])
    template = '''import numpy as np
from collections import deque

BG = __BG__
RED = __RED__


def _components(mask):
    mask = np.asarray(mask, bool)
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _box(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return (min(ys), min(xs), max(ys), max(xs))


def _gap(a, b):
    ay0, ax0, ay1, ax1 = a
    by0, bx0, by1, bx1 = b
    dy = max(0, by0 - ay1, ay0 - by1)
    dx = max(0, bx0 - ax1, ax0 - bx1)
    return dy + dx


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    brackets = [_box(c) for c in _components(g == RED)]
    movers = []
    for colour in sorted(set(g.ravel().tolist()) - {BG, RED}):
        for cells in _components(g == colour):
            movers.append((colour, cells))
    if not brackets or not movers:
        return out.tolist()
    for colour, cells in movers:
        for y, x in cells:
            out[y, x] = BG
    for colour, cells in movers:
        mb = _box(cells)
        my0, mx0, my1, mx1 = mb
        cy = (my0 + my1) / 2.0
        cx = (mx0 + mx1) / 2.0
        best = None
        bestkey = None
        for i, b in enumerate(brackets):
            by0, bx0, by1, bx1 = b
            d = abs((by0 + by1) / 2.0 - cy) + abs((bx0 + bx1) / 2.0 - cx)
            key = (d, _gap(mb, b), i)
            if bestkey is None or key < bestkey:
                bestkey = key
                best = b
        by0, bx0, by1, bx1 = best
        new = []
        for y, x in cells:
            if mx1 < bx0:
                ny, nx = y, 2 * bx0 - x
            elif mx0 > bx1:
                ny, nx = y, 2 * bx1 - x
            elif my1 < by0:
                ny, nx = 2 * by0 - y, x
            elif my0 > by1:
                ny, nx = 2 * by1 - y, x
            else:
                ny, nx = y, x
            new.append((ny, nx))
        for ny, nx in new:
            if 0 <= ny < H and 0 <= nx < W:
                out[ny, nx] = colour
    return out.tolist()
'''
    return template.replace('__BG__', str(bg)).replace('__RED__', str(red))
