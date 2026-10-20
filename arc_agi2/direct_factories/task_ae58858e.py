def build_program(d4, palette):
    bg = int(palette[0])
    red = int(palette[2])
    mag = int(palette[6])
    src = '''import numpy as np

BG = %d
RED = %d
MAG = %d
THRESH = 4

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    mask = (g == RED)
    seen = np.zeros((h, w), dtype=bool)
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                stack = [(y, x)]
                seen[y, x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                if len(cells) >= THRESH:
                    for cy, cx in cells:
                        out[cy, cx] = MAG
    return out.tolist()
''' % (bg, red, mag)
    return src
