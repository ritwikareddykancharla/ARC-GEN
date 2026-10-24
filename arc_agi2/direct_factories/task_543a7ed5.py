# Repair (RE-ARC domain review): objects are the four-connected components of
# every non-background input colour, not only native pink (palette[6]). Native
# inputs contain one object colour, so their result is unchanged; RE-ARC draws
# up to seven object colours and its verifier rings every univalued object.
def build_program(d4, palette):
    bg = int(palette[8])
    ring = int(palette[3])
    hole = int(palette[4])
    src = '''import numpy as np
from collections import deque

BG = __BG__
RING = __RING__
HOLE = __HOLE__

def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
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
    H, W = g.shape
    out = g.copy()
    # enclosed background pockets (not touching the grid border) become HOLE
    for comp in _components(g == BG):
        if not any(y == 0 or y == H - 1 or x == 0 or x == W - 1 for y, x in comp):
            for y, x in comp:
                out[y, x] = HOLE
    # one-cell ring around each object's bounding box, painted on background only;
    # every non-background colour forms objects (one per four-connected component)
    comps = []
    for colour in sorted(set(g.ravel().tolist()) - {BG}):
        comps.extend(_components(g == colour))
    for comp in comps:
        ys = [c[0] for c in comp]
        xs = [c[1] for c in comp]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        for y in range(max(0, y0 - 1), min(H, y1 + 2)):
            for x in range(max(0, x0 - 1), min(W, x1 + 2)):
                if (y < y0 or y > y1 or x < x0 or x > x1) and out[y, x] == BG:
                    out[y, x] = RING
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg))
    src = src.replace('__RING__', str(ring)).replace('__HOLE__', str(hole))
    return src
