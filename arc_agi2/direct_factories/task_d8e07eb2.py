TEMPLATE = '''import numpy as np
from collections import deque

BG = __BG__
MARK = __MARK__
FAIL = __FAIL__
AXIS = __AXIS__
SIGN = __SIGN__


def _glyphs(g, region):
    H, W = g.shape
    seen = np.zeros((H, W), dtype=bool)
    res = []
    for y in range(H):
        for x in range(W):
            if not region[y, x] or seen[y, x] or g[y, x] == BG:
                continue
            col = int(g[y, x])
            seen[y, x] = True
            queue = deque([(y, x)])
            cells = []
            while queue:
                cy, cx = queue.popleft()
                cells.append((cy, cx))
                for ddy in (-1, 0, 1):
                    for ddx in (-1, 0, 1):
                        ny, nx = cy + ddy, cx + ddx
                        if 0 <= ny < H and 0 <= nx < W and region[ny, nx] and not seen[ny, nx] and g[ny, nx] == col:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            y0, x0, y1, x1 = min(ys), min(xs), max(ys), max(xs)
            shape = frozenset((cy - y0, cx - x0) for cy, cx in cells)
            res.append(((col, shape), (y0, x0, y1, x1)))
    return res


def _span(box, axis):
    if axis == 0:
        return box[0], box[2]
    return box[1], box[3]


def _snap(v0, v1, starts, fallback):
    for s in starts:
        if s <= v0 and v1 <= s + 2:
            return s
    return fallback


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    L = H if AXIS == 0 else W
    M = W if AXIS == 0 else H
    divs = []
    for i in range(L):
        line = g[i, :] if AXIS == 0 else g[:, i]
        if line[0] != BG and np.all(line == line[0]):
            divs.append(i)
    if len(divs) < 2:
        return out.tolist()
    lo, hi = divs[0], divs[-1]
    pc = np.indices((H, W))[AXIS]
    if SIGN > 0:
        dq = lo
        qmask = pc < lo
        rmask = pc > hi
    else:
        dq = hi
        qmask = pc > hi
        rmask = pc < lo
    cmask = (pc > lo) & (pc < hi)
    queries = _glyphs(g, qmask)
    cat = _glyphs(g, cmask)
    pstarts = sorted(set(_span(b, AXIS)[0] for _, b in cat if _span(b, AXIS)[1] - _span(b, AXIS)[0] == 2))
    sstarts = sorted(set(_span(b, 1 - AXIS)[0] for _, b in cat if _span(b, 1 - AXIS)[1] - _span(b, 1 - AXIS)[0] == 2))
    matches = []
    for qkey, _ in queries:
        for ckey, cbox in cat:
            if ckey != qkey:
                continue
            p0, p1 = _span(cbox, AXIS)
            s0, s1 = _span(cbox, 1 - AXIS)
            if SIGN > 0:
                pf = dq + 3 + 5 * ((p0 - dq - 3) // 5)
            else:
                pf = dq - 5 - 5 * ((dq - 3 - p1) // 5)
            sf = 2 + 5 * ((s0 - 2) // 5)
            matches.append((_snap(p0, p1, pstarts, pf), _snap(s0, s1, sstarts, sf)))
            break
    for ps, ss in matches:
        for a in range(max(ps - 1, 0), min(ps + 4, L)):
            for b in range(max(ss - 1, 0), min(ss + 4, M)):
                y, x = (a, b) if AXIS == 0 else (b, a)
                if out[y, x] == BG:
                    out[y, x] = MARK
    success = (len(matches) > 1 and len(matches) == len(queries) and
               (len(set(m[0] for m in matches)) == 1 or len(set(m[1] for m in matches)) == 1))
    if success:
        out[rmask & (out == BG)] = MARK
        out[qmask & (out == BG)] = MARK
    else:
        out[rmask & (out == BG)] = FAIL
    return out.tolist()
'''


def build_program(d4, palette):
    d4 = int(d4) % 8
    dy, dx = 1, 0
    if d4 >= 4:
        dx = -dx
    for _ in range(d4 % 4):
        dy, dx = dx, -dy
    if dy != 0:
        axis, sign = 0, dy
    else:
        axis, sign = 1, dx
    pal = [int(palette[c]) for c in range(10)]
    src = TEMPLATE
    for key, val in (('__BG__', pal[8]), ('__MARK__', pal[3]), ('__FAIL__', pal[2]), ('__AXIS__', axis), ('__SIGN__', sign)):
        src = src.replace(key, str(val))
    return src
