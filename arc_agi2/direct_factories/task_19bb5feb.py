def build_program(d4, palette):
    bg = int(palette[0])
    rect = int(palette[8])
    src = '''import numpy as np
from collections import deque

BG = %d
RECT = %d

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

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    ys, xs = np.nonzero(g == RECT)
    if len(ys) == 0:
        mask = g != BG
        y0r, x0r = 0, 0
        sub = g
    else:
        y0r, y1r, x0r, x1r = ys.min(), ys.max(), xs.min(), xs.max()
        sub = g[y0r:y1r + 1, x0r:x1r + 1]
        mask = sub != RECT
    blocks = []
    for comp in _components(mask):
        by = min(c[0] for c in comp)
        bx = min(c[1] for c in comp)
        col = int(sub[by, bx])
        if col == RECT:
            continue
        blocks.append((by, bx, col))
    if not blocks:
        return [[BG]]
    rows = sorted(set(b[0] for b in blocks))
    cols = sorted(set(b[1] for b in blocks))
    out = [[BG] * len(cols) for _ in rows]
    for by, bx, col in sorted(blocks):
        out[rows.index(by)][cols.index(bx)] = col
    return out
''' % (bg, rect)
    return src
