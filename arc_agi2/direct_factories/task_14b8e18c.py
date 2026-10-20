def build_program(d4, palette):
    bg = int(palette[7])
    mark = int(palette[2])
    src = '''import numpy as np
from collections import deque

BG = %d
MARK = %d

def _components(g, colour):
    H, W = g.shape
    seen = np.zeros((H, W), bool)
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
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    colours = sorted(set(int(v) for v in g.ravel().tolist()) - {BG})
    for colour in colours:
        for cells in _components(g, colour):
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            h, w = y1 - y0 + 1, x1 - x0 + 1
            if h != w or h < 2:
                continue
            for cy, cx, dy, dx in ((y0, x0, -1, -1), (y0, x1, -1, 1), (y1, x0, 1, -1), (y1, x1, 1, 1)):
                for ny, nx in ((cy + dy, cx), (cy, cx + dx)):
                    if 0 <= ny < H and 0 <= nx < W and out[ny, nx] == BG:
                        out[ny, nx] = MARK
    return out.tolist()
''' % (bg, mark)
    return src
