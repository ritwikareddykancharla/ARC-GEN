def build_program(d4, palette):
    bg = int(palette[0])
    c1 = int(palette[1])
    c2 = int(palette[2])
    template = '''import numpy as np
from collections import deque

BG = __BG__
C1 = __C1__
C2 = __C2__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    seen = np.zeros((H, W), dtype=bool)
    for y0 in range(H):
        for x0 in range(W):
            if g[y0, x0] != BG or seen[y0, x0]:
                continue
            # one room = 4-connected component of background cells
            q = deque([(y0, x0)])
            seen[y0, x0] = True
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == BG:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            room = set(cells)
            # wall ring: every in-grid cell 8-adjacent to the room but not in it
            # (for a rectangular room this is its 1-cell frame, corners included,
            # exactly the (h+2)x(w+2) window the constructor counts)
            ring = set()
            for cy, cx in cells:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in room:
                            ring.add((ny, nx))
            n1 = 0
            n2 = 0
            for p in ring:
                v = g[p]
                if v == C1:
                    n1 += 1
                elif v == C2:
                    n2 += 1
            if n2 > n1:
                col = C2
            else:
                # n1 > n2 is the majority case; n1 == n2 never occurs in the
                # constructor's domain (tied scenes are rejected) - fallback only
                col = C1
            for p in cells:
                out[p] = col
    return out.tolist()
'''
    return template.replace('__BG__', repr(bg)).replace('__C1__', repr(c1)).replace('__C2__', repr(c2))
