_BODY = '''
import numpy as np
from collections import deque


def _components8(mask):
    h, w = mask.shape
    seen = np.zeros(mask.shape, dtype=bool)
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
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                out.append(cells)
    return out


def _crop_not(sub, colour):
    if sub.size == 0:
        return None
    ys, xs = np.where(sub != colour)
    if len(ys) == 0:
        return None
    return sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def _cut(P, lo, hi):
    lo = max(lo, 0)
    if VERT:
        return P[lo:hi, :]
    return P[:, lo:hi]


def _full_lines(a, rows):
    if rows:
        return [i for i in range(a.shape[0]) if np.all(a[i, :] == C6)]
    return [j for j in range(a.shape[1]) if np.all(a[:, j] == C6)]


def _cw(v):
    return (v[1], -v[0])


def _stamp_legend(P, out):
    n = P.shape[0] if VERT else P.shape[1]
    bands = _full_lines(P, VERT)
    if len(bands) < 2:
        return
    if DOWN_POS:
        b0, b1 = bands[0], bands[1]
        b2 = bands[2] if len(bands) > 2 else n
        upper = _cut(P, 0, b0)
        box1 = _cut(P, b0 + 1, b1)
        box2 = _cut(P, b1 + 1, b2)
    else:
        b0, b1 = bands[-1], bands[-2]
        b2 = bands[-3] if len(bands) > 2 else -1
        upper = _cut(P, b0 + 1, n)
        box1 = _cut(P, b1 + 1, b0)
        box2 = _cut(P, b2 + 1, b1)
    k1 = _crop_not(box1, C6)
    k2 = _crop_not(box2, C6)
    if k1 is None or k2 is None or upper.size == 0:
        return
    ys, xs = np.where(k1 == C4)
    if len(ys) == 0:
        return
    bottom = ys[0] >= k1.shape[0] / 2.0
    right = xs[0] >= k1.shape[1] / 2.0
    cy, cx = k2.shape[0] // 2, k2.shape[1] // 2
    ys, xs = np.where(k2 == C7)
    dy = int(np.sum(ys - cy))
    dx = int(np.sum(xs - cx))
    if dy == 0 and dx == 0:
        return
    if abs(dy) >= abs(dx):
        arrow = (1 if dy > 0 else -1, 0)
    else:
        arrow = (0, 1 if dx > 0 else -1)
    turns = 0
    v = UP
    while v != arrow and turns < 4:
        v = _cw(v)
        turns += 1
    tile = None
    shape = None
    for cells in _components8(upper != C0):
        cols = set(int(upper[y, x]) for y, x in cells)
        yy = [c[0] for c in cells]
        xx = [c[1] for c in cells]
        sub = upper[min(yy):max(yy) + 1, min(xx):max(xx) + 1]
        if len(cols) == 2 and tile is None:
            tile = sub.copy()
        elif len(cols) == 1 and shape is None:
            shape = sub == next(iter(cols))
    if tile is None or shape is None:
        return
    a, b = sorted(set(tile.ravel().tolist()))
    sw = np.where(tile == a, b, a)
    mask = np.rot90(shape, -turns)
    th, tw = sw.shape
    mh, mw = mask.shape
    CH, CW = out.shape
    oy = CH - mh * th if bottom else 0
    ox = CW - mw * tw if right else 0
    for i in range(mh):
        for j in range(mw):
            if mask[i, j]:
                y = oy + i * th
                x = ox + j * tw
                if 0 <= y and y + th <= CH and 0 <= x and x + tw <= CW:
                    out[y:y + th, x:x + tw] = sw


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    div = _full_lines(g, not VERT)
    n_cross = W if VERT else H
    strips = []
    start = 0
    for p in div + [n_cross]:
        if p > start:
            strips.append((start, p - 1))
        start = p + 1
    if not strips:
        return g.tolist()
    canvas = max(strips, key=lambda s: s[1] - s[0])
    legends = [s for s in strips if s != canvas]
    if VERT:
        out = g[:, canvas[0]:canvas[1] + 1].copy()
    else:
        out = g[canvas[0]:canvas[1] + 1, :].copy()
    for s0, s1 in legends:
        P = g[:, s0:s1 + 1] if VERT else g[s0:s1 + 1, :]
        _stamp_legend(P, out)
    return out.tolist()
'''


def build_program(d4, palette):
    d4 = int(d4)
    vd = (1, 0)
    if d4 >= 4:
        vd = (vd[0], -vd[1])
    for _ in range(d4 % 4):
        vd = (vd[1], -vd[0])
    vert = vd[0] != 0
    down_pos = (vd[0] if vert else vd[1]) > 0
    up = (-vd[0], -vd[1])
    head = ('C6 = %d\nC0 = %d\nC4 = %d\nC7 = %d\nVERT = %r\nDOWN_POS = %r\nUP = (%d, %d)\n'
            % (int(palette[6]), int(palette[0]), int(palette[4]), int(palette[7]),
               bool(vert), bool(down_pos), up[0], up[1]))
    return head + _BODY
