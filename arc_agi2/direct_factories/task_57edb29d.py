def build_program(d4, palette):
    frame = int(palette[4])
    src = '''import numpy as np
from collections import deque

FRAME = __FRAME__

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
    frame = FRAME
    if not np.any(g == frame):
        frame = int(g[0, 0])
    boxes = []
    for cells in _components(g != frame):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        sub = g[min(ys):max(ys) + 1, min(xs):max(xs) + 1]
        boxes.append(sub)
    marked = set()
    mcol = None
    blank = None
    col_line = False
    row_line = False
    for sub in boxes:
        h, w = sub.shape
        fill = int(sub[0, 0])
        if np.all(sub == fill):
            if blank is None or sub.size > blank[0] * blank[1]:
                blank = (h, w, fill)
            continue
        for y in range(h):
            for x in range(w):
                v = int(sub[y, x])
                if v != fill:
                    mcol = v
                    dy = min(y, h - 1 - y)
                    dx = min(x, w - 1 - x)
                    marked.add((dy, dx))
                    if dx == 1 and dy >= 3:
                        col_line = True
                    if dy == 1 and dx >= 3:
                        row_line = True
    if blank is None:
        sub = min(boxes, key=lambda s: int(np.sum(s != s[0, 0])))
        blank = (sub.shape[0], sub.shape[1], int(sub[0, 0]))
    h, w, fill = blank
    out = np.full((h, w), fill, dtype=int)
    if mcol is None:
        return out.tolist()
    for y in range(h):
        for x in range(w):
            dy = min(y, h - 1 - y)
            dx = min(x, w - 1 - x)
            hit = (dy, dx) in marked
            if col_line and dx == 1 and dy >= 1:
                hit = True
            if row_line and dy == 1 and dx >= 1:
                hit = True
            if hit:
                out[y, x] = mcol
    return out.tolist()
'''
    return src.replace('__FRAME__', str(frame))
