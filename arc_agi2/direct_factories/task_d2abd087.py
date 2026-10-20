def build_program(d4, palette):
    bg = int(palette[0])
    grey = int(palette[5])
    red = int(palette[2])
    blue = int(palette[1])
    # Under every D4 transform, 4-connectivity and component cell counts are unchanged,
    # so d4 doesn't alter the mechanism. Only the colour roles are specialised.
    src = '''import numpy as np
from collections import deque

BG = %d
GREY = %d
RED = %d
BLUE = %d
TARGET_SIZE = 6

def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
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
    comps = _components(g == GREY)
    # Stage 1: exact-size-6 shapes become red.
    for cells in comps:
        if len(cells) == TARGET_SIZE:
            for y, x in cells:
                out[y, x] = RED
    # Stage 2: every other grey shape becomes blue.
    for cells in comps:
        if len(cells) != TARGET_SIZE:
            for y, x in cells:
                out[y, x] = BLUE
    return out.tolist()
''' % (bg, grey, red, blue)
    return src
