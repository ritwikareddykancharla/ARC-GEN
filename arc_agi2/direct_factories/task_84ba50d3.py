BODY = '''
import numpy as np
from collections import deque


def _line_index(g, axis):
    H, W = g.shape
    if axis == 0:
        for r in range(H):
            if np.all(g[r, :] == LINE):
                return r
        return int(np.argmax((g == LINE).sum(axis=1)))
    for c in range(W):
        if np.all(g[:, c] == LINE):
            return c
    return int(np.argmax((g == LINE).sum(axis=0)))


def _components(mask):
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                comps.append(cells)
    return comps


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    if DR != 0:
        axis, s = 0, DR
    else:
        axis, s = 1, DC
    N = H if axis == 0 else W
    L = _line_index(g, axis)
    mask = g == OBJ
    out = g.copy()
    out[mask] = BG
    holes = []
    placed = []
    for cells in _components(mask):
        counts = dict()
        for cell in cells:
            a = cell[axis]
            counts[a] = counts.get(a, 0) + 1
        wide = [a for a, n in counts.items() if n > 1]
        along = [cell[axis] for cell in cells]
        if not wide:
            delta = (N - 1 - max(along)) if s > 0 else (0 - min(along))
            for cell in cells:
                holes.append(cell[1 - axis])
        else:
            front = max(wide) if s > 0 else min(wide)
            delta = (L - s) - front
        for cell in cells:
            p = [cell[0], cell[1]]
            p[axis] += delta
            placed.append((p[0], p[1]))
    for x in holes:
        if axis == 0:
            out[L, x] = BG
        else:
            out[x, L] = BG
    for r, c in placed:
        if 0 <= r < H and 0 <= c < W:
            out[r, c] = OBJ
    return out.tolist()
'''


def build_program(d4, palette):
    k = int(d4) % 4
    dr, dc = [(1, 0), (0, -1), (-1, 0), (0, 1)][k]
    header = 'BG = %d\nLINE = %d\nOBJ = %d\nDR = %d\nDC = %d\n' % (int(palette[8]), int(palette[2]), int(palette[1]), dr, dc)
    return header + BODY
