TEMPLATE = """import numpy as np
from collections import deque

SIDE = '__SIDE__'
BG = __BG__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    mask = g != BG
    if SIDE == 'bottom':
        mask[max(H - 2, 0):, :] = False
        line = g[H - 2, :]
    elif SIDE == 'top':
        mask[:2, :] = False
        line = g[1, :]
    elif SIDE == 'left':
        mask[:, :2] = False
        line = g[:, 1]
    else:
        mask[:, max(W - 2, 0):] = False
        line = g[:, W - 2]
    gaps = []
    n = len(line)
    i = 0
    while i < n:
        if line[i] == BG:
            s = i
            while i < n and line[i] == BG:
                i += 1
            gaps.append((s, i - s))
        else:
            i += 1
    seen = np.zeros((H, W), dtype=bool)
    objs = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                c = int(g[y, x])
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx] and g[ny, nx] == c:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                objs.append((c, cells))
    for c, cells in objs:
        for cy, cx in cells:
            out[cy, cx] = BG
    used = set()
    for c, cells in objs:
        ys = [p[0] for p in cells]
        xs = [p[1] for p in cells]
        hy = max(ys) - min(ys) + 1
        wx = max(xs) - min(xs) + 1
        if SIDE in ('bottom', 'top'):
            perp, along = hy, wx
        else:
            perp, along = wx, hy
        length = along if perp == 2 else perp
        for idx, (s, gl) in enumerate(gaps):
            if gl == length and idx not in used:
                used.add(idx)
                if SIDE == 'bottom':
                    out[H - 3:H - 1, s:s + gl] = c
                elif SIDE == 'top':
                    out[1:3, s:s + gl] = c
                elif SIDE == 'left':
                    out[s:s + gl, 1:3] = c
                else:
                    out[s:s + gl, W - 3:W - 1] = c
                break
    return out.tolist()
"""


def build_program(d4, palette):
    k = int(d4) % 4
    side = ['bottom', 'left', 'top', 'right'][k]
    bg = int(palette[0])
    return TEMPLATE.replace('__SIDE__', side).replace('__BG__', str(bg))
