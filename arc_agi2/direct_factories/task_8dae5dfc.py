def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np
from collections import deque

BG = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
    comps = []
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
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    for cells in _components(g != BG):
        boxes = {}
        for y, x in cells:
            c = int(g[y, x])
            if c in boxes:
                y0, x0, y1, x1 = boxes[c]
                boxes[c] = (min(y0, y), min(x0, x), max(y1, y), max(x1, x))
            else:
                boxes[c] = (y, x, y, x)
        def area(c):
            y0, x0, y1, x1 = boxes[c]
            return (y1 - y0 + 1) * (x1 - x0 + 1)
        order = sorted(boxes.keys(), key=lambda c: (-area(c), c))
        rev = order[::-1]
        mapping = {order[i]: rev[i] for i in range(len(order))}
        for y, x in cells:
            out[y, x] = mapping[int(g[y, x])]
    return out.tolist()
''' % bg
    return src
