TEMPLATE = r'''
import numpy as np
from collections import deque, Counter

BG = __BG__
LOOP = __LOOP__
FRAME = __FRAME__
REVERSED = __REVERSED__


def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
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
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out


def _boxes(g):
    res = []
    for comp in _components(g == FRAME):
        ys = [c[0] for c in comp]
        xs = [c[1] for c in comp]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        if y1 - y0 < 2 or x1 - x0 < 2:
            continue
        inner = g[y0 + 1:y1, x0 + 1:x1]
        vals = [int(v) for v in inner.ravel() if v != BG and v != FRAME and v != LOOP]
        if not vals:
            continue
        col = Counter(vals).most_common(1)[0][0]
        res.append({'box': (y0, x0, y1, x1), 'col': col,
                    'cy': (y0 + y1) / 2.0, 'cx': (x0 + x1) / 2.0})
    return res


def _keys(g, boxes):
    # Clockwise position (visible coordinates, y down) along the loop rectangle.
    ys, xs = np.nonzero(g == LOOP)
    if len(ys) == 0:
        import math
        my = sum(b['cy'] for b in boxes) / len(boxes)
        mx = sum(b['cx'] for b in boxes) / len(boxes)
        return [math.atan2(b['cy'] - my, b['cx'] - mx) for b in boxes]
    r0, r1, c0, c1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    W = c1 - c0
    H = r1 - r0
    keys = []
    for b in boxes:
        cy, cx = b['cy'], b['cx']
        px = min(max(cx, c0), c1)
        py = min(max(cy, r0), r1)
        cands = [((cy - r0) ** 2 + (cx - px) ** 2, px - c0),
                 ((cx - c1) ** 2 + (cy - py) ** 2, W + (py - r0)),
                 ((cy - r1) ** 2 + (cx - px) ** 2, W + H + (c1 - px)),
                 ((cx - c0) ** 2 + (cy - py) ** 2, 2 * W + H + (r1 - py))]
        keys.append(min(cands)[1])
    return keys


def _apply(g, step):
    out = g.copy()
    boxes = _boxes(g)
    n = len(boxes)
    if n < 2:
        return out
    keys = _keys(g, boxes)
    order = sorted(range(n), key=lambda i: (keys[i], boxes[i]['cy'], boxes[i]['cx']))
    for k, i in enumerate(order):
        b = boxes[i]
        nxt = boxes[order[(k + step) % n]]['col']
        y0, x0, y1, x1 = b['box']
        region = out[y0 + 1:y1, x0 + 1:x1]
        orig = g[y0 + 1:y1, x0 + 1:x1]
        region[orig == b['col']] = nxt
    return out


def _pair(d):
    if isinstance(d, dict):
        return d.get('input'), d.get('output')
    return d[0], d[1]


def solve(demonstrations, grid):
    step = -1 if REVERSED else 1

    def ok(s):
        try:
            for d in demonstrations or []:
                a, b = _pair(d)
                if a is None or b is None:
                    continue
                pa = _apply(np.array(a, dtype=int), s)
                pb = np.array(b, dtype=int)
                if pa.shape != pb.shape or not np.array_equal(pa, pb):
                    return False
            return True
        except Exception:
            return False

    if demonstrations and not ok(step) and ok(-step):
        step = -step
    return _apply(np.array(grid, dtype=int), step).tolist()
'''


def build_program(d4, palette):
    pal = [int(p) for p in palette]
    rev = 'True' if int(d4) >= 4 else 'False'
    return (TEMPLATE.replace('__BG__', str(pal[0]))
            .replace('__LOOP__', str(pal[1]))
            .replace('__FRAME__', str(pal[2]))
            .replace('__REVERSED__', rev))
