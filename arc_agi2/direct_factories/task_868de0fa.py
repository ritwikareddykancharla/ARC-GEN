# Repair (RE-ARC domain review): frames are the four-connected components of
# every non-background input colour, not only native blue (palette[1]). Native
# inputs use blue frames alone, so their result is unchanged; RE-ARC draws each
# frame in its own colour (never 2 or 7), and its verifier fills every square
# background region by the parity of its side.
def build_program(d4, palette):
    bg = int(palette[0])
    odd_fill = int(palette[7])
    even_fill = int(palette[2])
    src = '''import numpy as np
from collections import deque

BG = %d
ODD_FILL = %d
EVEN_FILL = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
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
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    # Each frame is one colour; frames of different colours are separate objects.
    for frame in sorted(set(int(v) for v in np.unique(g)) - {BG}):
        for cells in _components(g == frame):
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            iy0, iy1, ix0, ix1 = y0 + 1, y1 - 1, x0 + 1, x1 - 1
            if iy1 < iy0 or ix1 < ix0:
                continue
            ih = iy1 - iy0 + 1
            iw = ix1 - ix0 + 1
            side = ih if ih == iw else min(ih, iw)
            col = ODD_FILL if side %% 2 == 1 else EVEN_FILL
            sub = out[iy0:iy1 + 1, ix0:ix1 + 1]
            sub[g[iy0:iy1 + 1, ix0:ix1 + 1] == BG] = col
    return out.tolist()
''' % (bg, odd_fill, even_fill)
    return src
