def build_program(d4, palette):
    ar, ac = 0, 1
    if d4 >= 4:
        ac = -ac
    for _ in range(d4 % 4):
        ar, ac = ac, -ar
    bg = int(palette[0])
    gray = int(palette[5])
    src = '''import numpy as np
from collections import deque

AR = @AR@
AC = @AC@
BG = @BG@
GRAY = @GRAY@


def _along(p):
    return p[0] * AR + p[1] * AC


def _components(g):
    h, w = g.shape
    mask = g != BG
    seen = np.zeros((h, w), dtype=bool)
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
    H, W = g.shape
    pieces = []
    for cells in _components(g):
        cols = [int(g[y, x]) for y, x in cells if g[y, x] != GRAY]
        colour = cols[0] if cols else GRAY
        hooks = sorted([c for c in cells if g[c[0], c[1]] == GRAY], key=_along)
        al = [_along(c) for c in cells]
        pieces.append((min(al), max(al) - min(al) + 1, cells, colour, hooks))
    if not pieces:
        return g.tolist()
    pieces.sort(key=lambda p: p[0])
    total = sum(p[1] for p in pieces)
    if AR == 0:
        out = np.full((H, total), BG, dtype=int)
    else:
        out = np.full((total, W), BG, dtype=int)
    OH, OW = out.shape
    cursor = 0 if AR + AC > 0 else -(total - 1)
    prev = None
    for i, (amin, ext, cells, colour, hooks) in enumerate(pieces):
        if i == 0 or prev is None or not hooks:
            s = cursor - amin
            dy, dx = s * AR, s * AC
        else:
            hy, hx = hooks[0]
            dy = prev[0] + AR - hy
            dx = prev[1] + AC - hx
        for y, x in cells:
            ny, nx = y + dy, x + dx
            if 0 <= ny < OH and 0 <= nx < OW:
                out[ny, nx] = colour
        cursor = amin + ext - 1 + dy * AR + dx * AC + 1
        if hooks:
            prev = (hooks[-1][0] + dy, hooks[-1][1] + dx)
        else:
            prev = None
    return out.tolist()
'''
    src = src.replace('@AR@', str(ar)).replace('@AC@', str(ac))
    src = src.replace('@BG@', str(bg)).replace('@GRAY@', str(gray))
    return src
