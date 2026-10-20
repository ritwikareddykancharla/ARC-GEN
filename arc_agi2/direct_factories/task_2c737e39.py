def build_program(d4, palette):
    bg = int(palette[0])
    marker = int(palette[5])
    src = '''import numpy as np
from collections import deque

BG = %d
MARK = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    steps = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
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

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    objs = _components(g != BG)
    if not objs:
        return g.tolist()
    # Lone marker: a single-cell object of the marker colour.
    target = None
    for cells in objs:
        if len(cells) == 1 and g[cells[0]] == MARK:
            target = cells[0]
    # Pattern: the largest multicolour (8-connected) object; its marker cell is the anchor.
    pattern = max(objs, key=lambda c: len(c))
    anchor = None
    for (y, x) in pattern:
        if g[y, x] == MARK:
            anchor = (y, x)
    out = g.copy()
    if target is None or anchor is None or len(pattern) == 1:
        return out.tolist()
    dy, dx = target[0] - anchor[0], target[1] - anchor[1]
    out[target] = BG
    for (y, x) in pattern:
        if g[y, x] == MARK:
            continue
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W:
            out[ny, nx] = g[y, x]
    return out.tolist()
''' % (bg, marker)
    return src
