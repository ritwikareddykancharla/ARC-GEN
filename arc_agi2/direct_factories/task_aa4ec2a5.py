TEMPLATE = '''import numpy as np
from collections import deque

BG = __BG__
SHAPE = __SHAPE__
OUTLINE = __OUTLINE__
HOLED = __HOLED__
HOLE = __HOLE__
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _label(mask):
    H, W = mask.shape
    lab = -np.ones((H, W), dtype=int)
    comps = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and lab[y, x] < 0:
                k = len(comps)
                lab[y, x] = k
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in N4:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and lab[ny, nx] < 0:
                            lab[ny, nx] = k
                            q.append((ny, nx))
                comps.append(cells)
    return lab, comps


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bgm = g == BG
    shp = g == SHAPE
    outside = np.zeros((H, W), dtype=bool)
    q = deque()
    for y in range(H):
        for x in range(W):
            if (y == 0 or y == H - 1 or x == 0 or x == W - 1) and bgm[y, x]:
                outside[y, x] = True
                q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in N4:
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < H and 0 <= nx < W and bgm[ny, nx] and not outside[ny, nx]:
                outside[ny, nx] = True
                q.append((ny, nx))
    holes = bgm & ~outside
    out = g.copy()
    ys, xs = np.nonzero(shp)
    for y, x in zip(ys.tolist(), xs.tolist()):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and outside[ny, nx]:
                    out[ny, nx] = OUTLINE
    slab, scomps = _label(shp)
    hlab, hcomps = _label(holes)
    holed = [False] * len(scomps)
    for hc in hcomps:
        owners = set()
        for y, x in hc:
            for dy, dx in N4:
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and slab[ny, nx] >= 0:
                    owners.add(int(slab[ny, nx]))
        if owners:
            for o in owners:
                holed[o] = True
            for y, x in hc:
                out[y, x] = HOLE
    for k, cells in enumerate(scomps):
        if holed[k]:
            for y, x in cells:
                out[y, x] = HOLED
    return out.tolist()
'''


def build_program(d4, palette):
    p = [int(palette[i]) for i in range(10)]
    src = TEMPLATE
    src = src.replace('__BG__', str(p[4]))
    src = src.replace('__SHAPE__', str(p[1]))
    src = src.replace('__OUTLINE__', str(p[2]))
    src = src.replace('__HOLED__', str(p[8]))
    src = src.replace('__HOLE__', str(p[6]))
    return src
