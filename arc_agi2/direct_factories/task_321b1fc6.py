def build_program(d4, palette):
    bg = int(palette[0])
    marker = int(palette[8])
    src = '''import numpy as np
from collections import deque

BG = %d
MARKER = %d

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
                out.append(sorted(cells))
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    comps = _components(g == MARKER)
    tcells = [(int(y), int(x)) for y, x in zip(*np.nonzero((g != BG) & (g != MARKER)))]
    if not tcells:
        return out.tolist()
    ty0 = min(c[0] for c in tcells)
    tx0 = min(c[1] for c in tcells)
    tset = set(tcells)
    # shape outline (relative to its bounding box) taken from a marker copy
    shape = None
    if comps:
        c0 = max(comps, key=len)
        sy0 = min(c[0] for c in c0)
        sx0 = min(c[1] for c in c0)
        shape = set((y - sy0, x - sx0) for y, x in c0)
    # locate the template's bbox origin: prefer the bbox of non-bg cells,
    # otherwise find an origin whose shape placement covers all template cells
    origin = (ty0, tx0)
    if shape is not None:
        def fits(oy, ox):
            placed = set((oy + a, ox + b) for a, b in shape)
            if not tset.issubset(placed):
                return False
            for y, x in placed:
                if not (0 <= y < h and 0 <= x < w) or g[y, x] == MARKER:
                    return False
            return True
        if not fits(ty0, tx0):
            found = None
            for (a, b) in sorted(shape):
                for (y, x) in tcells:
                    oy, ox = y - a, x - b
                    if fits(oy, ox):
                        found = (oy, ox)
                        break
                if found is not None:
                    break
            if found is not None:
                origin = found
    oy, ox = origin
    for comp in comps:
        y0 = min(c[0] for c in comp)
        x0 = min(c[1] for c in comp)
        for y, x in comp:
            sy, sx = oy + (y - y0), ox + (x - x0)
            if 0 <= sy < h and 0 <= sx < w:
                v = int(g[sy, sx])
                if v != MARKER and ((sy, sx) in tset or (shape is not None and (y - y0, x - x0) in shape)):
                    out[y, x] = v
    # erase the template
    if shape is not None and origin != (ty0, tx0) or shape is not None:
        for a, b in shape:
            y, x = oy + a, ox + b
            if 0 <= y < h and 0 <= x < w and g[y, x] != MARKER:
                out[y, x] = BG
    for y, x in tcells:
        out[y, x] = BG
    return out.tolist()
''' % (bg, marker)
    return src
