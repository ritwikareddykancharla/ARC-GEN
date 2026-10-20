def build_program(d4, palette):
    pal = [int(palette[c]) for c in range(10)]
    template = '''import numpy as np
from collections import deque

BG = __BG__
SRC_A = __SA__
SRC_B = __SB__
NEW_A = __NA__
NEW_B = __NB__


def _components(g, colour):
    H, W = g.shape
    seen = np.zeros((H, W), dtype=bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y, x] == colour and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == colour:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                comps.append(sorted(cells))
    return comps


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    # Shadows of the first object colour are stamped first; shadows of the
    # second colour are stamped afterwards and win on shared cells.
    for src, new, sign in ((SRC_A, NEW_A, 1), (SRC_B, NEW_B, -1)):
        for cells in _components(g, src):
            if len(cells) != 3:
                continue
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            if y1 - y0 != 1 or x1 - x0 != 1:
                continue
            cs = set(cells)
            missing = [(yy, xx) for yy in (y0, y1) for xx in (x0, x1) if (yy, xx) not in cs]
            if len(missing) != 1:
                continue
            gy, gx = missing[0]
            ey, ex = y0 + y1 - gy, x0 + x1 - gx
            dy, dx = (gy - ey) * sign, (gx - ex) * sign
            for y, x in cells:
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and g[ny, nx] == BG:
                    out[ny, nx] = new
    return out.tolist()
'''
    return (template.replace('__BG__', str(pal[7]))
                    .replace('__SA__', str(pal[5]))
                    .replace('__SB__', str(pal[2]))
                    .replace('__NA__', str(pal[4]))
                    .replace('__NB__', str(pal[3])))
