def build_program(d4, palette):
    RING = int(palette[1])
    RED = int(palette[2])
    RECT = int(palette[3])
    src = '''import numpy as np
from collections import deque

RING = %d
RED = %d
RECT = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps = []
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
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    active = np.zeros((H, W), dtype=bool)
    # Reds lying inside the bounding box of a rectangle-coloured component.
    for cells in _components(g == RECT):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        sub = g[y0:y1 + 1, x0:x1 + 1] == RED
        active[y0:y1 + 1, x0:x1 + 1] |= sub
    # Reds embedded in a rectangle (>=2 orthogonal rectangle neighbours);
    # covers rectangles split into several components by lines of reds.
    for y in range(H):
        for x in range(W):
            if g[y, x] != RED:
                continue
            n = 0
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and g[ny, nx] == RECT:
                    n += 1
            if n >= 2:
                active[y, x] = True
    for y in range(H):
        for x in range(W):
            if not active[y, x]:
                continue
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and not active[yy, xx]:
                        out[yy, xx] = RING
    return out.tolist()
''' % (RING, RED, RECT)
    return src
