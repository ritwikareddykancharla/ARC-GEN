def build_program(d4, palette):
    skel_a = int(palette[4])
    skel_b = int(palette[7])
    reflected = int(d4) >= 4
    # Clockwise border cycle: each region takes the colour of the previous region.
    # A reflection turns the clockwise walk into a counterclockwise one. So when we
    # walk clockwise in visible coordinates, each region takes the colour of the
    # NEXT region in the walk.
    shift = 1 if reflected else -1
    src = '''import numpy as np
from collections import deque

SKELETON = (__A__, __B__)
SHIFT = __S__

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
                out.append(sorted(cells))
    return out

def _border_walk(h, w):
    path = [(0, x) for x in range(w)]
    path += [(y, w - 1) for y in range(1, h)]
    if h > 1:
        path += [(h - 1, x) for x in range(w - 2, -1, -1)]
    if w > 1:
        path += [(y, 0) for y in range(h - 2, 0, -1)]
    return path

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    mask = ~np.isin(g, list(SKELETON))
    comps = _components(mask)
    cid = {}
    for i, comp in enumerate(comps):
        for p in comp:
            cid[p] = i
    order = []
    for p in _border_walk(h, w):
        if p in cid and cid[p] not in order:
            order.append(cid[p])
    out = g.copy()
    n = len(order)
    if n < 2:
        return out.tolist()
    colours = [int(g[comps[i][0]]) for i in order]
    for k, i in enumerate(order):
        newc = colours[(k + SHIFT) % n]
        for (y, x) in comps[i]:
            out[y, x] = newc
    return out.tolist()
'''
    src = src.replace('__A__', str(skel_a)).replace('__B__', str(skel_b)).replace('__S__', str(shift))
    return src
