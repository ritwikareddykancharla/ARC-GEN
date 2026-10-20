def build_program(d4, palette):
    bg = int(palette[0])
    one = int(palette[1])
    tile_fill = int(palette[8])
    template = '''import numpy as np
from collections import deque

BG = __BG__
ONE = __ONE__
FILL = __FILL__


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    h, w = g.shape
    mask = g != BG
    seen = np.zeros((h, w), dtype=bool)
    best = None
    best_score = -1
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            seen[y, x] = True
            queue = deque([(y, x)])
            cells = []
            while queue:
                cy, cx = queue.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            tile = g[y0:y1 + 1, x0:x1 + 1]
            score = int((tile == ONE).sum())
            if score > best_score:
                best_score = score
                best = tile.copy()
    if best is None:
        return g.tolist()
    return best.tolist()
'''
    return (template.replace('__BG__', str(bg))
                    .replace('__ONE__', str(one))
                    .replace('__FILL__', str(tile_fill)))
