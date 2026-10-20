def build_program(d4, palette):
    bg = int(palette[7])
    hit = int(palette[9])
    dup = int(palette[1])
    template = '''import numpy as np
from collections import deque

BG = __BG__
HIT = __HIT__
DUP = __DUP__
STEP = 5


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
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                out.append(sorted(cells))
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    comps = _components(g != BG)
    owner = {}
    for i, c in enumerate(comps):
        for p in c:
            owner[p] = i
    hits = {}
    for c in comps:
        best = None
        for a in c:
            s = 0
            for b in c:
                s += (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
            if best is None or s < best[0]:
                best = (s, a)
        tip = best[1]
        sy = sum(b[0] - tip[0] for b in c)
        sx = sum(b[1] - tip[1] for b in c)
        dy = -int(np.sign(sy))
        dx = -int(np.sign(sx))
        if dy == 0 and dx == 0:
            continue
        ty, tx = tip[0] + STEP * dy, tip[1] + STEP * dx
        if 0 <= ty < H and 0 <= tx < W:
            hits[(ty, tx)] = hits.get((ty, tx), 0) + 1
    for (ty, tx), n in sorted(hits.items()):
        if (ty, tx) in owner:
            for p in comps[owner[(ty, tx)]]:
                out[p] = HIT
        else:
            out[ty, tx] = DUP if n > 1 else HIT
    return out.tolist()
'''
    return template.replace('__BG__', str(bg)).replace('__HIT__', str(hit)).replace('__DUP__', str(dup))
