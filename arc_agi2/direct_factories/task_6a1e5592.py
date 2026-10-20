TEMPLATE = '''import numpy as np
from collections import deque

SIDE = __SIDE__
RED = __RED__
BLACK = __BLACK__
GRAY = __GRAY__
BLUE = __BLUE__


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
                out.append(sorted(cells))
    return out


def _band(g):
    H, W = g.shape
    red = g == RED
    band = np.zeros((H, W), bool)
    if SIDE == 0 or SIDE == 2:
        idx = np.nonzero(red.any(axis=1))[0]
        if len(idx) == 0:
            return band
        if SIDE == 0:
            band[:int(idx.max()) + 1, :] = True
        else:
            band[int(idx.min()):, :] = True
    else:
        idx = np.nonzero(red.any(axis=0))[0]
        if len(idx) == 0:
            return band
        if SIDE == 3:
            band[:, :int(idx.max()) + 1] = True
        else:
            band[:, int(idx.min()):] = True
    return band


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    band = _band(g)
    holes = _components(band & (g == BLACK))
    if not holes:
        return out.tolist()
    hid = -np.ones((H, W), int)
    for i, hole in enumerate(holes):
        for y, x in hole:
            hid[y, x] = i
    pieces = _components(g == GRAY)
    cands = []
    for pi, pc in enumerate(pieces):
        ys = [p[0] for p in pc]
        xs = [p[1] for p in pc]
        for dy in range(-min(ys), H - max(ys)):
            for dx in range(-min(xs), W - max(xs)):
                moved = [(y + dy, x + dx) for y, x in pc]
                ok = True
                inband = []
                for y, x in moved:
                    if g[y, x] == RED:
                        ok = False
                        break
                    if band[y, x]:
                        if hid[y, x] < 0:
                            ok = False
                            break
                        inband.append((y, x))
                if not ok or not inband:
                    continue
                hs = frozenset(int(hid[y, x]) for y, x in inband)
                if sum(len(holes[i]) for i in hs) != len(inband):
                    continue
                cands.append((pi, frozenset(moved), hs))
    nh = len(holes)
    npieces = len(pieces)

    def search(covered, used, occ, chosen, need_all):
        if len(covered) == nh:
            if need_all and len(used) != npieces:
                return None
            return list(chosen)
        best = None
        for hi in range(nh):
            if hi in covered:
                continue
            opts = [c for c in cands if hi in c[2] and c[0] not in used
                    and not (c[2] & covered) and not (c[1] & occ)]
            if best is None or len(opts) < len(best[1]):
                best = (hi, opts)
                if not opts:
                    break
        for c in best[1]:
            chosen.append(c)
            r = search(covered | c[2], used | frozenset([c[0]]), occ | c[1], chosen, need_all)
            if r is not None:
                return r
            chosen.pop()
        return None

    res = search(frozenset(), frozenset(), frozenset(), [], True)
    if res is None:
        res = search(frozenset(), frozenset(), frozenset(), [], False)
    if res is None:
        return out.tolist()
    for pi, moved, hs in res:
        for y, x in pieces[pi]:
            out[y, x] = BLACK
    for pi, moved, hs in res:
        for y, x in moved:
            out[y, x] = BLUE
    return out.tolist()
'''


def build_program(d4, palette):
    k = int(d4) % 4
    pal = [int(v) for v in palette]
    src = TEMPLATE
    src = src.replace('__SIDE__', str(k))
    src = src.replace('__RED__', str(pal[2]))
    src = src.replace('__BLACK__', str(pal[0]))
    src = src.replace('__GRAY__', str(pal[5]))
    src = src.replace('__BLUE__', str(pal[1]))
    return src
