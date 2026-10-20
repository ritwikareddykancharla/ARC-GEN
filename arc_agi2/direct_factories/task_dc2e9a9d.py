def build_program(d4, palette):
    d4 = int(d4) % 8
    bg = int(palette[0])
    fg = int(palette[3])
    if d4 % 2 == 0:
        vcol = int(palette[8])
        hcol = int(palette[1])
    else:
        vcol = int(palette[1])
        hcol = int(palette[8])
    src = '''import numpy as np
from collections import deque

BG = %d
FG = %d
VCOL = %d
HCOL = %d

def _components(mask):
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
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
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    for cells in _components(g == FG):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        h, w = y1 - y0 + 1, x1 - x0 + 1
        m = np.zeros((h, w), dtype=bool)
        for y, x in cells:
            m[y - y0, x - x0] = True
        sides = [('top', int(m[0].sum())), ('bottom', int(m[-1].sum())),
                 ('left', int(m[:, 0].sum())), ('right', int(m[:, -1].sum()))]
        nubs = [k for k, v in sides if v == 1]
        if len(nubs) != 1:
            continue
        nub = nubs[0]
        if nub == 'top':
            pat, dy, dx, col = m[::-1, :], h + 1, 0, VCOL
        elif nub == 'bottom':
            pat, dy, dx, col = m[::-1, :], -(h + 1), 0, VCOL
        elif nub == 'left':
            pat, dy, dx, col = m[:, ::-1], 0, w + 1, HCOL
        else:
            pat, dy, dx, col = m[:, ::-1], 0, -(w + 1), HCOL
        for yy in range(h):
            for xx in range(w):
                if pat[yy, xx]:
                    ty, tx = y0 + dy + yy, x0 + dx + xx
                    if 0 <= ty < H and 0 <= tx < W:
                        out[ty, tx] = col
    return out.tolist()
''' % (bg, fg, vcol, hcol)
    return src
