def build_program(d4, palette):
    bg = int(palette[8])
    frame = int(palette[1])
    line = int(palette[6])
    src = '''import numpy as np
from collections import deque

BG = %d
FRAME = %d
LINE = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
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
    bg = BG
    mask = (g == FRAME)
    if not mask.any():
        # fallback: treat every non-background cell as frame material
        mask = (g != bg)
    for cells in _components(mask):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        cy = (min(ys) + max(ys)) // 2
        cx = (min(xs) + max(xs)) // 2
        r = out[cy]
        r[g[cy] == bg] = LINE
        c = out[:, cx]
        c[g[:, cx] == bg] = LINE
    return out.tolist()
''' % (bg, frame, line)
    return src
