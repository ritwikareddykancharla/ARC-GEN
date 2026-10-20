def build_program(d4, palette):
    bg = int(palette[0])
    sq = int(palette[1])
    fill = int(palette[8])
    src = '''import numpy as np
from collections import deque

BG = __BG__
SQ = __SQ__
FILL = __FILL__

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
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    comps = _components(g == SQ)
    if not comps:
        return g.tolist()
    boxes = []
    for cells in comps:
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        boxes.append((min(ys), min(xs), max(ys), max(xs), cells))
    boxes.sort(key=lambda b: (b[0], b[1]))
    y0, x0, y1, x1, cells = boxes[0]
    th, tw = y1 - y0 + 1, x1 - x0 + 1
    tmpl = np.zeros((th, tw), bool)
    for (cy, cx) in cells:
        tmpl[cy - y0, cx - x0] = True
    tops = sorted({b[0] for b in boxes})
    lefts = sorted({b[1] for b in boxes})
    occupied = {(b[0], b[1]) for b in boxes}
    out = g.copy()
    for y in tops:
        for x in lefts:
            if (y, x) in occupied:
                continue
            for i in range(th):
                for j in range(tw):
                    if tmpl[i, j]:
                        yy, xx = y + i, x + j
                        if 0 <= yy < H and 0 <= xx < W and out[yy, xx] == BG:
                            out[yy, xx] = FILL
    return out.tolist()
'''
    return src.replace('__BG__', repr(bg)).replace('__SQ__', repr(sq)).replace('__FILL__', repr(fill))
