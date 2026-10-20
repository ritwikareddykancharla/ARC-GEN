def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[7])
    k = int(d4) % 4
    flip = int(d4) >= 4
    n = 9

    def m(r, c):
        if flip:
            c = n - 1 - c
        for _ in range(k):
            r, c = c, n - 1 - r
        return r, c

    def tbox(b):
        r0, c0, r1, c1 = b
        p = m(r0, c0)
        q = m(r1, c1)
        return (min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]))

    def anti(b):
        r0, c0, r1, c1 = b
        return (n - 1 - c1, n - 1 - r1, n - 1 - c0, n - 1 - r0)

    base = [(1, 0, 3, 2), (4, 5, 6, 7)]
    configs = [[tbox(b) for b in base], [tbox(anti(b)) for b in base]]

    template = '''import numpy as np
from collections import deque

BG = __BG__
FILL = __FILL__
CONFIGS = __CONFIGS__

def _components(g):
    h, w = g.shape
    mask = g != BG
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                comps.append(cells)
    return comps

def _bbox(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return (min(ys), min(xs), max(ys), max(xs))

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    h, w = g.shape
    boxes = [_bbox(c) for c in _components(g)]
    assign = None
    if (h, w) == (9, 9) and boxes:
        for cfg in CONFIGS:
            chosen = []
            ok = True
            for b in boxes:
                hits = [tuple(s) for s in cfg if s[0] <= b[0] and s[1] <= b[1] and b[2] <= s[2] and b[3] <= s[3]]
                if not hits:
                    ok = False
                    break
                chosen.append(hits[0])
            if ok and len(set(chosen)) == len(chosen):
                assign = chosen
                break
    if assign is None:
        assign = boxes
    for (r0, c0, r1, c1) in assign:
        sub = out[r0:r1 + 1, c0:c1 + 1]
        sub[sub == BG] = FILL
    return out.tolist()
'''
    return template.replace('__BG__', repr(bg)).replace('__FILL__', repr(fill)).replace('__CONFIGS__', repr(configs))
