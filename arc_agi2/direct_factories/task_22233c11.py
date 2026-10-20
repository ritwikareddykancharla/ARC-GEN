def build_program(d4, palette):
    G = int(palette[3])
    C = int(palette[8])
    BG = int(palette[0])
    src = '''
import numpy as np
from collections import deque

GREEN = %d
CYAN = %d
BG = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
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
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    squares = []
    for cells in _components(g == GREEN):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, x0, y1, x1 = min(ys), min(xs), max(ys), max(xs)
        hh, ww = y1 - y0 + 1, x1 - x0 + 1
        if hh != ww or len(cells) != hh * ww:
            continue
        squares.append((y0, x0, hh))
    squares.sort()

    def stamp(y, x, s):
        for yy in range(y, y + s):
            for xx in range(x, x + s):
                if 0 <= yy < H and 0 <= xx < W:
                    out[yy, xx] = CYAN

    n = len(squares)
    for i in range(n):
        for j in range(i + 1, n):
            ya, xa, sa = squares[i]
            yb, xb, sb = squares[j]
            if sa != sb:
                continue
            s = sa
            dy, dx = yb - ya, xb - xa
            if abs(dy) != s or abs(dx) != s:
                continue
            # empty corners of the 2x2 block square are (ya, xb) and (yb, xa);
            # push each one block outward along the perpendicular diagonal
            stamp(ya - dy, xb + dx, s)
            stamp(yb + dy, xa - dx, s)
    return out.tolist()
''' % (G, C, BG)
    return src
