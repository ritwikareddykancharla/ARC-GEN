def build_program(d4, palette):
    frame = int(palette[4])
    one = int(palette[1])
    zero = int(palette[0])
    src = '''import numpy as np
from collections import deque

FRAME = %d
ONE = %d
ZERO = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
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

def _box(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return min(ys), min(xs), max(ys), max(xs)

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    comps = _components(g != FRAME)
    legend = None
    panels = []
    for cells in comps:
        y0, x0, y1, x1 = _box(cells)
        hh, ww = y1 - y0 + 1, x1 - x0 + 1
        if len(cells) == 36 and hh == 6 and ww == 6:
            if legend is None:
                legend = (y0, x0)
        elif len(cells) == 9 and hh == 3 and ww == 3:
            panels.append((y0, x0))
    if legend is None:
        return out.tolist()
    ly, lx = legend
    bc = g[ly:ly + 6, lx:lx + 6]
    cols = [int(c) for c in np.unique(bc) if int(c) != ZERO and int(c) != FRAME]
    if not cols:
        return out.tolist()
    # special colour = most frequent non-zero, non-frame colour in legend
    special = max(cols, key=lambda c: (int(np.sum(bc == c)), -c))
    pat = bc[::2, ::2] == special
    if not pat.any():
        return out.tolist()
    for (a, b) in panels:
        sub = g[a:a + 3, b:b + 3]
        if np.all(sub[pat] == ONE):
            region = out[a:a + 3, b:b + 3]
            region[pat] = special
            out[a:a + 3, b:b + 3] = region
    return out.tolist()
''' % (frame, one, zero)
    return src
