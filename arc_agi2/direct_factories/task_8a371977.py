def build_program(d4, palette):
    zero = int(palette[0])
    border_col = int(palette[2])
    inner_col = int(palette[3])
    src = '''import numpy as np
from collections import deque

CELL = %d
BORDER = %d
INNER = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
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

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    comps = _components(g == CELL)
    if not comps:
        return out.tolist()
    boxes = []
    for c in comps:
        ys = [p[0] for p in c]
        xs = [p[1] for p in c]
        boxes.append((min(ys), min(xs), max(ys), max(xs)))
    tops = sorted(set(b[0] for b in boxes))
    lefts = sorted(set(b[1] for b in boxes))
    border, inner = [], []
    for c, b in zip(comps, boxes):
        if b[0] in (tops[0], tops[-1]) or b[1] in (lefts[0], lefts[-1]):
            border.append(c)
        else:
            inner.append(c)
    for c in border:
        for y, x in c:
            out[y, x] = BORDER
    for c in inner:
        for y, x in c:
            out[y, x] = INNER
    return out.tolist()
''' % (zero, border_col, inner_col)
    return src
